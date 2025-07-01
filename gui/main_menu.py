# gui/main_menu.py

import os
import sys
import tkinter as tk
from tkinter import messagebox
from serial.tools import list_ports
import subprocess

from gui.calibration import launch_calibration_window
from gui.monitor_selector import select_monitor
from gui.gui_components import create_header, create_main_button

class StartWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Cyclades Interactive System")
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        create_header(self.master, "Cyclades Interactive System")

        tk.Label(self.master,
                 text="An Experimental System for Real-Time Geospatial Interaction",
                 font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b").pack(pady=(0, 30))

        button_frame = tk.Frame(self.master, bg="#e8f0f2")
        button_frame.pack()

        create_main_button(button_frame, "Run Main Application", self.run_main_app).grid(row=0, column=0, padx=10, pady=10)
        create_main_button(button_frame, "Setup & Calibration", self.open_configurator).grid(row=0, column=1, padx=10, pady=10)

        tk.Button(self.master, text=" Help", font=("Helvetica", 10),
                  width=18, height=1, command=self.show_help,
                  bg="#ffffff", fg="#333", bd=1, relief="solid", cursor="hand2").pack(pady=10)

        tk.Label(self.master, text="Developed by Afroditi Kalantzi",
                 font=("Helvetica", 9, "italic"), bg="#e8f0f2", fg="#666").pack(side="bottom", pady=15)

    def is_ais_receiver_connected(self):
        ports = list_ports.comports()
        return any("AIS" in (port.description or "") or "USB" in (port.description or "") for port in ports)

    def run_main_app(self):
        def on_monitor_selected(monitor_index):
            display_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','core','interactive', 'display.py'))
            ais_receiver_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core', 'ais', 'ais_receiver.py'))

            env = os.environ.copy()
            env["SDL_VIDEO_FULLSCREEN_DISPLAY"] = str(monitor_index)

            self.decode_proc = None

            if self.is_ais_receiver_connected():
                try:
                    messagebox.showinfo("Running with AIS", "AIS module detected. Launching full system..")

                    self.decode_proc = subprocess.Popen(
                        [sys.executable, ais_receiver_script],
                        creationflags=subprocess.CREATE_NEW_CONSOLE  # This opens a new terminal
                        )

                    self.main_proc = subprocess.Popen([sys.executable, display_script], env=env)
                except Exception as e:
                    messagebox.showerror("Launch Error", f"Failed to launch with AIS:\n{e}")
                    return
            else:
                proceed = messagebox.askyesno(
                    "AIS Receiver Not Found",
                    "No AIS receiver detected.\n\nDo you want to continue without AIS?"
                )
                if not proceed:
                    return
                try:
                    messagebox.showinfo("Running without AIS", "AIS module not detected. Launching system in offline mode...")
                    self.main_proc = subprocess.Popen([sys.executable, display_script], env=env)
                except Exception as e:
                    messagebox.showerror("Launch Error", f"Failed to launch main.py:\n{e}")
                    return

            self.master.destroy()

            self.main_proc.wait()
            if self.decode_proc:
                self.decode_proc.terminate()
                self.decode_proc.wait()            

        select_monitor(on_monitor_selected)

    def open_configurator(self):
        self.master.destroy()
        launch_calibration_window()

    def show_help(self):
        help_text = (
            "Welcome to the Cyclades Interactive System!\n\n"
            "Use 'Setup & Calibration' to:\n"
            "• Configure your database\n"
            "• Calibrate the projector and camera\n"
            "• Georeference a custom map image\n\n"
            "Use 'Run Main Application' to:\n"
            "• Display live ship positions on the 3D maquette\n"
            "• Interact using hand gestures via webcam\n"
            "• View AIS data in real time (if receiver is connected)\n\n"
            "Need help? Contact Afroditi Kalantzi."
        )
        messagebox.showinfo("Help", help_text)

def launch_start_window():
    root = tk.Tk()
    app = StartWindow(root)
    root.mainloop()
