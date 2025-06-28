import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import rasterio
from rasterio.transform import rowcol
import os

# Real-world coordinates (latitude, longitude)
target_lat = 37.401150
target_lon = 24.972372

# Path to georeferenced image (adjust if needed)
geotiff_path = os.path.join( "images", "georeferenced", "georeferenced_map.tif")

# Open georeferenced image using rasterio
with rasterio.open(geotiff_path) as src:
    transform = src.transform
    image_data = src.read()
    image_data = image_data[:3]  # use RGB bands only

    # Convert to height x width x channels format
    image_np = image_data.transpose(1, 2, 0)

    # Convert coordinates (lat, lon) → pixel (row, col)
    row, col = rowcol(transform, target_lon, target_lat)

# Convert numpy image to Pillow
img_pil = Image.fromarray(image_np)

# Draw a red dot at the target pixel
draw = ImageDraw.Draw(img_pil)
dot_radius = 5
draw.ellipse(
    [(col - dot_radius, row - dot_radius), (col + dot_radius, row + dot_radius)],
    fill="red",
    outline="black"
)

# Display in Tkinter
root = tk.Tk()
root.title("Georeferenced Dot Viewer")

tk_img = ImageTk.PhotoImage(img_pil)
canvas = tk.Canvas(root, width=tk_img.width(), height=tk_img.height())
canvas.pack()
canvas.create_image(0, 0, image=tk_img, anchor="nw")

root.mainloop()
