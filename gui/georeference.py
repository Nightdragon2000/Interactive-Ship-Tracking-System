import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class GeoreferenceWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Georeference Image")
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
        title = tk.Label(self.master, text="Georeference Image",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))

        # Instructions
        instructions = (
            "• Select an image (TIFF, PNG, JPG, etc.).\n"
            "• Click 4 points on the image and enter their real coordinates.\n"
            "• Drag with Right Click to move the image.\n"
            "• Zoom using the mouse wheel.\n"
            "• After 4 points, a GeoTIFF will be saved automatically."
        )
        instruction_label = tk.Label(self.master, text=instructions,
                                     font=("Helvetica", 11), bg="#e8f0f2", fg="#333",
                                     justify="center")
        instruction_label.pack(padx=30, pady=(0, 40))

        # Run georeference tool
        btn_run = tk.Button(self.master, text="Start Georeferencing Tool",
                            command=self.run_georeference,
                            font=("Helvetica", 11, "bold"),
                            width=30, height=2,
                            bg="#4a90e2", fg="white",
                            activebackground="#357ABD", activeforeground="white",
                            bd=0, cursor="hand2")
        btn_run.pack()

    def run_georeference(self):
        try:
            self.master.destroy()

            # Get absolute path to georeference/app.py
            project_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(project_root, "georeference", "app.py")

            if not os.path.exists(script_path):
                raise FileNotFoundError(f"{script_path} does not exist.")

            subprocess.run([sys.executable, script_path])

            # Relaunch the window after closing the tool
            import tkinter as tk
            from gui.georeference import GeoreferenceWindow

            root = tk.Tk()
            app = GeoreferenceWindow(root)
            root.update_idletasks()
            root.deiconify()
            root.lift()
            root.focus_force()
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
