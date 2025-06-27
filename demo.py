import tkinter as tk
from setup import run_georeference_tool  # import the function

def run_georeference():
    run_georeference_tool()

# Create the window
root = tk.Tk()
root.title("Georeferencing App")

# Add a button
btn = tk.Button(root, text="Run Georeference", command=run_georeference)
btn.pack(padx=20, pady=20)

# Run the app
root.mainloop()