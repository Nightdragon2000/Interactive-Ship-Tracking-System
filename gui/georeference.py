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


class GeoreferenceWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Georeference Image")
        self.master.geometry("600x540")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_back_button(self.master, self.go_back).place(x=10, y=10)
        create_header(self.master, "Georeference Image")

        create_instructions(
            self.master,
            "• Select an image (TIFF, PNG, JPG, etc.).\n"
            "• Click on 4 points and enter their real coordinates (lat, lon).\n"
            "• Click on an existing point to edit or delete it.\n"
            "• Drag with Right Click to move the image.\n"
            "• Zoom using the mouse wheel.\n"
            "• After 4 valid points, the image will be automatically saved as GeoTIFF."
        )

        create_main_button(
            self.master, "Start Georeferencing Tool", self.run_georeference
        ).pack(pady=(0, 25))

        # Add tip about the known empty window behavior
        tip_frame = tk.Frame(self.master, bg="#e8f0f2", bd=1, relief="solid")
        tip_frame.pack(pady=(0, 20), padx=40)

        tip_label = tk.Label(
            tip_frame,
            text="Note: After completing the process, an empty window may appear.\n"
                 "Please close it manually to return to the main application.",
            font=("Helvetica", 9, "italic"),
            bg="#e8f0f2", fg="#007acc",
            justify="center", wraplength=420
        )
        tip_label.pack(padx=10, pady=10)

    def run_georeference(self):
        try:
            self.master.destroy()

            project_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(project_root, "core", "georeference", "app.py")

            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"{script_path} does not exist.")
                return

            subprocess.run([sys.executable, script_path])

            # Relaunch window after georeferencing closes (even if it fails)
            from gui.georeference import launch_georeference_window
            root = tk.Tk()
            app = GeoreferenceWindow(root)
            root.mainloop()

        except Exception as e:
            messagebox.showerror("Error", f"Could not run georeferencing tool:\n{e}")

    def go_back(self):
        self.master.destroy()
        from gui.calibration import launch_calibration_window
        launch_calibration_window()


def launch_georeference_window():
    root = tk.Tk()
    app = GeoreferenceWindow(root)
    root.mainloop()
