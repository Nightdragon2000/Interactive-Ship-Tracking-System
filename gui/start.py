import tkinter as tk
from tkinter import messagebox
from gui.calibration import launch_calibration_window


class StartWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Cyclades Interactive System")
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")
        self.create_widgets()

    def create_widgets(self):
        # Title
        title = tk.Label(self.master, text="Cyclades Interactive System",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(30, 5))

        # Subtitle
        subtitle = tk.Label(self.master,
                            text="An Experimental System for Real-Time Geospatial Interaction",
                            font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b")
        subtitle.pack(pady=(0, 30))

        # Buttons
        button_frame = tk.Frame(self.master, bg="#e8f0f2")
        button_frame.pack()

        btn_style = {
            "font": ("Helvetica", 11, "bold"),
            "width": 22,
            "height": 2,
            "bg": "#4a90e2",
            "fg": "white",
            "activebackground": "#357ABD",
            "activeforeground": "white",
            "bd": 0,
            "cursor": "hand2"
        }

        # Main App button
        tk.Button(button_frame, text="Run Main Application",
                  command=self.run_main_app, **btn_style).grid(row=0, column=0, padx=10, pady=10)

        # Configurator button
        tk.Button(button_frame, text="Open Configurator",
                  command=self.open_configurator, **btn_style).grid(row=0, column=1, padx=10, pady=10)

        # Help button
        tk.Button(self.master, text="❓ Help", font=("Helvetica", 10),
                  width=18, height=1, command=self.show_help,
                  bg="#ffffff", fg="#333", bd=1, relief="solid", cursor="hand2").pack(pady=10)

        # Footer
        footer = tk.Label(self.master, text="Developed by Afroditi Kalantzi",
                          font=("Helvetica", 9, "italic"), bg="#e8f0f2", fg="#666")
        footer.pack(side="bottom", pady=15)

    def run_main_app(self):
        messagebox.showinfo("Main App", "This will launch the main system.\n(Insert your logic here)")

    def open_configurator(self):
        self.master.destroy()
        launch_calibration_window()

    def show_help(self):
        help_text = (
            "Welcome to the Cyclades Interactive System!\n\n"
            "🛠️ Use 'Open Configurator' to:\n"
            "• Calibrate devices\n"
            "• Georeference your image\n"
            "• Configure database\n\n"
            "▶ Use 'Run Main Application' to:\n"
            "• Project data onto the physical model\n"
            "• Interact using webcam\n"
            "• View AIS data\n\n"
            "Contact Afroditi Kalantzi for support."
        )
        messagebox.showinfo("Help", help_text)


def launch_start_window():
    root = tk.Tk()
    app = StartWindow(root)
    root.mainloop()
