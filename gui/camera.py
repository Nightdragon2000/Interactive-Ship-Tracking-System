import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess

from gui.gui_components import (
    create_back_button,
    create_header,
    create_instructions,
    create_main_button
)

class CameraCalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Camera Calibration")
        self.master.geometry("600x500")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_back_button(self.master, self.go_back).place(x=10, y=10)
        create_header(self.master, "Camera Calibration")

        create_instructions(self.master,
            "• Make sure your camera is connected.\n"
            "• A blue rectangle will appear on the camera feed.\n"
            "• Drag the corners or move the rectangle to adjust.\n"
            "• Press [Enter] to save the rectangle.\n"
            "• Press [Esc] to cancel the calibration."
        )

        create_main_button(self.master, "Start Camera Calibration", self.run_calibration).pack()

    def run_calibration(self):
        try:
            project_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(project_root, "core", "calibration", "camera.py")

            subprocess.run([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not run camera calibration:\n{e}")

    def go_back(self):
        self.master.destroy()
        from gui.calibration import launch_calibration_window
        launch_calibration_window()

def launch_camera_window():
    root = tk.Tk()
    app = CameraCalibrationWindow(root)
    root.mainloop()
