import customtkinter as ctk
from src.ui.main_window import AutoGraderWindow

if __name__ == "__main__":
    # Set the theme and color
    ctk.set_appearance_mode("System") 
    ctk.set_default_color_theme("blue")
    
    # Initialize and run the app
    app = AutoGraderWindow()
    app.mainloop()