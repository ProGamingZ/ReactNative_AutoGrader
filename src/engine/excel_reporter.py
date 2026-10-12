import pandas as pd
import os
from datetime import datetime
from src.models.grade_result import GradeResult

class ExcelReporter:
    def __init__(self, original_df, original_filepath):
        self.df = original_df.copy()
        self.original_filepath = original_filepath

    def record_grade(self, index, result: GradeResult):
        """Updates the dataframe for a specific student's row using GradeResult."""
        result_dict = result.to_dict()
        for col_name, value in result_dict.items():
            self.df.at[index, col_name] = value

    def save(self, output_dir):
        """Saves the dataframe to a new timestamped Excel file in the chosen directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(self.original_filepath).replace(".xlsx", "")
        
        new_filename = f"{base_name}_GRADED_{timestamp}.xlsx"
        save_path = os.path.join(output_dir, new_filename)
        
        try:
            self.df.to_excel(save_path, index=False)
            return save_path
        except Exception as e:
            print(f"[ERROR] Failed to save Excel: {e}")
            return None