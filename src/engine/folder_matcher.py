import os
from thefuzz import fuzz, process

class StudentFolderMatcher:
    def __init__(self, submissions_path):
        self.submissions_path = submissions_path
        # Get a list of all folders (ignoring standalone files like .DS_Store)
        try:
            self.available_folders = [
                f for f in os.listdir(submissions_path) 
                if os.path.isdir(os.path.join(submissions_path, f))
            ]
        except Exception:
            self.available_folders = []

    def find_match(self, excel_name):
        """
        Takes a student name from the Excel sheet and finds the closest matching folder.
        Returns the exact folder name if a match is found, otherwise None.
        """
        if not self.available_folders:
            return None
        
        # Clean the Excel name (remove commas and periods for better matching)
        clean_name = str(excel_name).replace(',', '').replace('.', '')
        
        # Assign to a single variable first to satisfy the type checker
        match_result = process.extractOne(clean_name, self.available_folders, scorer=fuzz.token_set_ratio)
        
        if match_result:
            best_match = str(match_result[0])
            score = int(match_result[1])
            
            # 80 is a safe threshold for typos or missing middle names
            if score >= 80:
                return best_match
        
        return None