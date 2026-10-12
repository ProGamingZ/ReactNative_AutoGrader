import pandas as pd
import os
from datetime import datetime
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment
from src.models.grade_result import GradeResult
import logging
logger = logging.getLogger("AutoGrader")

class ExcelReporter:
    def __init__(self, original_df, original_filepath):
        self.df = original_df.copy()
        self.original_filepath = original_filepath
        # Track dynamically added rubric columns
        self.rubric_columns = []

    def record_grade(self, index, result: GradeResult):
        """Updates the dataframe for a specific student's row using GradeResult."""
        result_dict = result.to_dict()
        
        # Save rubric criterion names as they appear so we can order them later
        for criterion in result.scores.keys():
            if criterion not in self.rubric_columns:
                self.rubric_columns.append(criterion)
                
        for col_name, value in result_dict.items():
            self.df.at[index, col_name] = value

    def save(self, output_dir, custom_filename):
        """Saves the dataframe to a formatted Excel file in the chosen directory."""
        if not custom_filename.endswith(".xlsx"):
            custom_filename += ".xlsx"
            
        save_path = os.path.join(output_dir, custom_filename)
        
        # 1. Reorder the columns
        # Dynamically grab the first 5 columns (NO, ID, NAME, PROGRAM, YEAR)
        original_cols = list(self.df.columns)[:5] 
        base_cols = original_cols + ['Matched Folder', 'File Count']
        
        # Assemble the final column order
        final_cols = base_cols + self.rubric_columns + ['Final Score', 'AI Feedback']
        
        # Keep only the columns that actually exist to prevent Pandas KeyErrors
        final_cols = [col for col in final_cols if col in self.df.columns]
        self.df = self.df[final_cols]
        
        try:
            # 2. Export and Format using openpyxl
            with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
                self.df.to_excel(writer, index=False, sheet_name='GRADES')
                
                # Access the openpyxl worksheet object
                worksheet = writer.sheets['GRADES']
                
                # 3. Apply Column Widths and Text Wrapping
                for col_idx, col_name in enumerate(self.df.columns, start=1):
                    column_letter = get_column_letter(col_idx)
                    
                    # Wrap text and align to the top for every cell in this column
                    for cell in worksheet[column_letter]:
                        cell.alignment = Alignment(wrap_text=True, vertical='top')
                    
                    # Set precise column widths based on the column name
                    if col_name == 'AI Feedback':
                        width = 55
                    elif col_name in self.rubric_columns:
                        width = 12  # Narrow for numbers, allows header text to wrap
                    elif col_name == 'NAME':
                        width = 25
                    elif col_name == 'Matched Folder':
                        width = 18
                    elif col_name == 'ID':
                        width = 16
                    elif col_name in ['NO', 'File Count', 'Final Score', 'YEAR']:
                        width = 10
                    elif col_name == 'PROGRAM':
                        width = 12
                    else:
                        width = 15  # Default fallback width
                        
                    worksheet.column_dimensions[column_letter].width = width
                    
            return save_path
        except Exception as e:
            print(f"[ERROR] Failed to save Excel: {e}")
            return None