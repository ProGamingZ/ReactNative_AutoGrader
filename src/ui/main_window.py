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

        # Student Count Display
        self.lbl_student_count = ctk.CTkLabel(self.frame, text="Students loaded: 0", font=ctk.CTkFont(weight="bold"))
        self.lbl_student_count.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # --- Controls Frame ---
        # Start Button
        self.btn_start = ctk.CTkButton(self, text="Start Grading Batch", height=40, fg_color="green", hover_color="darkgreen", state="disabled")
        self.btn_start.grid(row=2, column=0, pady=20)

        # Progress Bar Placeholder
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=3, column=0, pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready. Please select the Excel file and Submissions folder.")
        self.status_label.grid(row=4, column=0)

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