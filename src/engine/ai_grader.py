import json
import re
import ollama
import logging

logger = logging.getLogger("AutoGrader")

class AIGrader:
    def __init__(self, model_name="qwen2.5-coder:3b"):
        self.model_name = model_name

    def clean_json(self, text):
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        text = text.strip()
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

    def evaluate(self, code_text, objective_flags, rubric_text, rubric_categories, stop_event=None):
        score_template = {cat: 0 for cat in rubric_categories}

        system_prompt = f"""You are a strict, critical React Native code grader.
Grade the student code strictly using this rubric:
{rubric_text}

Verified Syntax Flags (True = present in student code, False = missing):
{json.dumps(objective_flags)}

STRICT SCORING TIERS (Do NOT give 100% unless code is flawless):
- INCOMPLETE (0% to 40% of category max): Required syntax flag for that category is False, or feature is missing/broken.
- AVERAGE (60% to 84% of category max): Required flags are True, but code has flaws (e.g., inline style objects instead of StyleSheet, hardcoded pixel heights/widths instead of Flexbox, messy nesting, single giant unmodular component).
- EXCELLENT (85% to 100% of category max): All required flags are True, clean modular components, responsive Flexbox, and zero anti-patterns.

Instructions:
1. Deduct points critically for any code flaws, inline styling, fixed pixel dimensions, or poor organization.
2. Only mention tools/components that actually appear in the Student Source Code.
3. Keep "feedback" to a HARD MAXIMUM of 20 words. State specific code flaws or strengths directly.
4. Output ONLY valid JSON matching the exact keys below:

{json.dumps({"scores": score_template, "feedback": "Specific reason for deductions or praise in under 20 words."}, indent=4)}"""

        try:
            logger.debug(f"Sending prompt to Ollama model: {self.model_name}...")
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
                    logger.warning("AI generation aborted by user Stop signal.")
                    return None
                raw_content += chunk['message']['content']
            
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
            logger.error(f"AI API Connection Failed: {e}")
            return {
                "scores": {cat: 0 for cat in rubric_categories},
                "feedback": "AI grading error. Manual review required."
            }

    def unload_model(self):
        """Immediately unloads the model from RAM and GPU VRAM without stopping the Ollama service."""
        try:
            logger.info(f"Unloading model '{self.model_name}' from RAM/VRAM...")
            ollama.generate(model=self.model_name, prompt="", keep_alive=0)
            logger.info(f"Model '{self.model_name}' successfully unloaded from memory.")
        except Exception as e:
            logger.debug(f"Could not unload model: {e}")