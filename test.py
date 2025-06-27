# main.py

import tkinter as tk
from calibration.camera import camera_calibration
from calibration.projector import projector_calibration

def run_camera():
    camera_calibration()

def run_projector():
    projector_calibration()

root = tk.Tk()
root.title("Calibration Tool")

tk.Button(root, text="Calibrate Camera", command=run_camera, width=25).pack(pady=10)
tk.Button(root, text="Calibrate Projector", command=run_projector, width=25).pack(pady=10)

root.mainloop()
