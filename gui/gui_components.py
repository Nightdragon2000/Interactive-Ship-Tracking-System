import tkinter as tk

# ------- Back Button -------
def create_back_button(parent, command):
    return tk.Button(parent, text="← Go Back", command=command,
                     font=("Helvetica", 14), bg="#e8f0f2", fg="#1f3b4d",
                     bd=0, highlightthickness=0,
                     activebackground="#e8f0f2", activeforeground="#1f3b4d",
                     cursor="hand2")

# ------- Main Action Button -------
def create_main_button(parent, text, command):
    return tk.Button(parent, text=text, command=command,
                     font=("Helvetica", 11, "bold"),
                     width=30, height=2,
                     bg="#4a90e2", fg="white",
                     activebackground="#357ABD", activeforeground="white",
                     bd=0, cursor="hand2")

# ------- Header -------
def create_header(parent, title):
    tk.Label(parent, text=title,
             font=("Helvetica", 20, "bold"),
             bg="#e8f0f2", fg="#1f3b4d").pack(pady=(50, 10))

# ------- Instruction Text -------
def create_instructions(parent, text):
    tk.Label(parent, text=text,
             font=("Helvetica", 11),
             bg="#e8f0f2", fg="#333",
             justify="center").pack(padx=30, pady=(0, 40))
