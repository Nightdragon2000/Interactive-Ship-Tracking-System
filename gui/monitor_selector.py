# gui/monitor_selector.py

import tkinter as tk
from tkinter import ttk
from gui.gui_components import create_header, create_main_button

def select_monitor(callback):
    """
    Show a popup to let user choose which monitor to use for projection.
    Calls the callback with the selected monitor index.
    """
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
    root.geometry("350x200")
    root.configure(bg="#e8f0f2")
    root.resizable(False, False)

    create_header(root, "Choose Monitor")

    monitor_var = tk.IntVar(value=0)
    options = [f"Monitor {i + 1}" for i in range(monitor_count)]

    combo = ttk.Combobox(root, values=options, state="readonly", font=("Helvetica", 11))
    combo.current(0)
    combo.pack(pady=10)

    def on_combo_change(event):
        monitor_var.set(combo.current())

    combo.bind("<<ComboboxSelected>>", on_combo_change)

    create_main_button(root, "Confirm", submit_selection).pack(pady=(10, 20))

    root.grab_set()  # Makes this window modal
