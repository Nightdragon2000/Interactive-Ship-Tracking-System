import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class CameraCalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Camera Calibration")
        self.master.geometry("600x500")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        # Back button
        btn_back = tk.Button(self.master, text="← Go Back", command=self.go_back,
                             font=("Helvetica", 14), bg="#e8f0f2", fg="#1f3b4d",
                             bd=0, highlightthickness=0,
                             activebackground="#e8f0f2", activeforeground="#1f3b4d",
                             cursor="hand2")
        btn_back.place(x=10, y=10)

        # Title
        title = tk.Label(self.master, text="Camera Calibration",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))

        # Instructions
        instructions = (
            "• Make sure your camera is connected.\n"
            "• A blue rectangle will appear on the camera feed.\n"
            "• Drag the corners or move the rectangle to adjust.\n"
            "• Press [Enter] to save the rectangle.\n"
            "• Press [Esc] to cancel the calibration."
        )
        instruction_label = tk.Label(self.master, text=instructions,
                                     font=("Helvetica", 11), bg="#e8f0f2", fg="#333",
                                     justify="center")
        instruction_label.pack(padx=30, pady=(0, 40))

        # Run calibration button (text only)
        btn_run = tk.Button(self.master, text="Start Camera Calibration",
                            command=self.run_calibration,
                            font=("Helvetica", 11, "bold"),
                            width=30, height=2,
                            bg="#4a90e2", fg="white",
                            activebackground="#357ABD", activeforeground="white",
                            bd=0, cursor="hand2")
        btn_run.pack()

    def run_calibration(self):
        try:
            # Dynamically resolve the correct path relative to project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(project_root, "calibration", "camera.py")
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"{script_path} does not exist.")
            subprocess.run([sys.executable, script_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not run camera calibration:\n{e}")

    def go_back(self):
        self.master.destroy()
        
        # Delayed import to avoid circular reference
        from gui.calibration import launch_calibration_window
        launch_calibration_window()



def launch_camera_window():
    root = tk.Tk()
    app = CameraCalibrationWindow(root)
    root.mainloop()
