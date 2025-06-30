import os
import sys

# Set monitor index early
monitor_index = os.environ.get("SDL_VIDEO_FULLSCREEN_DISPLAY", "0")
print(f"[DEBUG] SDL_VIDEO_FULLSCREEN_DISPLAY (before pygame import): {monitor_index}")
os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = monitor_index

# Imports AFTER setting monitor
import pygame
import rasterio
import numpy as np
import cv2
import mediapipe as mp
import json
import time
from datetime import datetime, timedelta
import ctypes
from ctypes import wintypes
from database.db_setup import load_credentials
import mysql.connector

# ─── Monitor Move Function ─────────────────────────
def move_window_to_monitor(window, monitor_index):
    hwnd = pygame.display.get_wm_info()['window']
    user32 = ctypes.windll.user32
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
        monitor_index = 0
    left, top, width, height = monitors[monitor_index]
    user32.MoveWindow(hwnd, left, top, width, height, True)
    print(f"[DEBUG] Moved window to monitor {monitor_index} at ({left}, {top}, {width}, {height})")

# ─── Load Coordinates ──────────────────────────────
with open('./calibration/coordinates.json', 'r') as f:
    coordinates = json.load(f)
camera_coordinates = coordinates["camera"]
camera_top_left = camera_coordinates["tl_corner"]
camera_bottom_right = camera_coordinates["br_corner"]
projector_coordinates = coordinates["projector"]
projector_top_left = projector_coordinates["tl_corner"]
projector_bottom_right = projector_coordinates["br_corner"]

polygon_points = [
    camera_top_left,
    [camera_bottom_right[0], camera_top_left[1]],
    camera_bottom_right,
    [camera_top_left[0], camera_bottom_right[1]]
]
polygon_points_array = np.array(polygon_points, np.int32).reshape((-1, 1, 2))

image_x = projector_top_left[0]
image_y = projector_top_left[1]
image_width = projector_bottom_right[0] - projector_top_left[0]
image_height = projector_bottom_right[1] - projector_top_left[1]

# ─── Load Georeferenced Image ──────────────────────
image_path = "./images/georeferenced/georeferenced_map.tif"
with rasterio.open(image_path) as src:
    image_data = src.read()
    transform = src.transform
    src_width = src.width
    src_height = src.height

num_bands = image_data.shape[0]
if num_bands > 3:
    image_data = image_data[:3]
elif num_bands == 1:
    image_data = np.stack([image_data[0]] * 3, axis=0)

image_data = np.transpose(image_data, (1, 2, 0))
image_data = np.clip(image_data, 0, 255).astype(np.uint8)
image_data = np.flipud(image_data)
image_data = np.rot90(image_data, 3)

# ─── Init Pygame & Window ──────────────────────────
pygame.init()
desktops = pygame.display.get_desktop_sizes()
monitor_index = int(monitor_index)
screen_width, screen_height = desktops[monitor_index]
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
move_window_to_monitor(screen, monitor_index)
pygame.display.set_caption("Cyclades Interactive")

# ─── Prepare Image Surface ─────────────────────────
image_surface = pygame.surfarray.make_surface(image_data)
image_surface = pygame.transform.scale(image_surface, (image_width, image_height))
image_rect = image_surface.get_rect(topleft=(image_x, image_y))

# ─── Setup Camera & MediaPipe ──────────────────────
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# ─── Load DB Credentials ───────────────────────────
credentials = load_credentials()
engine = credentials.pop("engine")  # Remove 'engine' from the dict

if engine == "postgresql":
    import psycopg2
    conn = psycopg2.connect(**credentials)
elif engine == "mysql":
    conn = mysql.connector.connect(**credentials)
else:
    raise ValueError(f"Unsupported database engine: {engine}")


cursor = conn.cursor()
TABLE_NAME = "ships"

# ─── Ship Position Fetch ───────────────────────────
def geo_to_pixel(lat, lon, transform):
    row, col = rasterio.transform.rowcol(transform, lon, lat)
    return int(col * image_width / src_width), int(row * image_height / src_height)

def fetch_ship_positions(start_time, end_time):
    query = f"""
        SELECT s.mmsi, s.latitude, s.longitude, s.image_path, s.name, s.destination, s.eta, s.navigation_status
        FROM {TABLE_NAME} s
        INNER JOIN (
            SELECT mmsi, MAX(timestamp) AS latest_timestamp
            FROM {TABLE_NAME}
            WHERE timestamp BETWEEN %s AND %s
            GROUP BY mmsi
        ) latest ON s.mmsi = latest.mmsi AND s.timestamp = latest.latest_timestamp
        ORDER BY s.timestamp DESC;
    """
    cursor.execute(query, (start_time, end_time))
    ship_positions = cursor.fetchall()
    ship_positions = [(mmsi, geo_to_pixel(lat, lon, transform), image_path, name, destination, eta, navigation_status)
                      for mmsi, lat, lon, image_path, name, destination, eta, navigation_status in ship_positions]
    return ship_positions

def geo_to_pixel(lat, lon, transform):
    row, col = rasterio.transform.rowcol(transform, lon, lat)
    return int(col * image_width / src.width), int(row * image_height / src.height)

def refresh_ship_positions():
    global ship_positions
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=10)
    ship_positions = fetch_ship_positions(start_time, end_time)
    print(f"Refreshed ship positions: {ship_positions}")

refresh_ship_positions()

# ---------------------------- Hand Detection Functions ---------------------------- # 
def is_near_ship(ship_pos, x, y, threshold=20):
    ship_x, ship_y = ship_pos
    return np.sqrt((ship_x - x)**2 + (ship_y - y)**2) <= threshold

def is_index_touching_thumb(hand_landmarks):
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2 + (index_tip.z - thumb_tip.z)**2)
    return distance < 0.075

# ---------------------------- Main Loop ---------------------------- #
near_ship_start_time = None
current_ship_mmsi = None
selected_ship_mmsi = None
selected_ship_start_time = None

font = pygame.font.SysFont("Arial", 24)
small_font = pygame.font.SysFont("Arial", 18)

pygame.time.set_timer(pygame.USEREVENT, 60000)
running = True

while running and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)

    cv2.polylines(frame, [polygon_points_array], isClosed=True, color=(255, 0, 0), thickness=2)

    image_surface = pygame.surfarray.make_surface(image_data)
    image_surface = pygame.transform.scale(image_surface, (image_width, image_height))

    for mmsi, (pixel_x, pixel_y), image_path, name, ship_destination, ship_eta, ship_navigation_status in ship_positions:
        if selected_ship_mmsi == mmsi:
            dot_color = (255, 255, 0)  # Yellow for selected ship
        else:
            dot_color = (255, 0, 0)    # Red for others
        pygame.draw.circle(image_surface, dot_color, (pixel_x, pixel_y), 5)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            h, w, _ = frame.shape
            x = int(index_finger_tip.x * w)
            y = int(index_finger_tip.y * h)

            if cv2.pointPolygonTest(polygon_points_array, (x, y), False) >= 0:
                cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)
                map_x = int((x - camera_top_left[0]) / (camera_bottom_right[0] - camera_top_left[0]) * image_width)
                map_y = int((y - camera_top_left[1]) / (camera_bottom_right[1] - camera_top_left[1]) * image_height)
                pygame.draw.circle(image_surface, (0, 255, 0), (map_x, map_y), 10)

                for mmsi, (ship_x, ship_y), image_path, name, ship_destination, ship_eta, ship_navigation_status in ship_positions:
                    if is_near_ship((ship_x, ship_y), map_x, map_y):
                        if near_ship_start_time is None:
                            near_ship_start_time = time.time()
                            current_ship_mmsi = mmsi
                        elif current_ship_mmsi == mmsi:
                            elapsed_time = time.time() - near_ship_start_time
                            if elapsed_time >= 2:
                                selected_ship_mmsi = mmsi
                                selected_ship_start_time = time.time()
                        break
                else:
                    near_ship_start_time = None
                    current_ship_mmsi = None

            if selected_ship_mmsi and is_index_touching_thumb(hand_landmarks):
                selected_ship_mmsi = None
                selected_ship_start_time = None

    cv2.imshow('Webcam Feed', frame)
    screen.fill((0, 0, 0))
    screen.blit(image_surface, image_rect)

    if selected_ship_mmsi:
        ship_info = next((mmsi, name, image_path, ship_destination, ship_eta, ship_navigation_status)
                        for mmsi, _, image_path, name, ship_destination, ship_eta, ship_navigation_status in ship_positions
                        if mmsi == selected_ship_mmsi)
        ship_name, ship_image_path, ship_destination, ship_eta, ship_navigation_status = ship_info[1:]

        title_font = pygame.font.SysFont("Arial", 16, bold=True)
        text_font = pygame.font.SysFont("Arial", 10)

        name_text = title_font.render(ship_name, True, (0, 0, 0))
        destination_label = text_font.render('Destination/Προορισμός:', True, (0, 0, 0))
        destination_text = text_font.render(ship_destination, True, (0, 0, 0))
        eta_label = text_font.render('ETA/Εκτ. Ώρα Άφιξης:', True, (0, 0, 0))
        eta_text = text_font.render(ship_eta, True, (0, 0, 0))

        box_width, box_height = 200, 300
        box_x = image_x + image_width - box_width - 10
        box_y = image_y + 10
        pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, box_width, box_height))
        screen.blit(name_text, (box_x + 10, box_y + 10))

        # Load ship image or placeholder
        image_display_height = 0
        if os.path.exists(ship_image_path):
            try:
                ship_image = pygame.image.load(ship_image_path)
                ship_image = pygame.transform.scale(ship_image, (box_width - 20, box_height // 3))
                image_display_height = ship_image.get_height()
                screen.blit(ship_image, (box_x + 10, box_y + 40))
            except Exception as e:
                print(f"Warning: Failed to load image {ship_image_path}: {e}")
        else:
            # Draw placeholder
            placeholder_height = box_height // 3
            placeholder_rect = pygame.Rect(box_x + 10, box_y + 40, box_width - 20, placeholder_height)
            pygame.draw.rect(screen, (200, 200, 200), placeholder_rect)
            placeholder_text = text_font.render("No image", True, (80, 80, 80))
            screen.blit(placeholder_text, (placeholder_rect.centerx - placeholder_text.get_width() // 2,
                                           placeholder_rect.centery - placeholder_text.get_height() // 2))
            image_display_height = placeholder_height

        # Draw ship info
        info_y = box_y + 40 + image_display_height + 10
        if ship_navigation_status == "Moored":
            moored_text = text_font.render("Moored / Στάσιμο", True, (0, 0, 0))
            screen.blit(moored_text, (box_x + 10, info_y))
        else:
            screen.blit(destination_label, (box_x + 10, info_y))
            screen.blit(destination_text, (box_x + 10, info_y + 20))
            screen.blit(eta_label, (box_x + 10, info_y + 40))
            screen.blit(eta_text, (box_x + 10, info_y + 60))

        # Hide info after 15 seconds
        if time.time() - selected_ship_start_time >= 15:
            selected_ship_mmsi = None
            selected_ship_start_time = None

    
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == pygame.USEREVENT:
            refresh_ship_positions()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False

# ---------------------------- Display Shutdown Message ---------------------------- #
shutdown_font = pygame.font.SysFont("Arial", 48)
shutdown_text = "Shutting down..."
screen.fill((0, 0, 0))
text_surface = shutdown_font.render(shutdown_text, True, (255, 255, 255))
text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
screen.blit(text_surface, text_rect)
pygame.display.flip()
time.sleep(2)  # Display message for 2 seconds


cap.release()
pygame.quit()
cv2.destroyAllWindows()
cursor.close()
conn.close()