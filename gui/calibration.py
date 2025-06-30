import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
from gui.camera import launch_camera_window
from gui.projector import launch_projector_window
from gui.georeference import launch_georeference_window
from gui.database import launch_database_window




class CalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Setup & Calibration")
        self.master.geometry("600x560")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        # Back button (top-left)
        btn_back = tk.Button(self.master, text="← Go Back", command=self.back_to_main,
                             font=("Helvetica", 14), bg="#e8f0f2", fg="#1f3b4d",
                             bd=0, highlightthickness=0,
                             activebackground="#e8f0f2", activeforeground="#1f3b4d",
                             cursor="hand2")
        btn_back.place(x=10, y=10)

        # Title
        title = tk.Label(self.master, text="Setup & Calibration",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))

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
            ("Georeference Image", self.georeference_image),
            ("Camera Calibration", self.camera_calibration),
            ("Projector Calibration", self.projector_calibration),
        ]

        for text, command in options:
            tk.Button(button_frame, text=text, command=command, **btn_style).pack(pady=7)

        # First-time user guidance (styled note)
        note_frame = tk.Frame(self.master, bg="#d9edf7", bd=2, relief="solid")
        note_frame.pack(padx=40, pady=(20, 10), fill="x")

        note_label = tk.Label(note_frame,
                              text="💡 Tip: If this is your first time running the program,\nplease complete all the above steps in order.",
                              font=("Helvetica", 10, "italic"),
                              bg="#d9edf7", fg="#31708f", justify="center", wraplength=480)
        note_label.pack(padx=10, pady=10)

    def back_to_main(self):
        self.master.destroy()
        from gui.start import launch_start_window  # ✅ Import here to avoid circular import
        launch_start_window()

    def setup_database(self):
        self.master.destroy()
        launch_database_window()

    def camera_calibration(self):
        self.master.destroy()
        launch_camera_window()

    def projector_calibration(self):
        self.master.destroy()
        launch_projector_window()

    def georeference_image(self):
        self.master.destroy()
        launch_georeference_window()


def launch_calibration_window():
    root = tk.Tk()
    app = CalibrationWindow(root)
    root.mainloop()
