import tkinter as tk
from tkinter import messagebox

# --- Start Window ---
class StartWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Cyclades Interactive System")
        self.master.geometry("600x400")
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(self.master, text="Cyclades Interactive System",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(30, 5))

        subtitle = tk.Label(self.master,
                            text="An Experimental System for Real-Time Geospatial Interaction",
                            font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b")
        subtitle.pack(pady=(0, 30))

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

        btn_main_app = tk.Button(button_frame, text="Run Main Application", command=self.run_main_app, **btn_style)
        btn_main_app.grid(row=0, column=0, padx=10, pady=10)

        btn_calibration = tk.Button(button_frame, text="Setup & Calibration", command=self.open_calibration, **btn_style)
        btn_calibration.grid(row=0, column=1, padx=10, pady=10)

        btn_help = tk.Button(self.master, text="❓ Help", font=("Helvetica", 10),
                             width=18, height=1, command=self.show_help,
                             bg="#ffffff", fg="#333", bd=1, relief="solid", cursor="hand2")
        btn_help.pack(pady=10)

        footer = tk.Label(self.master, text="Developed by Afroditi Kalantzi",
                          font=("Helvetica", 9, "italic"), bg="#e8f0f2", fg="#666")
        footer.pack(side="bottom", pady=15)

    def run_main_app(self):
        messagebox.showinfo("Main App", "This will launch the main system.\n(Insert your logic here)")

    def open_calibration(self):
        self.master.destroy()
        launch_calibration_window()

    def show_help(self):
        help_text = (
            "Welcome to the Cyclades Interactive System!\n\n"
            "🛠️ Use 'Setup & Calibration' to:\n"
            "• Calibrate your projector and camera\n"
            "• Georeference your image\n"
            "• Configure the database\n\n"
            "▶ Use 'Run Main Application' to:\n"
            "• Project geospatial data onto the physical model\n"
            "• Interact via webcam\n"
            "• View real-time AIS ship data\n\n"
            "For more info, check the documentation or contact Afroditi Kalantzi."
        )
        messagebox.showinfo("Help", help_text)


# --- Calibration Window ---
class CalibrationWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Setup & Calibration")
        self.master.geometry("600x520")  # Increased height to fit content
        self.master.resizable(False, False)
        self.master.configure(bg="#e8f0f2")

        self.create_widgets()

    def create_widgets(self):
        # Simple arrow back button (top-left)
        btn_back = tk.Button(self.master, text="← Go Back", command=self.back_to_main,
                             font=("Helvetica", 14), bg="#e8f0f2", fg="#1f3b4d",
                             bd=0, highlightthickness=0,
                             activebackground="#e8f0f2", activeforeground="#1f3b4d",
                             cursor="hand2")
        btn_back.place(x=10, y=10)

        title = tk.Label(self.master, text="Setup & Calibration",
                         font=("Helvetica", 20, "bold"), bg="#e8f0f2", fg="#1f3b4d")
        title.pack(pady=(50, 10))  # Moved down to avoid overlap with back button

        subtitle = tk.Label(self.master,
                            text="Choose an option below to configure the system",
                            font=("Helvetica", 11), bg="#e8f0f2", fg="#3b3b3b")
        subtitle.pack(pady=(0, 20))

        button_frame = tk.Frame(self.master, bg="#e8f0f2")
        button_frame.pack()

        btn_style = {
            "font": ("Helvetica", 11, "bold"),
            "width": 25,
            "height": 2,
            "bg": "#4a90e2",
            "fg": "white",
            "activebackground": "#357ABD",
            "activeforeground": "white",
            "bd": 0,
            "cursor": "hand2"
        }

        tk.Button(button_frame, text="Setup Database", command=self.setup_database, **btn_style).pack(pady=7)
        tk.Button(button_frame, text="Camera Calibration", command=self.camera_calibration, **btn_style).pack(pady=7)
        tk.Button(button_frame, text="Projector Calibration", command=self.projector_calibration, **btn_style).pack(pady=7)
        tk.Button(button_frame, text="Georeference Image", command=self.georeference_image, **btn_style).pack(pady=7)
        tk.Button(button_frame, text="Full Setup Wizard", command=self.full_setup, **btn_style).pack(pady=7)

    # Placeholder methods
    def setup_database(self):
        messagebox.showinfo("Database Setup", "Launch database setup (insert logic here).")

    def camera_calibration(self):
        messagebox.showinfo("Camera Calibration", "Launch camera calibration (insert logic here).")

    def projector_calibration(self):
        messagebox.showinfo("Projector Calibration", "Launch projector calibration (insert logic here).")

    def georeference_image(self):
        messagebox.showinfo("Georeference Image", "Launch georeferencing tool (insert logic here).")

    def full_setup(self):
        messagebox.showinfo("Full Setup Wizard", "Launch full system setup (insert logic here).")

    def back_to_main(self):
        self.master.destroy()
        launch_start_window()


# --- Functions to Launch Windows ---
def launch_start_window():
    root = tk.Tk()
    app = StartWindow(root)
    root.mainloop()


def launch_calibration_window():
    root = tk.Tk()
    app = CalibrationWindow(root)
    root.mainloop()


# --- Start the application ---
if __name__ == "__main__":
    launch_start_window()




# # main.py

# import tkinter as tk
# from tkinter import messagebox

# # Import calibration tools
# from calibration.camera import camera_calibration
# from calibration.projector import projector_calibration

# # Import the georeference GUI class
# from georeference.app import GeoreferencingApp

# def create_main_window():
#     root = tk.Tk()
#     root.title("Calibration & Georeference Tool")
#     root.geometry("300x250")

#     def run_tool(func):
#         try:
#             func()
#         except Exception as e:
#             messagebox.showerror("Error", f"Something went wrong:\n{e}")

#     # Buttons
#     tk.Button(root, text="Camera Calibration", command=lambda: run_tool(camera_calibration)).pack(pady=10)
#     tk.Button(root, text="Projector Calibration", command=lambda: run_tool(projector_calibration)).pack(pady=10)
#     tk.Button(root, text="Georeference Image", command=lambda: GeoreferencingApp().root.mainloop()).pack(pady=10)
#     tk.Button(root, text="Exit", command=root.destroy).pack(pady=10)

#     root.mainloop()

# if __name__ == "__main__":
#     create_main_window()
