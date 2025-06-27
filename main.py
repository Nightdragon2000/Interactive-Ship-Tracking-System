import tkinter as tk
from tkinter import messagebox
# Import functions from setup.py
import setup # Import the whole module

# Function to create the initial selection window
def create_initial_window():
    root = tk.Tk()
    root.title("Calibration and Setup Tool")
    root.geometry("300x200") # Adjusted size for better layout

    # Function to handle button clicks and potential errors
    def run_tool(tool_function):
        try:
            tool_function()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    # --- Button 1: Setup Database ---
    # Changed text and command
    btn_db_setup = tk.Button(root, text="Setup Database", command=lambda: setup.database_connection(root)) # Pass root as parent
    btn_db_setup.pack(pady=10)

    # --- New Button: Image Georeference ---
    # Wrapped in a function to ensure proper error handling
    def launch_georeference_tool():
        try:
            # Ensure Tkinter is in a clean state before launching
            root.update()
            setup.run_georeference_tool()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred launching the georeference tool: {e}")
            
    btn_georef = tk.Button(root, text="Image Georeference", command=launch_georeference_tool)
    btn_georef.pack(pady=10)

    # --- Button 2: Camera Calibration ---
    btn_camera_calib = tk.Button(root, text="Camera Calibration", command=lambda: run_tool(setup.camera_calibration))
    btn_camera_calib.pack(pady=10)

    # --- Button 3: Projector Calibration ---
    btn_projector_calib = tk.Button(root, text="Projector Calibration", command=lambda: run_tool(setup.projector_calibration))
    btn_projector_calib.pack(pady=10)


    root.mainloop()

# Main execution block
if __name__ == "__main__":
    create_initial_window()