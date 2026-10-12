import json
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

    def evaluate(self, code_text, objective_flags, rubric_text):
        system_prompt = f"""You are a strict but progressive React Native computer science instructor.
Evaluate the following student code based ONLY on the maximum points listed in this rubric:
{rubric_text}

Deterministic Parser Flags (Trust these values. True means they used the required tool OR a valid modern alternative): 
{json.dumps(objective_flags)}

INCLUSIVE GRADING POLICY:
If a student uses a valid, modern industry alternative (e.g., using Shopify's FlashList instead of FlatList, Zustand instead of useState, Expo Router instead of React Navigation, or NativeWind/Tailwind instead of StyleSheet), you MUST award them full points for that category as if they used the standard tool. Do not penalize them for reading ahead or using modern standards.

Instructions:
1. For each category in the rubric, assign an integer score between 0 and the category's maximum point limit based on code quality.
2. Output ONLY the strict JSON format below. Do NOT add conversational text.

JSON Format:
{{
    "scores": {{
        "exact_category_title_1": 0,
        "exact_category_title_2": 0
    }},
    "feedback": "A concise 1-2 sentence explanation of point deductions. Praise good use of modern alternatives if present."
}}"""

        try:
            logger.debug(f"Sending prompt to Ollama model: {self.model_name}...")
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Student Source Code:\n\n{code_text}"}
                ],
                options={"temperature": 0.1, "num_predict": 300, "num_thread": 4} 
            )
            
            cleaned = self.clean_json(response['message']['content'])
            logger.debug(f"Raw AI Output: {cleaned}")
            return json.loads(cleaned)
            
        except Exception as e:
            logger.error(f"AI API Connection Failed: {e}")
            return {
                "scores": {},
                "feedback": "Error processing AI grading. Requires manual review."
            }