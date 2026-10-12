import json
import ollama

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
        system_prompt = f"""You are a strict React Native computer science instructor.
Evaluate the following student code based ONLY on the maximum points listed in this rubric:
{rubric_text}

Deterministic Parser Flags (Trust these values): 
{json.dumps(objective_flags)}

Instructions:
1. For each category in the rubric, assign an integer score between 0 and the category's maximum point limit based on code quality.
2. Output ONLY the strict JSON format below. Do NOT add conversational text.

JSON Format:
{{
    "scores": {{
        "exact_category_title_1": 0,
        "exact_category_title_2": 0
    }},
    "feedback": "A concise 1-2 sentence explanation of point deductions."
}}"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Student Source Code:\n\n{code_text}"}
                ],
                options={
                    "temperature": 0.1,        # Prevents deterministic infinite repetition loops
                    "num_predict": 300,        # HARD CAP: Limits response length to ~300 tokens (JSON is small)
                    "num_thread": 4            # Forces Ollama to use 4 CPU threads on your i7
                }
            )
            
            cleaned = self.clean_json(response['message']['content'])
            return json.loads(cleaned)
            
        except Exception as e:
            print(f"[AI ERROR] {e}")
            return {
                "scores": {},
                "feedback": "Error processing AI grading. Requires manual review."
            }