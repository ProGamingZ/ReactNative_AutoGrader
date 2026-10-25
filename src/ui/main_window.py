import logging
from datetime import datetime
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


class TextBoxLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Tkinter is not thread-safe. We use .after(0) to safely push updates to the UI
        def append():
            self.text_widget.configure(state="normal")
            self.text_widget.insert("end", msg + "\n")
            self.text_widget.configure(state="disabled")
            self.text_widget.yview("end")  # Auto-scroll to bottom
        self.text_widget.after(0, append)
class AutoGraderWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("React Native Auto-Grader")
        self.geometry("650x750")
        self.minsize(650, 750)
        self.maxsize(900, 900)
        self.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkLabel(self, text="React Native Auto-Grader", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, pady=(10, 5))

        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
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
        
        self.model_var = ctk.StringVar(value="qwen2.5-coder:3b")
        self.dropdown_model = ctk.CTkOptionMenu(
            self.frame,
            variable=self.model_var,
            values=["qwen2.5-coder:3b", "qwen2.5-coder:1.5b", "llama3.2:3b", "llama3"]
        )
        self.dropdown_model.grid(row=4, column=1, padx=10, pady=10, sticky="e")

        self.lbl_student_count = ctk.CTkLabel(self.frame, text="Students loaded: 0", font=ctk.CTkFont(weight="bold"))
        self.lbl_student_count.grid(row=5, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        self.stop_event = threading.Event()

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, pady=10)

        self.btn_start = ctk.CTkButton(
            self.btn_frame, text="Start Grading Batch", width=190, height=40,
            fg_color="green", hover_color="darkgreen", state="disabled", command=self.start_grading
        )
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = ctk.CTkButton(
            self.btn_frame, text="Stop & Save", width=190, height=40,
            fg_color="#b30000", hover_color="#7a0000", state="disabled", command=self.stop_grading
        )
        self.btn_stop.grid(row=0, column=1, padx=10)

        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=3, column=0, pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready. Please configure all settings.")
        self.status_label.grid(row=4, column=0)

        # Diagnostic Terminal
        self.terminal = ctk.CTkTextbox(self, height=200, state="disabled", fg_color="black", text_color="lightgreen", font=ctk.CTkFont(family="Consolas", size=11))
        self.terminal.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")
        self.grid_rowconfigure(5, weight=1)

        # Setup Base Logger
        self.logger = logging.getLogger("AutoGrader")
        self.logger.setLevel(logging.DEBUG) # Capture everything internally
        
        # Wire Logger to the UI Terminal (Only show INFO and above)
        self.ui_handler = TextBoxLogHandler(self.terminal)
        self.ui_handler.setLevel(logging.INFO)
        self.ui_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))
        self.logger.addHandler(self.ui_handler)

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
        output_path = self.output_path
        if output_path is None:
            self.status_label.configure(text="Please select an output folder before starting.")
            return

        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.set(0)
        self.terminal.configure(state="normal")
        self.terminal.delete("1.0", "end") # Clear terminal on new run
        self.terminal.configure(state="disabled")
        
        # Setup File Handler (Write everything to .log file)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(output_path, f"Diagnostic_Report_{timestamp}.log")
        
        self.file_handler = logging.FileHandler(log_file, encoding='utf-8')
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s'))
        self.logger.addHandler(self.file_handler)
        
        self.logger.info("--- STARTED NEW GRADING BATCH ---")
        self.logger.debug(f"Target Output Directory: {self.output_path}")

        threading.Thread(target=self._run_grading_batch, daemon=True).start()

    def stop_grading(self):
        """Signals the background thread and Ollama stream to stop immediately and save."""
        if not self.stop_event.is_set():
            self.stop_event.set()
            self.btn_stop.configure(state="disabled")
            self.status_label.configure(text="Stopping batch... Saving analyzed data...")
            self.logger.warning("--- STOP REQUESTED BY USER: Halting and saving partial report... ---")

    def _set_stop_btn(self, state: str):
        """Thread-safe helper to enable/disable the stop button."""
        self.after(0, lambda: self.btn_stop.configure(state=state))

    def _set_status(self, text: str):
        """Thread-safe helper to update the status label."""
        self.after(0, lambda: self.status_label.configure(text=text))

    def _set_progress(self, value: float):
        """Thread-safe helper to update the progress bar."""
        self.after(0, lambda: self.progress.set(value))

    def _set_start_btn(self, state: str):
        """Thread-safe helper to enable/disable the start button."""
        self.after(0, lambda: self.btn_start.configure(state=state))

    def _run_grading_batch(self):
        if self.students_df is None or self.submissions_path is None or self.output_path is None:
            return

        # Start of the Graceful Teardown pattern
        try:
            rubric_categories = AIGrader.extract_rubric_categories(self.rubric_text)
            matcher = StudentFolderMatcher(self.submissions_path)
            reporter = ExcelReporter(self.students_df, self.excel_filepath, rubric_categories)
            total = len(self.students_df)
            zero_scores = {cat: 0 for cat in rubric_categories}
            
            for count, (index, row) in enumerate(self.students_df.iterrows(), start=1):
                if self.stop_event.is_set():
                    self.logger.info(f"Batch stopped at student {count}/{total}. Saving analyzed records...")
                    break

                student_name = str(row['NAME'])
                self._set_status(f"Grading ({count}/{total}): {student_name}")
                self.logger.info(f"Processing Student ({count}/{total}): {student_name}")
                
                matched_folder = matcher.find_match(student_name)
                
                if matched_folder:
                    student_folder_path = os.path.join(self.submissions_path, matched_folder)
                    parser = ReactNativeParser(student_folder_path)
                    folder_file_ratio = f"{parser.folder_count}/{parser.file_count}"
                    
                    if parser.file_count > 0:
                        self.logger.info(f"Extracted {folder_file_ratio} (Folders/Files). Running AI Evaluation...")
                        grader = AIGrader(model_name=self.model_var.get())
                        ai_result = grader.evaluate(
                            parser.raw_code,
                            parser.check_objective_rubric(self.rubric_text),
                            self.rubric_text,
                            rubric_categories,
                            stop_event=self.stop_event
                        )
                        
                        # If user clicked Stop while AI was mid-evaluation, exit loop and save previous data
                        if ai_result is None or self.stop_event.is_set():
                            self.logger.info(f"Aborted in-progress evaluation for {student_name}.")
                            break
                        
                        scores_dict = ai_result.get('scores', zero_scores)
                        calculated_total = sum(int(val) for val in scores_dict.values() if isinstance(val, (int, float)))
                        
                        result = GradeResult(
                            student_name=student_name,
                            folder_and_files=folder_file_ratio,
                            scores=scores_dict,
                            final_score=calculated_total,
                            feedback=ai_result.get('feedback', '')
                        )
                        self.logger.info(f"Score: {calculated_total} | Done.")
                    else:
                        self.logger.warning(f"Folder matched ({folder_file_ratio}) but contained NO valid React Native files.")
                        result = GradeResult(
                            student_name=student_name,
                            folder_and_files=folder_file_ratio,
                            scores=zero_scores.copy(),
                            final_score=0,
                            feedback="Empty folder. No .js/.tsx files."
                        )
                else:
                    self.logger.warning(f"No LMS folder match found for {student_name}.")
                    result = GradeResult(
                        student_name=student_name,
                        folder_and_files="0/0",
                        scores=zero_scores.copy(),
                        final_score=0,
                        feedback="Folder not found."
                    )

                reporter.record_grade(index, result)
                self._set_progress(count / total)
                
            saved_path = reporter.save(self.output_path, self.filename_var.get())
            if saved_path:
                self.logger.info(f"--- BATCH COMPLETE ---")
                self.logger.info(f"Report saved to: {os.path.basename(saved_path)}")
                self._set_status("Complete! Check terminal for details.")
            else:
                self.logger.error("Batch complete, but failed to save Excel file.")
                self._set_status("Complete, but failed to save Excel file.")
                
        except Exception as e:
            # Catch unexpected crashes so they don't break the thread silently
            self.logger.error(f"FATAL BATCH ERROR: {e}")
            self._set_status("Grading stopped due to an error.")
            
        finally:
            # THIS ALWAYS RUNS: Releasing system resources
            self._set_stop_btn("disabled")
            self._set_start_btn("normal")
            
            # Explicitly close the file lock and remove the handler so the .log file can be edited
            if hasattr(self, 'file_handler') and self.file_handler:
                self.file_handler.close()
                self.logger.removeHandler(self.file_handler)
                self.file_handler = None
    