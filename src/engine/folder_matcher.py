import os
from thefuzz import fuzz, process
import logging
logger = logging.getLogger("AutoGrader")

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
        if not self.available_folders:
            return None
        
        clean_name = str(excel_name).replace(',', '').replace('.', '')
        logger.debug(f"Attempting to match cleaned name: '{clean_name}'")
        
        match_result = process.extractOne(clean_name, self.available_folders, scorer=fuzz.token_set_ratio)
        
        if match_result:
            best_match = str(match_result[0])
            score = int(match_result[1])
            
            if score >= 80:
                self.available_folders.remove(best_match)
                logger.debug(f"Match SUCCESS: '{best_match}' (Confidence: {score}) - Locked folder.")
                return best_match
            else:
                logger.debug(f"Match FAILED: Best was '{best_match}' but score {score} is below threshold 80.")
        return None