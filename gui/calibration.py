import tkinter as tk
from gui.camera import launch_camera_window
from gui.projector import launch_projector_window
from gui.georeference import launch_georeference_window
from gui.database import launch_database_window
from gui.gui_components import (
    create_back_button,
    create_header,
    create_main_button
)

class CalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Setup & Calibration")
        self.master.geometry("600x550")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_back_button(self.master, self.back_to_main).place(x=10, y=10)

        create_header(self.master, "Setup & Calibration")

        tk.Label(self.master, text="Select a setup component to configure",
                 font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b").pack(pady=(0, 20))

        button_frame = tk.Frame(self.master, bg="#e8f0f2")
        button_frame.pack()

        options = [
            ("Setup Database", self.setup_database),
            ("Georeference Image", self.georeference_image),
            ("Camera Calibration", self.camera_calibration),
            ("Projector Calibration", self.projector_calibration),
        ]

        for text, command in options:
            create_main_button(button_frame, text, command).pack(pady=7)

        note_frame = tk.Frame(self.master, bg="#d9edf7", bd=2, relief="solid")
        note_frame.pack(padx=40, pady=(20, 10), fill="x")

        tk.Label(note_frame,
                 text="💡 Tip: If this is your first time running the program,\n"
                      "please complete all the above steps in order.",
                 font=("Helvetica", 10, "italic"),
                 bg="#d9edf7", fg="#31708f", justify="center", wraplength=480).pack(padx=10, pady=10)

    def back_to_main(self):
        self.master.destroy()
        from gui.main_menu import launch_start_window
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
