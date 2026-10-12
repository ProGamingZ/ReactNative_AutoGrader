import threading
import time
from src.engine.folder_matcher import StudentFolderMatcher
from src.engine.ast_parser import ReactNativeParser
from src.engine.ai_grader import AIGrader
import customtkinter as ctk
from customtkinter import filedialog
import pandas as pd
import os

class AutoGraderWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("React Native Auto-Grader")
        self.geometry("700x550")
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="React Native Auto-Grader", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, pady=(20, 10))

        # --- File Selection Frame ---
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame.grid_columnconfigure(1, weight=1)

        # Excel Selector
        self.lbl_excel = ctk.CTkLabel(self.frame, text="Class List (Excel): None selected")
        self.lbl_excel.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.btn_excel = ctk.CTkButton(self.frame, text="Browse Excel...", command=self.load_excel)
        self.btn_excel.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # Submissions Folder Selector
        self.lbl_folder = ctk.CTkLabel(self.frame, text="Submissions Folder: None selected")
        self.lbl_folder.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        
        self.btn_folder = ctk.CTkButton(self.frame, text="Browse Folder...", command=self.load_folder)
        self.btn_folder.grid(row=1, column=1, padx=10, pady=10, sticky="e")

        # Rubric Selector
        self.lbl_rubric = ctk.CTkLabel(self.frame, text="Select Grading Rubric:")
        self.lbl_rubric.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        
        self.rubric_var = ctk.StringVar(value="Activity 2: Static UI")
        self.dropdown_rubric = ctk.CTkOptionMenu(self.frame, variable=self.rubric_var, values=[
            "Activity 2: Static UI", 
            "Activity 3: Dynamic List", 
            "Activity 4: Navigation"
        ])
        self.dropdown_rubric.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        # Student Count Display
        self.lbl_student_count = ctk.CTkLabel(self.frame, text="Students loaded: 0", font=ctk.CTkFont(weight="bold"))
        self.lbl_student_count.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # --- Controls Frame ---
        # Start Button
        self.btn_start = ctk.CTkButton(self, text="Start Grading Batch", height=40, fg_color="green", hover_color="darkgreen", state="disabled", command=self.start_grading)
        self.btn_start.grid(row=4, column=0, pady=20)

        # Progress Bar Placeholder
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=5, column=0, pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready. Please select the Excel file and Submissions folder.")
        self.status_label.grid(row=6, column=0)

        # Data Storage
        self.students_df = None
        self.submissions_path = None

    def load_excel(self):
        filepath = filedialog.askopenfilename(
            title="Select Class List",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filepath:
            filename = os.path.basename(filepath)
            self.lbl_excel.configure(text=f"Class List: {filename}")
            self.status_label.configure(text="Reading Excel file...")
            
            try:
                # Read the "DATA" sheet, skipping the first two title rows (header=2)
                df = pd.read_excel(filepath, sheet_name="DATA", header=2)
                
                # Drop rows that don't have a valid ID or Name (cleans up empty rows at the bottom)
                df = df.dropna(subset=['ID', 'NAME'])
                
                self.students_df = df
                count = len(self.students_df)
                self.lbl_student_count.configure(text=f"Students loaded: {count}")
                self.status_label.configure(text="Excel loaded successfully.")
                self.check_ready_state()
                
            except Exception as e:
                self.status_label.configure(text=f"Error reading Excel: {str(e)}")
                self.students_df = None

    def load_folder(self):
        folderpath = filedialog.askdirectory(title="Select Submissions Folder")
        if folderpath:
            self.submissions_path = folderpath
            foldername = os.path.basename(folderpath)
            self.lbl_folder.configure(text=f"Submissions Folder: {foldername}")
            self.status_label.configure(text="Folder selected successfully.")
            self.check_ready_state()

    def check_ready_state(self):
        # Only enable the Start button if both the Excel file and Folder are selected
        if self.students_df is not None and self.submissions_path is not None:
            self.btn_start.configure(state="normal")
            self.status_label.configure(text="Ready to begin grading.")

    def start_grading(self):
        # Disable UI elements so the user doesn't click them while grading
        self.btn_start.configure(state="disabled")
        self.btn_excel.configure(state="disabled")
        self.btn_folder.configure(state="disabled")
        self.status_label.configure(text="Initializing grading engine...")
        
        # Reset progress bar
        self.progress.set(0)

        # Launch the grading process in a background thread to prevent UI freezing
        thread = threading.Thread(target=self._run_grading_batch)
        thread.daemon = True # Closes the thread if the main app is closed
        thread.start()

    def _run_grading_batch(self):
        # Guard clause: Proves to Pylance that these are not None
        if self.students_df is None or self.submissions_path is None:
            return

        matcher = StudentFolderMatcher(self.submissions_path)
        total_students = len(self.students_df)
        
        # Use enumerate to get a strict integer count starting at 1
        for count, (index, row) in enumerate(self.students_df.iterrows(), start=1):
            student_name = str(row['NAME'])
            
            # Safely update UI from the thread
            self.status_label.configure(text=f"Scanning ({count}/{total_students}): {student_name}")
            
            # Attempt to find their submission folder
            matched_folder = matcher.find_match(student_name)
            
            if matched_folder:
                student_folder_path = os.path.join(self.submissions_path, matched_folder)
                parser = ReactNativeParser(student_folder_path)
                
                print(f"\n[FOUND] {student_name} -> {matched_folder} ({parser.file_count} files)")
                
                if parser.file_count > 0:
                    # 1. Objective Check
                    objective_results = parser.check_objective_rubric()
                    
                    # 2. AI Evaluation
                    self.status_label.configure(text=f"AI Evaluating ({count}/{total_students}): {student_name}")
                    grader = AIGrader(model_name="llama3") 
                    selected_rubric = self.rubric_var.get()
                    
                    # Call the AI! (This may take a few seconds per student depending on your PC)
                    ai_result = grader.evaluate(parser.raw_code, objective_results, selected_rubric)
                    
                    print(f"   [AI GRADE] {ai_result['final_score']}/100")
                    print(f"   [FEEDBACK] {ai_result['feedback']}")
                    
                    # TODO: Save to Excel
                else:
                    print("   [WARNING] No .js/.tsx files found.")
            
        # Re-enable the UI when finished
        self.status_label.configure(text="Batch scanning complete! Check the terminal output.")
        self.btn_start.configure(state="normal")
        self.btn_excel.configure(state="normal")
        self.btn_folder.configure(state="normal")
    