import json
import re
import ollama
import logging
logger = logging.getLogger("AutoGrader")
class AIGrader:
    def __init__(self, model_name="phi3"):
        self.model_name = model_name

    def clean_json(self, text):
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
    
    @staticmethod
    def extract_rubric_categories(rubric_text: str) -> list:
        """Extracts exact bolded rubric category titles from the Markdown file."""
        # Matches bullet lines like: * **Component Usage & JSX Structure (Max: 25 pts):**
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
        # Build exact JSON score template from pre-parsed rubric columns
        score_template = {cat: 0 for cat in rubric_categories}

        system_prompt = f"""You are a strict but progressive React Native computer science instructor.
Evaluate the following student code based ONLY on the maximum points listed in this rubric:
{rubric_text}

Deterministic Parser Flags (Trust these values. True means they used the required tool OR a valid modern alternative): 
{json.dumps(objective_flags)}

INCLUSIVE GRADING POLICY:
If a student uses a valid, modern industry alternative (e.g., using Shopify's FlashList instead of FlatList, Zustand instead of useState, Expo Router instead of React Navigation, or NativeWind/Tailwind instead of StyleSheet), you MUST award them full points for that category as if they used the standard tool. Do not penalize them for reading ahead or using modern standards.

Instructions:
1. For each category in the rubric, assign an integer score between 0 and the category's maximum point limit based on code quality.
2. You MUST use the exact category keys shown in the JSON Format below. Do NOT rename or add keys.
3. Keep "feedback" to a HARD MAXIMUM of 20 words or less. Be blunt, direct, and telegraphic (ignore grammar).
4. Output ONLY the strict JSON format below.

JSON Format:
{{
    "scores": {json.dumps(score_template, indent=8)},
    "feedback": "Max 20 words. Direct, telegraphic reason for deductions or praise."
}}"""

        try:
            logger.debug(f"Sending prompt to Ollama model: {self.model_name}...")
            stream = ollama.chat(
                model=self.model_name,
                format="json",
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Student Source Code:\n\n{code_text}"}
                ],
                options={"temperature": 0.1, "num_predict": 750, "num_thread": 4},
                stream=True
            )
            
            raw_content = ""
            for chunk in stream:
                if stop_event and stop_event.is_set():
                    stream.close()  # Immediately terminate Ollama generation
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
                    # Fallback match if LLM stripped "(Max: XX pts)" from the key name
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