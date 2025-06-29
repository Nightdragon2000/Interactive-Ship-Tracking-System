import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.transform import from_gcps
import os
import numpy as np
import warnings
from rasterio.errors import NotGeoreferencedWarning

warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

class GeoreferencingApp:
    def __init__(self, master=None):
        if master:
            self.parent = master
        else:
            self.parent = None

        self.root = tk.Toplevel()
        self.root.title("Georeference Tool")
        self.root.geometry("1400x900")
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', 1)
        self.root.after_idle(self.root.attributes, '-topmost', 0)

        self.canvas = tk.Canvas(self.root, bg='lightgray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.raw_image_array = None
        self.tk_image = None
        self.image_on_canvas = None
        self.meta = None

        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.clicked_points = []  # [(img_x, img_y), (lat, lon), dot_id]
        self.counter_text_id = None

        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<ButtonPress-3>", self.start_drag)
        self.canvas.bind("<B3-Motion>", self.perform_drag)
        self.canvas.bind("<MouseWheel>", self.handle_zoom)

        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)
        self.root.after(100, self.open_image)

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[("Image files", "*.tif *.tiff *.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        )
        if not path:
            self.root.destroy()
            if self.parent:
                self.parent.deiconify()
            return

        try:
            with rasterio.open(path) as src:
                img = src.read()
                self.meta = src.meta.copy()

                if img.shape[0] == 1:
                    img = np.repeat(img, 3, axis=0)

                img = np.transpose(img[:3], (1, 2, 0))
                self.raw_image_array = img.astype(np.uint8)

            self.display_image()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.root.destroy()
            if self.parent:
                self.parent.deiconify()

    def display_image(self):
        img_pil = Image.fromarray(self.raw_image_array)
        w, h = img_pil.size
        img_scaled = img_pil.resize((int(w * self.scale), int(h * self.scale)), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(img_scaled)

        if self.image_on_canvas:
            self.canvas.delete(self.image_on_canvas)

        self.image_on_canvas = self.canvas.create_image(self.offset_x, self.offset_y, image=self.tk_image, anchor='nw')
        self.canvas.image = self.tk_image

        self.redraw_points()
        self.update_counter()

    def handle_click(self, event):
        canvas_x, canvas_y = event.x, event.y
        img_x = int((canvas_x - self.offset_x) / self.scale)
        img_y = int((canvas_y - self.offset_y) / self.scale)

        for i, (pixel, _, dot_id) in enumerate(self.clicked_points):
            dot_canvas_x = self.offset_x + pixel[0] * self.scale
            dot_canvas_y = self.offset_y + pixel[1] * self.scale
            if abs(canvas_x - dot_canvas_x) < 6 and abs(canvas_y - dot_canvas_y) < 6:
                self.edit_or_delete_point(i)
                return

        dot_id = self.canvas.create_oval(canvas_x - 3, canvas_y - 3, canvas_x + 3, canvas_y + 3, fill='red', outline='red')

        coord_input = simpledialog.askstring("Real Coordinates", f"Pixel: ({img_x},{img_y})\nEnter (lat, lon):", parent=self.root)
        if not coord_input:
            self.canvas.delete(dot_id)
            return

        try:
            if "," not in coord_input:
                raise ValueError("Missing comma")
            lat, lon = map(float, coord_input.strip().split(','))
            self.clicked_points.append(((img_x, img_y), (lat, lon), dot_id))
            self.update_counter()
            if len(self.clicked_points) == 4:
                self.georeference_image()
        except:
            self.canvas.delete(dot_id)
            messagebox.showerror("Invalid Input", "Please enter coordinates as: number,number")

    def edit_or_delete_point(self, index):
        (px, py), (lat, lon), dot_id = self.clicked_points[index]

        popup = tk.Toplevel(self.root)
        popup.title("Edit/Delete Point")
        popup.geometry("300x120")
        popup.transient(self.root)
        popup.grab_set()

        self.root.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - 120) // 2
        popup.geometry(f"+{x}+{y}")
        popup.lift()
        popup.focus_force()

        tk.Label(popup, text=f"Pixel: ({px},{py})\nReal: ({lat}, {lon})\nChoose action:").pack(pady=10)

        def do_edit():
            popup.destroy()
            new_input = simpledialog.askstring("Edit Coordinates", f"Current: {lat},{lon}\nNew (lat, lon):", parent=self.root)
            if new_input:
                try:
                    if "," not in new_input:
                        raise ValueError("Missing comma")
                    new_lat, new_lon = map(float, new_input.strip().split(','))
                    self.clicked_points[index] = ((px, py), (new_lat, new_lon), dot_id)
                    self.update_counter()
                except:
                    messagebox.showerror("Invalid Input", "Please enter coordinates as: number,number")

        def do_delete():
            popup.destroy()
            self.canvas.delete(dot_id)
            self.clicked_points.pop(index)
            self.update_counter()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Edit", width=10, command=do_edit).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Delete", width=10, command=do_delete).grid(row=0, column=1, padx=10)

    def redraw_points(self):
        for i, ((img_x, img_y), coords, old_dot_id) in enumerate(self.clicked_points):
            self.canvas.delete(old_dot_id)
            x = self.offset_x + img_x * self.scale
            y = self.offset_y + img_y * self.scale
            new_dot_id = self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill='red', outline='red')
            self.clicked_points[i] = ((img_x, img_y), coords, new_dot_id)

    def update_counter(self):
        count = len(self.clicked_points)
        if self.tk_image:
            x = self.offset_x + self.tk_image.width() - 10
            y = self.offset_y + 10
            if self.counter_text_id:
                self.canvas.delete(self.counter_text_id)
            self.counter_text_id = self.canvas.create_text(x, y, anchor='ne', text=f"Points: {count}/4", fill='black', font=('Arial', 14, 'bold'))

    def start_drag(self, event):
        self.last_drag_x = event.x
        self.last_drag_y = event.y

    def perform_drag(self, event):
        dx = event.x - self.last_drag_x
        dy = event.y - self.last_drag_y
        self.offset_x += dx
        self.offset_y += dy
        self.last_drag_x = event.x
        self.last_drag_y = event.y
        self.display_image()

    def handle_zoom(self, event):
        self.scale *= 1.1 if event.delta > 0 else 0.9
        self.display_image()

    def georeference_image(self):
        gcps = [
            GroundControlPoint(row=py, col=px, x=lon, y=lat)
            for (px, py), (lat, lon), _ in self.clicked_points
        ]

        output_dir = os.path.join(os.path.dirname(__file__), '..', 'images', 'georeferenced')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'georeferenced_map.tif')

        try:
            self.meta.update({
                'transform': from_gcps(gcps),
                'crs': CRS.from_string('WGS84'),
                'count': 3
            })

            with rasterio.open(output_path, 'w', **self.meta) as dst:
                for i in range(3):
                    dst.write(self.raw_image_array[:, :, i], i + 1)

            messagebox.showinfo("Success", f"Georeferenced image saved at:\n{output_path}")
            self.root.destroy()
            if self.parent:
                self.parent.deiconify()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save georeferenced image:\n{e}")

    def confirm_exit(self):
        if len(self.clicked_points) < 4:
            if not messagebox.askyesno("Exit Confirmation", "You haven't selected all 4 points.\nExit anyway?"):
                return
        self.root.destroy()
        if self.parent:
            self.parent.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the default root window
    app = GeoreferencingApp(master=root)
    app.root.mainloop()
