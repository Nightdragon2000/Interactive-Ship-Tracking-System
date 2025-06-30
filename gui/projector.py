import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class ProjectorCalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Projector Calibration")
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
        title = tk.Label(self.master, text="Projector Calibration",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))

        # Instructions
        instructions = (
            "• Select a GeoTIFF image when prompted.\n"
            "• The image will be projected full-screen.\n"
            "• Use mouse wheel to zoom in/out the image.\n"
            "• Drag the image to reposition it.\n"
            "• Press [Enter] to save its position and size.\n"
            "• Press [Esc] to cancel calibration."
        )
        instruction_label = tk.Label(self.master, text=instructions,
                                     font=("Helvetica", 11), bg="#e8f0f2", fg="#333",
                                     justify="center")
        instruction_label.pack(padx=30, pady=(0, 40))

        # Run calibration button
        btn_run = tk.Button(self.master, text="Start Projector Calibration",
                            command=self.run_calibration,
                            font=("Helvetica", 11, "bold"),
                            width=30, height=2,
                            bg="#4a90e2", fg="white",
                            activebackground="#357ABD", activeforeground="white",
                            bd=0, cursor="hand2")
        btn_run.pack()

        

    def run_calibration(self):
        from gui.monitor_selector import select_monitor

        def on_monitor_selected(monitor_index):
            try:
                self.master.destroy()

                # Prepare environment and run calibration script with monitor index
                project_root = os.path.dirname(os.path.dirname(__file__))
                script_path = os.path.join(project_root, "calibration", "projector.py")
                if not os.path.exists(script_path):
                    raise FileNotFoundError(f"{script_path} does not exist.")

                env = os.environ.copy()
                env["SDL_VIDEO_FULLSCREEN_DISPLAY"] = str(monitor_index)

                print(f"[DEBUG] Launching calibration with SDL_VIDEO_FULLSCREEN_DISPLAY={monitor_index}")


                subprocess.run([sys.executable, script_path], env=env)

                # Relaunch calibration window
                import tkinter as tk
                from gui.projector import ProjectorCalibrationWindow
                root = tk.Tk()
                app = ProjectorCalibrationWindow(root)
                root.mainloop()

            except Exception as e:
                messagebox.showerror("Error", f"Could not run projector calibration:\n{e}")

        # Show monitor selection GUI
        select_monitor(on_monitor_selected)


            
    def go_back(self):
        self.master.destroy()
        from gui.calibration import launch_calibration_window
        launch_calibration_window()


def launch_projector_window():
    root = tk.Tk()
    app = ProjectorCalibrationWindow(root)
    root.mainloop()
