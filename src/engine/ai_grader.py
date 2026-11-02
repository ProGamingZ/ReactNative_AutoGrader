import json
import os
import re
import time
import logging
import ollama
from groq import Groq, RateLimitError, BadRequestError, APIStatusError

logger = logging.getLogger("AutoGrader")

class AIGrader:
    def __init__(self, model_name="qwen2.5-coder:7b", provider="Local (Ollama)", api_key=""):
        self.model_name = model_name
        self.provider = provider
        self.api_key = api_key.strip() or os.environ.get("GROQ_API_KEY", "")

    def clean_json(self, text):
        # Remove <think>...</think> blocks if emitted by reasoning models (e.g., gpt-oss / qwen3.8)
        text = re.sub(r'<think>[\s\S]*?</think>', '', text).strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()
        # Locate first '{' in case model added a preamble
        if "{" in text and not text.startswith("{"):
            text = text[text.find("{"):]
        # Auto-heal if LLM hit token limit inside the "feedback" string
        if text.startswith("{") and not text.endswith("}"):
            text = text.rstrip('"') + '"}'
        return text

    @staticmethod
    def extract_rubric_categories(rubric_text: str) -> list:
        """Extracts exact bolded rubric category titles from the Markdown file."""
        categories = re.findall(r'^\s*\*\s+\*\*(.+?)\*\*', rubric_text, re.MULTILINE)
        return [cat.rstrip(':').strip() for cat in categories]

    @staticmethod
    def enforce_word_limit(text: str, max_words: int = 20) -> str:
        """Hard-limits feedback string to max_words."""
        words = str(text).strip().split()
        if len(words) > max_words:
            return " ".join(words[:max_words])
        return " ".join(words)

    def _interruptible_sleep(self, seconds: float, stop_event) -> bool:
        """Sleeps in 0.25s increments so the Stop button remains responsive during rate-limit waits."""
        steps = int(seconds / 0.25)
        for _ in range(max(1, steps)):
            if stop_event and stop_event.is_set():
                return False
            time.sleep(0.25)
        return True

    def _call_ollama(self, system_prompt: str, code_text: str, stop_event) -> str | None:
        """Streams inference from local Ollama instance."""
        logger.debug(f"Sending prompt to Local Ollama model: {self.model_name}...")
        stream = ollama.chat(
            model=self.model_name,
            format="json",
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Student Source Code:\n\n{code_text}"}
            ],
            options={
                "temperature": 0.1,
                "num_predict": 250,
                "num_ctx": 3072,
                "num_thread": 6
            },
            stream=True
        )

        raw_content = ""
        for chunk in stream:
            if stop_event and stop_event.is_set():
                getattr(stream, "close", lambda: None)()
                logger.warning("Local AI generation aborted by user Stop signal.")
                return None
            raw_content += chunk['message']['content']
        return raw_content

    def _call_groq(self, system_prompt: str, code_text: str, stop_event) -> str | None:
        """Calls Groq Cloud API with reasoning_effort control, 400 JSON fallback, and 429 backoff."""
        client = Groq(api_key=self.api_key)
        max_retries = 4
        use_json_mode = True

        # Configure model-specific reasoning effort so Chain-of-Thought never starves JSON output
        extra_kwargs = {}
        model_lower = self.model_name.lower()
        if "gpt-oss" in model_lower:
            extra_kwargs["reasoning_effort"] = "low"
        elif "qwen" in model_lower:
            extra_kwargs["reasoning_effort"] = "none"

        for attempt in range(1, max_retries + 1):
            if stop_event and stop_event.is_set():
                return None
            try:
                logger.debug(f"Sending prompt to Groq Cloud model: {self.model_name} (Attempt {attempt})...")
                req_kwargs = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Student Source Code:\n\n{code_text}"}
                    ],
                    "temperature": 0.1,
                    "max_completion_tokens": 2048,
                    "stream": True,
                    **extra_kwargs
                }
                if use_json_mode:
                    req_kwargs["response_format"] = {"type": "json_object"}

                stream = client.chat.completions.create(**req_kwargs)

                raw_content = ""
                for chunk in stream:
                    if stop_event and stop_event.is_set():
                        getattr(stream, "close", lambda: None)()
                        logger.warning("Groq Cloud generation aborted by user Stop signal.")
                        return None
                    delta = chunk.choices[0].delta.content
                    if delta:
                        raw_content += delta

                self._interruptible_sleep(2.2, stop_event)
                return raw_content

            except BadRequestError as e:
                # Handle Groq HTTP 400 'json_validate_failed' on gpt-oss models
                err_body = getattr(e, "body", {}) or {}
                failed_gen = err_body.get("error", {}).get("failed_generation", "")
                if failed_gen and "{" in failed_gen:
                    logger.warning(f"Recovered partial JSON from Groq failed_generation on Attempt {attempt}.")
                    return failed_gen
                logger.warning(f"Groq JSON mode validation failed on Attempt {attempt}. Retrying in text-extraction mode...")
                use_json_mode = False
                if not self._interruptible_sleep(1.5, stop_event):
                    return None

            except RateLimitError:
                wait_time = 12.0 * attempt
                logger.warning(f"Groq Rate Limit (429) reached. Pausing {wait_time:.0f}s before retry ({attempt}/{max_retries})...")
                if not self._interruptible_sleep(wait_time, stop_event):
                    return None

            except APIStatusError as e:
                if e.status_code in (401, 403, 404):
                    logger.error(f"FATAL Groq Error ({e.status_code}): {e.message}. Stopping batch.")
                    if stop_event:
                        stop_event.set()
                    return None
                if e.status_code >= 500 and attempt < max_retries:
                    logger.warning(f"Groq Server Error ({e.status_code}). Retrying in 5s...")
                    if not self._interruptible_sleep(5.0, stop_event):
                        return None
                else:
                    raise e

        raise RuntimeError("Exceeded maximum Groq API retries.")

    def evaluate(self, code_text, objective_flags, rubric_text, rubric_categories, stop_event=None):
        score_template = {cat: 0 for cat in rubric_categories}

        system_prompt = f"""You are a strict, critical React Native code grader.
Grade the student code strictly using this rubric:
{rubric_text}

Verified Syntax Flags (True = present in student code, False = missing):
{json.dumps(objective_flags)}

STRICT SCORING TIERS (Do NOT give 100% unless code is flawless):
- INCOMPLETE (0% to 40% of category max): Required syntax flag for that category is False, or feature is missing/broken.
- AVERAGE (60% to 84% of category max): Required flags are True, but code has flaws (e.g., inline style objects instead of StyleSheet, hardcoded pixel heights/widths instead of Flexbox, messy nesting, or single giant unmodular component).
- EXCELLENT (85% to 100% of category max): All required flags are True, clean modular components, responsive Flexbox, and zero anti-patterns.

Instructions:
1. Deduct points critically for genuine code flaws, inline styling, fixed pixel dimensions, or poor organization.
2. IMPORTANT: Markers like "[Middle of file omitted for memory]" indicate parser memory limits. Never deduct points for omitted lines, and trust Verified Syntax Flags (e.g., if "has_stylesheet": true, StyleSheet is present).
3. Only mention tools/components that actually appear in the Student Source Code.
4. You MUST output BOTH the "scores" object AND a non-empty "feedback" string (HARD MAXIMUM of 20 words). Never omit the "feedback" key.
5. Output ONLY valid JSON matching the exact keys below:

{json.dumps({"scores": score_template, "feedback": "Specific reason for deductions or praise in under 20 words."}, indent=4)}"""

        try:
            if self.provider == "Online (Groq)":
                raw_content = self._call_groq(system_prompt, code_text, stop_event)
            else:
                raw_content = self._call_ollama(system_prompt, code_text, stop_event)

            if raw_content is None:
                return None

            cleaned = self.clean_json(raw_content)
            logger.debug(f"Raw AI Output: {cleaned}")
            parsed = json.loads(cleaned)
            raw_scores = parsed.get("scores", {})

            # Map AI scores strictly onto pre-existing rubric columns
            fixed_scores = {}
            for cat in rubric_categories:
                if cat in raw_scores and isinstance(raw_scores[cat], (int, float)):
                    fixed_scores[cat] = int(raw_scores[cat])
                else:
                    base_cat = cat.split("(Max:")[0].strip().lower()
                    matched_val = 0
                    for k, v in raw_scores.items():
                        if base_cat in str(k).lower() and isinstance(v, (int, float)):
                            matched_val = int(v)
                            break
                    fixed_scores[cat] = matched_val

            raw_feedback = parsed.get("feedback", "Evaluated.")
            return {
                "scores": fixed_scores,
                "feedback": self.enforce_word_limit(raw_feedback, 20)
            }

        except Exception as e:
            logger.error(f"AI API Connection Failed ({self.provider}): {e}")
            return {
                "scores": {cat: 0 for cat in rubric_categories},
                "feedback": "AI grading error. Manual review required."
            }

    def unload_model(self):
        """Immediately unloads the model from RAM and GPU VRAM if Local (Ollama) was used."""
        if self.provider != "Local (Ollama)":
            return
        try:
            logger.info(f"Unloading local model '{self.model_name}' from RAM/VRAM...")
            ollama.generate(model=self.model_name, prompt="", keep_alive=0)
            logger.info(f"Model '{self.model_name}' successfully unloaded from memory.")
        except Exception as e:
            logger.debug(f"Could not unload model: {e}")

    @staticmethod
    def fetch_active_groq_models(api_key: str) -> list:
        """Queries Groq API for currently active text/chat models."""
        try:
            client = Groq(api_key=api_key)
            models = client.models.list()
            excluded = ("whisper", "orpheus", "guard", "tts", "embedding")
            active = [
                m.id for m in models.data
                if not any(ex in m.id.lower() for ex in excluded)
            ]
            return sorted(active) if active else ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
        except Exception:
            return ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]