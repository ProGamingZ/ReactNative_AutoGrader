import pandas as pd
import os
from datetime import datetime

class ExcelReporter:
    def __init__(self, original_df, original_filepath):
        # Create a deep copy so we don't accidentally modify the loaded DataFrame
        self.df = original_df.copy()
        self.original_filepath = original_filepath
        
        # Initialize new columns
        self.df['Matched Folder'] = "Not Checked"
        self.df['Final Score'] = 0
        self.df['AI Feedback'] = ""

    def record_grade(self, index, folder_status, score, feedback):
        """Updates the dataframe for a specific student's row."""
        self.df.at[index, 'Matched Folder'] = folder_status
        self.df.at[index, 'Final Score'] = score
        self.df.at[index, 'AI Feedback'] = feedback

    def save(self, output_dir):
        """Saves the dataframe to a new timestamped Excel file in the chosen directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.basename(self.original_filepath).replace(".xlsx", "")
        
        new_filename = f"{base_name}_GRADED_{timestamp}.xlsx"
        
        # Use the user-selected output directory
        save_path = os.path.join(output_dir, new_filename)
        
        try:
            self.df.to_excel(save_path, index=False)
            return save_path
        except Exception as e:
            print(f"[ERROR] Failed to save Excel: {e}")
            return None