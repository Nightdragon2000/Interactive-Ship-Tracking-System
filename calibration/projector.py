import os
import sys

# Set SDL display environment early for Pygame
monitor_index = os.environ.get("SDL_VIDEO_FULLSCREEN_DISPLAY", "0")
print(f"[DEBUG] SDL_VIDEO_FULLSCREEN_DISPLAY (before pygame import): {monitor_index}")
os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = monitor_index  # Always set explicitly before pygame

import pygame
import rasterio
import numpy as np
import json
from tkinter import filedialog, messagebox

import ctypes
from ctypes import wintypes

# ─── SAFER MONITOR WINDOW PLACEMENT (Windows only) ──────────────────────────────
def move_window_to_monitor(window, monitor_index):
    """Moves the Pygame window to the correct monitor using real screen coordinates (Windows only)."""
    hwnd = pygame.display.get_wm_info()['window']

    user32 = ctypes.windll.user32
    MONITORINFOF_PRIMARY = 1

    monitor_enum_proc = ctypes.WINFUNCTYPE(
        ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), ctypes.c_double
    )

    monitors = []

    def _monitor_enum(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return 1

    user32.EnumDisplayMonitors(0, 0, monitor_enum_proc(_monitor_enum), 0)

    if monitor_index >= len(monitors):
        monitor_index = 0  # fallback to primary

    left, top, width, height = monitors[monitor_index]
    user32.MoveWindow(hwnd, left, top, width, height, True)
    print(f"[DEBUG] Moved window to monitor {monitor_index} at ({left}, {top}, {width}, {height})")

# ─── COORDINATE SAVE ────────────────────────────────────────────────────────────
def save_coordinates(projector_coordinates=None):
    path = os.path.join(os.path.dirname(__file__), 'coordinates.json')
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Warning: JSON file is empty or corrupted.")

    if projector_coordinates:
        data['projector'] = projector_coordinates

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    print("Projector coordinates saved.")

# ─── MAIN CALIBRATION FUNCTION ──────────────────────────────────────────────────
def projector_calibration():
    georef_path = filedialog.askopenfilename(title="Select GeoTIFF Image",
                                             filetypes=[("GeoTIFF files", "*.tif")])
    if not georef_path or not os.path.exists(georef_path):
        messagebox.showerror("Error", "No image selected.")
        return

    try:
        with rasterio.open(georef_path) as src:
            image_data = src.read()
            print(f"Loaded image: {georef_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open image: {e}")
        return

    if image_data.shape[0] < 3:
        band = image_data[0]
        if band.dtype != np.uint8:
            band = ((band - band.min()) / (band.max() - band.min()) * 255).astype(np.uint8)
        image_data = np.stack([band]*3, axis=0)

    image_data = np.transpose(image_data[:3], (1, 2, 0)).astype(np.uint8)
    image_data = np.rot90(image_data, 1)
    image_data = np.flipud(image_data)

    pygame.init()
    pygame.font.init()

    num_displays = pygame.display.get_num_displays()
    print(f"[DEBUG] Number of displays available: {num_displays}")

    desktops = pygame.display.get_desktop_sizes()
    print(f"[DEBUG] Desktop sizes per display: {desktops}")

    monitor_index = int(os.environ.get("SDL_VIDEO_FULLSCREEN_DISPLAY", 0))
    screen_width, screen_height = desktops[monitor_index]
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)

    move_window_to_monitor(screen, monitor_index)

    pygame.display.set_caption("Projector Calibration")

    try:
        img_original = pygame.surfarray.make_surface(image_data)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot create display surface: {e}")
        pygame.quit()
        return

    img_surface = img_original.copy()
    img_rect = img_surface.get_rect(center=screen.get_rect().center)

    scale = 1.0
    dragging = False
    offset_x = offset_y = 0

    def scale_image(surface, factor):
        new_size = (int(surface.get_width() * factor), int(surface.get_height() * factor))
        return pygame.transform.smoothscale(surface, new_size)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    save_coordinates(projector_coordinates={
                        "tl_corner": img_rect.topleft,
                        "br_corner": img_rect.bottomright
                    })
                    messagebox.showinfo("Success", "Projector calibration saved.")
                    running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and img_rect.collidepoint(event.pos):
                    dragging = True
                    offset_x = img_rect.x - event.pos[0]
                    offset_y = img_rect.y - event.pos[1]
                elif event.button == 4:
                    scale = min(scale * 1.1, 5.0)
                    center = img_rect.center
                    img_surface = scale_image(img_original, scale)
                    img_rect = img_surface.get_rect(center=center)
                elif event.button == 5:
                    scale = max(scale * 0.9, 0.1)
                    center = img_rect.center
                    img_surface = scale_image(img_original, scale)
                    img_rect = img_surface.get_rect(center=center)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    img_rect.x = event.pos[0] + offset_x
                    img_rect.y = event.pos[1] + offset_y

        screen.fill((0, 0, 0))
        screen.blit(img_surface, img_rect)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    projector_calibration()
