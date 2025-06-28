# main.py

import tkinter as tk
from tkinter import messagebox

# Import calibration tools
from calibration.camera import camera_calibration
from calibration.projector import projector_calibration

# Import the georeference GUI class
from georeference.app import GeoreferencingApp

def create_main_window():
    root = tk.Tk()
    root.title("Calibration & Georeference Tool")
    root.geometry("300x250")

    def run_tool(func):
        try:
            func()
        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{e}")

    # Buttons
    tk.Button(root, text="Camera Calibration", command=lambda: run_tool(camera_calibration)).pack(pady=10)
    tk.Button(root, text="Projector Calibration", command=lambda: run_tool(projector_calibration)).pack(pady=10)
    tk.Button(root, text="Georeference Image", command=lambda: GeoreferencingApp().root.mainloop()).pack(pady=10)
    tk.Button(root, text="Exit", command=root.destroy).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_main_window()
