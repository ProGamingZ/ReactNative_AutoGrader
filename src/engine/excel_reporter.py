import pandas as pd
import os
from datetime import datetime
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from src.models.grade_result import GradeResult
import logging
logger = logging.getLogger("AutoGrader")

class ExcelReporter:
    def __init__(self, original_df, original_filepath, rubric_columns: list):
        self.df = original_df.copy()
        self.original_filepath = original_filepath
        # Fixed rubric columns extracted directly from the Markdown file
        self.rubric_columns = list(rubric_columns)

        # Pre-create all required columns in exact order
        self.df['Folder & Files'] = "0/0"
        for col in self.rubric_columns:
            self.df[col] = 0
        self.df['Final Score'] = 0
        self.df['AI Feedback'] = ""

    def record_grade(self, index, result: GradeResult):
        """Updates the dataframe for a specific student's row using only pre-allocated columns."""
        self.df.at[index, 'Folder & Files'] = result.folder_and_files
        for criterion in self.rubric_columns:
            self.df.at[index, criterion] = result.scores.get(criterion, 0)
        self.df.at[index, 'Final Score'] = result.final_score
        self.df.at[index, 'AI Feedback'] = result.feedback

    def save(self, output_dir, custom_filename):
        """Saves the dataframe to a formatted Excel file in the chosen directory."""
        if not custom_filename.endswith(".xlsx"):
            custom_filename += ".xlsx"
            
        save_path = os.path.join(output_dir, custom_filename)
        
        # 1. Enforce exact column order:
        # NO, ID, NAME, PROGRAM, YEAR, Folder & Files, [Rubric Categories...], Final Score, AI Feedback
        original_cols = list(self.df.columns)[:5]
        final_cols = original_cols + ['Folder & Files'] + self.rubric_columns + ['Final Score', 'AI Feedback']
        
        final_cols = [col for col in final_cols if col in self.df.columns]
        self.df = self.df[final_cols]
        
        try:
            # 2. Export and Format using openpyxl
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                self.df.to_excel(writer, index=False, sheet_name='GRADES')
                worksheet = writer.sheets['GRADES']
                
                # 3. Apply Column Widths and Text Wrapping
                for col_idx, col_name in enumerate(self.df.columns, start=1):
                    column_letter = get_column_letter(col_idx)
                    
                    for cell in worksheet[column_letter]:
                        cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
                    if col_name == 'AI Feedback':
                        width = 38
                    elif col_name in self.rubric_columns:
                        width = 14
                    elif col_name == 'NAME':
                        width = 25
                    elif col_name == 'Folder & Files':
                        width = 15
                    elif col_name == 'ID':
                        width = 16
                    elif col_name in ['NO', 'Final Score', 'YEAR']:
                        width = 10
                    elif col_name == 'PROGRAM':
                        width = 12
                    else:
                        width = 15
                        
                    worksheet.column_dimensions[column_letter].width = width
                    
            return save_path
        except Exception as e:
            logger.error(f"Failed to save Excel: {e}")
            return None