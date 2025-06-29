import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from gui.camera import launch_camera_window
from gui.projector import launch_projector_window
from gui.georeference import launch_georeference_window


class CalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Setup & Calibration")
        self.master.geometry("600x520")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        # Back button (top-left arrow only)
        btn_back = tk.Button(self.master, text="← Go Back", command=self.back_to_main,
                             font=("Helvetica", 14), bg="#e8f0f2", fg="#1f3b4d",
                             bd=0, highlightthickness=0,
                             activebackground="#e8f0f2", activeforeground="#1f3b4d",
                             cursor="hand2")
        btn_back.place(x=10, y=10)

        # Title
        title = tk.Label(self.master, text="Setup & Calibration",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))  # Lower to avoid back button

        # Subtitle
        subtitle = tk.Label(self.master, text="Choose a configuration option",
                            font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b")
        subtitle.pack(pady=(0, 20))

        # Button container
        button_frame = tk.Frame(self.master, bg="#e8f0f2")
        button_frame.pack()

        btn_style = {
            "font": ("Helvetica", 11, "bold"),
            "width": 25,
            "height": 2,
            "bg": "#4a90e2",
            "fg": "white",
            "activebackground": "#357ABD",
            "activeforeground": "white",
            "bd": 0,
            "cursor": "hand2"
        }

        # Setup options
        options = [
            ("Setup Database", self.setup_database),
            ("Camera Calibration", self.camera_calibration),
            ("Projector Calibration", self.projector_calibration),
            ("Georeference Image", self.georeference_image),
            ("Full Setup Wizard", self.full_setup),
        ]

        for text, command in options:
            tk.Button(button_frame, text=text, command=command, **btn_style).pack(pady=7)

    def back_to_main(self):
        self.master.destroy()
        subprocess.Popen([sys.executable, "launcher.py"])


    def setup_database(self):
        messagebox.showinfo("Setup", "Database setup (placeholder)")

    def camera_calibration(self):
        self.master.destroy()
        launch_camera_window()

    def projector_calibration(self):
        self.master.destroy()
        launch_projector_window()

    def georeference_image(self):        
        self.master.destroy()
        launch_georeference_window()

    def full_setup(self):
        messagebox.showinfo("Setup", "Full setup wizard (placeholder)")

def launch_calibration_window():
    root = tk.Tk()
    app = CalibrationWindow(root)
    root.mainloop()
