import customtkinter as ctk

class AutoGraderWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("React Native Auto-Grader")
        self.geometry("700x500")
        self.grid_columnconfigure(0, weight=1)

        # Header
        self.header = ctk.CTkLabel(self, text="React Native Auto-Grader", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.grid(row=0, column=0, pady=(20, 10))

        # Placeholder for File Selection Layout
        self.frame = ctk.CTkFrame(self)
        self.frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.frame.grid_columnconfigure(1, weight=1)

        self.lbl_excel = ctk.CTkLabel(self.frame, text="Class List (Excel):")
        self.lbl_excel.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        self.btn_excel = ctk.CTkButton(self.frame, text="Browse...")
        self.btn_excel.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # Start Button
        self.btn_start = ctk.CTkButton(self, text="Start Grading Batch", height=40, fg_color="green", hover_color="darkgreen")
        self.btn_start.grid(row=2, column=0, pady=20)

        # Progress Bar Placeholder
        self.progress = ctk.CTkProgressBar(self, width=400)
        self.progress.grid(row=3, column=0, pady=10)
        self.progress.set(0)
        
        self.status_label = ctk.CTkLabel(self, text="Ready...")
        self.status_label.grid(row=4, column=0)