import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import rasterio
from rasterio.control import GroundControlPoint
from rasterio.crs import CRS
from rasterio.transform import from_gcps
import os
import numpy as np

class GeoreferencingApp:
    def __init__(self):
        self.root = tk.Toplevel()
        self.root.title("Georeference Tool")

        self.canvas = tk.Canvas(self.root, bg='lightgray')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.image_path = None
        self.raw_image_array = None
        self.tk_image = None
        self.image_on_canvas = None
        self.clicked_points = []

        self.canvas.bind("<Button-1>", self.handle_click)
        self.root.after(100, self.open_image)

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[
                ("Image files", "*.tif *.tiff *.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*")
            ]
        )
        if not path:
            self.root.destroy()
            return

        try:
            self.image_path = path
            with rasterio.open(path) as src:
                img = src.read()
                self.meta = src.meta.copy()

                if img.shape[0] == 1:
                    img = np.repeat(img, 3, axis=0)  # convert grayscale to RGB

                img = np.transpose(img[:3], (1, 2, 0))  # rasterio: (bands, rows, cols) → (rows, cols, bands)

                self.raw_image_array = img.astype(np.uint8)

            img_pil = Image.fromarray(self.raw_image_array)
            self.tk_image = ImageTk.PhotoImage(img_pil)

            self.image_on_canvas = self.canvas.create_image(0, 0, image=self.tk_image, anchor='nw')
            self.canvas.config(width=img_pil.width, height=img_pil.height)
            self.canvas.image = self.tk_image  # preserve reference

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")
            self.root.destroy()

    def handle_click(self, event):
        px, py = event.x, event.y

        coord_input = simpledialog.askstring(
            "Real Coordinates",
            f"Pixel: ({px},{py})\nEnter real-world coordinates (lat, lon):"
        )
        if not coord_input:
            return

        try:
            lat, lon = map(float, coord_input.split(','))
            self.clicked_points.append(((px, py), (lat, lon)))

            self.canvas.create_oval(
                px - 3, py - 3, px + 3, py + 3,
                fill='red', outline='red'
            )

            if len(self.clicked_points) == 4:
                self.georeference_image()

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter coordinates as: lat, lon")

    def georeference_image(self):
        image_coords = [pt[0] for pt in self.clicked_points]
        real_coords = [pt[1] for pt in self.clicked_points]

        gcps = []
        for (px, py), (lat, lon) in zip(image_coords, real_coords):
            # row = y (height), col = x (width)
            gcps.append(GroundControlPoint(row=py, col=px, x=lon, y=lat))

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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save georeferenced image:\n{e}")

        self.root.destroy()
