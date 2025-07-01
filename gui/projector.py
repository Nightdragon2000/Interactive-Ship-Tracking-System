import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess

from gui.monitor_selector import select_monitor
from gui.gui_components import (
    create_back_button,
    create_header,
    create_instructions,
    create_main_button
)

class ProjectorCalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Projector Calibration")
        self.master.geometry("600x500")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_back_button(self.master, self.go_back).place(x=10, y=10)
        create_header(self.master, "Projector Calibration")

        create_instructions(self.master,
            "• Select a GeoTIFF image when prompted.\n"
            "• The image will be projected full-screen.\n"
            "• Use mouse wheel to zoom in/out the image.\n"
            "• Drag the image to reposition it.\n"
            "• Press [Enter] to save its position and size.\n"
            "• Press [Esc] to cancel calibration."
        )

        create_main_button(self.master, "Start Projector Calibration", self.run_calibration).pack()

    def run_calibration(self):
        def on_monitor_selected(monitor_index):
            try:
                self.master.destroy()

                project_root = os.path.dirname(os.path.dirname(__file__))
                script_path = os.path.join(project_root, "core", "calibration", "projector.py")

                if not os.path.exists(script_path):
                    raise FileNotFoundError(f"{script_path} does not exist.")

                env = os.environ.copy()
                env["SDL_VIDEO_FULLSCREEN_DISPLAY"] = str(monitor_index)

                subprocess.run([sys.executable, script_path], env=env)

                from gui.projector import launch_projector_window
                root = tk.Tk()
                app = ProjectorCalibrationWindow(root)
                root.mainloop()

            except Exception as e:
                messagebox.showerror("Error", f"Could not run projector calibration:\n{e}")

        select_monitor(on_monitor_selected)

    def go_back(self):
        self.master.destroy()
        from gui.calibration import launch_calibration_window
        launch_calibration_window()

def launch_projector_window():
    root = tk.Tk()
    app = ProjectorCalibrationWindow(root)
    root.mainloop()
