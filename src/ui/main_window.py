import threading
import time
from src.engine.folder_matcher import StudentFolderMatcher
from src.engine.ast_parser import ReactNativeParser
from src.engine.ai_grader import AIGrader
from src.engine.excel_reporter import ExcelReporter
from src.models.grade_result import GradeResult
import customtkinter as ctk
from customtkinter import filedialog
import pandas as pd
import os

class AutoGraderWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("React Native Auto-Grader")
        self.geometry("750x650")
        self.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(self, text="React Native Auto-Grader", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, pady=(20, 10))

        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame.grid_columnconfigure(1, weight=1)

        # 1. Excel Selector
        self.lbl_excel = ctk.CTkLabel(self.frame, text="Class List (.xlsx): None")
        self.lbl_excel.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.btn_excel = ctk.CTkButton(self.frame, text="Browse Excel...", command=self.load_excel)
        self.btn_excel.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # 2. Submissions Selector
        self.lbl_folder = ctk.CTkLabel(self.frame, text="Submissions (Folder): None")
        self.lbl_folder.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.btn_folder = ctk.CTkButton(self.frame, text="Browse Folder...", command=self.load_folder)
        self.btn_folder.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        # 3. Dynamic Rubric Selector
        self.lbl_rubric = ctk.CTkLabel(self.frame, text="Grading Rubric (.md): None")
        self.lbl_rubric.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.btn_rubric = ctk.CTkButton(self.frame, text="Browse Rubric...", command=self.load_rubric)
        self.btn_rubric.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        # 4. Output Directory Selector
        self.lbl_output = ctk.CTkLabel(self.frame, text="Save Report To: None")
        self.lbl_output.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.btn_output = ctk.CTkButton(self.frame, text="Browse Output...", command=self.load_output_folder)
        self.btn_output.grid(row=3, column=1, padx=10, pady=10, sticky="e")

        # 5. Output Filename & Model Selection Row
        self.filename_var = ctk.StringVar(value="Graded_Report")
        self.entry_filename = ctk.CTkEntry(self.frame, textvariable=self.filename_var, width=150)
        self.entry_filename.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        
        self.model_var = ctk.StringVar(value="phi3")
        self.dropdown_model = ctk.CTkOptionMenu(self.frame, variable=self.model_var, values=["phi3", "llama3"])
        self.dropdown_model.grid(row=4, column=1, padx=10, pady=10, sticky="e")

        self.lbl_student_count = ctk.CTkLabel(self.frame, text="Students loaded: 0", font=ctk.CTkFont(weight="bold"))
        self.lbl_student_count.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.btn_start = ctk.CTkButton(self, text="Start Grading Batch", height=40, fg_color="green", hover_color="darkgreen", state="disabled", command=self.start_grading)
        self.btn_start.grid(row=2, column=0, pady=10)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=3, column=0, pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready. Please configure all settings.")
        self.status_label.grid(row=4, column=0)

        # Paths and Data
        self.students_df = None
        self.excel_filepath = None
        self.submissions_path = None
        self.rubric_path = None
        self.rubric_text = ""
        self.output_path = None

    def load_excel(self):
        filepath = filedialog.askopenfilename(title="Select Class List", filetypes=[("Excel files", "*.xlsx")])
        if filepath:
            self.excel_filepath = filepath
            self.lbl_excel.configure(text=f"Class List: {os.path.basename(filepath)}")
            try:
                df = pd.read_excel(filepath, sheet_name="DATA", header=2).dropna(subset=['ID', 'NAME'])
                self.students_df = df
                self.lbl_student_count.configure(text=f"Students loaded: {len(self.students_df)}")
                self.check_ready_state()
            except Exception as e:
                self.status_label.configure(text=f"Error reading Excel: {e}")

    def load_folder(self):
        folderpath = filedialog.askdirectory(title="Select Submissions Folder")
        if folderpath:
            self.submissions_path = folderpath
            self.lbl_folder.configure(text=f"Submissions: {os.path.basename(folderpath)}")
            self.check_ready_state()

    def load_rubric(self):
        filepath = filedialog.askopenfilename(title="Select Rubric File", filetypes=[("Markdown", "*.md")])
        if filepath:
            self.rubric_path = filepath
            self.lbl_rubric.configure(text=f"Grading Rubric: {os.path.basename(filepath)}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.rubric_text = f.read()
                self.check_ready_state()
            except Exception as e:
                self.status_label.configure(text=f"Error reading Rubric: {e}")

    def load_output_folder(self):
        folderpath = filedialog.askdirectory(title="Select Output Folder")
        if folderpath:
            self.output_path = folderpath
            self.lbl_output.configure(text=f"Save Report To: .../{os.path.basename(folderpath)}")
            self.check_ready_state()

    def check_ready_state(self):
        if all([self.students_df is not None, self.submissions_path, self.rubric_path, self.output_path]):
            self.btn_start.configure(state="normal")
            self.status_label.configure(text="Ready to begin grading.")

    def start_grading(self):
        self.btn_start.configure(state="disabled")
        self.progress.set(0)
        threading.Thread(target=self._run_grading_batch, daemon=True).start()

    def _run_grading_batch(self):
        # GUARD CLAUSE: Proves to Pylance that these are populated before we use them
        if self.students_df is None or self.submissions_path is None or self.output_path is None:
            return

        matcher = StudentFolderMatcher(self.submissions_path)
        reporter = ExcelReporter(self.students_df, self.excel_filepath)
        total = len(self.students_df)
        
        for count, (index, row) in enumerate(self.students_df.iterrows(), start=1):
            student_name = str(row['NAME'])
            self.status_label.configure(text=f"Scanning ({count}/{total}): {student_name}")
            matched_folder = matcher.find_match(student_name)
            
            if matched_folder:
                student_folder_path = os.path.join(self.submissions_path, matched_folder)
                parser = ReactNativeParser(student_folder_path)
                
                if parser.file_count > 0:
                    self.status_label.configure(text=f"AI Evaluating ({count}/{total}): {student_name}")
                    grader = AIGrader(model_name=self.model_var.get())
                    ai_result = grader.evaluate(parser.raw_code, parser.check_objective_rubric(), self.rubric_text)
                    
                    scores_dict = ai_result.get('scores', {})
                    
                    # Programmatically calculate the total score in Python
                    calculated_total = sum(int(val) for val in scores_dict.values() if isinstance(val, (int, float)))
                    
                    result = GradeResult(
                        student_name=student_name,
                        matched_folder=f"Matched ({parser.file_count})",
                        file_count=parser.file_count,
                        scores=scores_dict,
                        final_score=calculated_total,  # Python-computed sum
                        feedback=ai_result.get('feedback', '')
                    )
                else:
                    result = GradeResult(student_name=student_name, matched_folder="Empty", file_count=0, feedback="No .js/.tsx files.")
            else:
                result = GradeResult(student_name=student_name, matched_folder="Missing", file_count=0, feedback="Folder not found.")

            reporter.record_grade(index, result)
            self.progress.set(count / total)
            
        saved_path = reporter.save(self.output_path, self.filename_var.get())
        if saved_path:
            self.status_label.configure(text=f"Complete! Saved to: {os.path.basename(saved_path)}")
        else:
            self.status_label.configure(text="Complete, but failed to save Excel file.")
            
        self.btn_start.configure(state="normal")
    