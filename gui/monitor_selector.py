# gui/monitor_selector.py

import tkinter as tk
from tkinter import ttk

def select_monitor(callback):
    try:
        import pygame
        pygame.init()
        monitor_count = pygame.display.get_num_displays()
        pygame.quit()
    except Exception:
        monitor_count = 1

    def submit_selection():
        selected = monitor_var.get()
        root.destroy()
        callback(selected)

    root = tk.Toplevel()
    root.title("Select Display Monitor")
    root.geometry("350x180")
    root.configure(bg="#e8f0f2")
    root.resizable(False, False)

    title = tk.Label(root, text="Choose Monitor for Projection",
                     font=("Helvetica", 14, "bold"), bg="#e8f0f2", fg="#1f3b4d")
    title.pack(pady=(20, 10))

    monitor_var = tk.IntVar(value=0)

    options = [f"Monitor {i + 1}" for i in range(monitor_count)]
    combo = ttk.Combobox(root, values=options, state="readonly", font=("Helvetica", 11))
    combo.current(0)
    combo.pack(pady=10)

    def on_combo_change(event):
        monitor_var.set(combo.current())

    combo.bind("<<ComboboxSelected>>", on_combo_change)

    btn = tk.Button(root, text="Confirm",
                    font=("Helvetica", 11), bg="#4a90e2", fg="white",
                    activebackground="#357ABD", activeforeground="white",
                    command=submit_selection)
    btn.pack(pady=(10, 20))

    root.grab_set()  # Make this window modal
