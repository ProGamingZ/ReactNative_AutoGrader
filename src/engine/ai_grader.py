import json
import ollama

class AIGrader:
    def __init__(self, model_name="phi3"):
        self.model_name = model_name

    def clean_json(self, text):
        """Strips markdown formatting if the AI wraps the JSON response."""
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()

    def evaluate(self, code_text, objective_flags, activity_type):
        """Sends the code to the local LLM and returns a parsed JSON dictionary."""
        
        # Define the rubric context based on the selected activity
        rubric_context = ""
        if "Activity 2" in activity_type:
            rubric_context = "Grade out of 100: Component Usage (25), Flexbox Layout (30), UI Aesthetics (25), Code Organization (20)."
        elif "Activity 3" in activity_type:
            rubric_context = "Grade out of 100: State Management (25), List Rendering (25), Interactivity (25), UI/Code (25)."
        elif "Activity 4" in activity_type:
            rubric_context = "Grade out of 100: Navigation Architecture (25), Screen Flow (25), Data Transfer (25), Reverse Nav/Code (25)."

        # Construct the strict system prompt
        system_prompt = f"""You are a strict React Native instructor.
Evaluate the following student code based on this rubric: {rubric_context}
Here is the objective syntax scan from the deterministic parser (Trust these boolean values): 
{json.dumps(objective_flags)}

You MUST output your evaluation ONLY in the following strict JSON format. Do not add any conversational text.
{{
    "scores": {{
        "criterion_1": 0,
        "criterion_2": 0,
        "criterion_3": 0,
        "criterion_4": 0
    }},
    "final_score": 0,
    "feedback": "A concise, 1-2 sentence explanation of deductions."
}}"""

        try:
            # Call the local offline LLM
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f"Evaluate this code:\n\n{code_text}"}
                ],
                options={"temperature": 0.0} # Zero temperature for strict deterministic output
            )
            
            raw_response = response['message']['content']
            cleaned_json = self.clean_json(raw_response)
            return json.loads(cleaned_json)
            
        except Exception as e:
            print(f"[AI ERROR] Failed to parse AI response: {e}")
            # Fallback dictionary so the application doesn't crash
            return {
                "scores": {"criterion_1": 0, "criterion_2": 0, "criterion_3": 0, "criterion_4": 0},
                "final_score": 0,
                "feedback": "Error processing AI grading. Requires manual review."
            }