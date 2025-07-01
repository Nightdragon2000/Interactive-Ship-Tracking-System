# ------- Imports -------
import os
import sys
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime, timedelta

import pygame
import rasterio
import numpy as np
import cv2
import mediapipe as mp

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from core.database.db_setup import load_credentials


BASE_DIR = os.path.dirname(os.path.abspath(__file__))            # core/interactive/
CORE_DIR = os.path.dirname(BASE_DIR)                             # core/                    

COORDINATES_PATH = os.path.join(CORE_DIR, "calibration", "coordinates.json")
IMAGE_PATH = os.path.join(PROJECT_ROOT, "images", "georeferenced", "georeferenced_map.tif")
TABLE_NAME = "ships"

# ------- Load Configuration -------
with open(COORDINATES_PATH, 'r') as f:
    coordinates = json.load(f)

camera_top_left = coordinates["camera"]["tl_corner"]
camera_bottom_right = coordinates["camera"]["br_corner"]
projector_top_left = coordinates["projector"]["tl_corner"]
projector_bottom_right = coordinates["projector"]["br_corner"]

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

# ------- Load Georeferenced Image -------
with rasterio.open(IMAGE_PATH) as src:
    image_data = src.read()
    transform = src.transform
    src_width, src_height = src.width, src.height

if image_data.shape[0] > 3:
    image_data = image_data[:3]
elif image_data.shape[0] == 1:
    image_data = np.repeat(image_data, 3, axis=0)

image_data = np.transpose(image_data, (1, 2, 0))
image_data = np.clip(image_data, 0, 255).astype(np.uint8)
image_data = np.flipud(image_data)
image_data = np.rot90(image_data, 3)

# ------- Move Window to Specific Monitor -------
def move_window_to_monitor(window, monitor_index):
    hwnd = pygame.display.get_wm_info()['window']
    user32 = ctypes.windll.user32

    def _monitor_enum(hMonitor, hdcMonitor, lprcMonitor, dwData):
        r = lprcMonitor.contents
        monitors.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
        return 1

    monitors = []
    proc = ctypes.WINFUNCTYPE(
        ctypes.c_int, wintypes.HMONITOR, wintypes.HDC,
        ctypes.POINTER(wintypes.RECT), ctypes.c_double
    )(_monitor_enum)
    user32.EnumDisplayMonitors(0, 0, proc, 0)

    if monitor_index >= len(monitors):
        monitor_index = 0

    left, top, width, height = monitors[monitor_index]
    user32.MoveWindow(hwnd, left, top, width, height, True)

# ------- Setup Display -------
os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = os.environ.get("SDL_VIDEO_FULLSCREEN_DISPLAY", "0")
pygame.init()
monitor_index = int(os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"])
screen_width, screen_height = pygame.display.get_desktop_sizes()[monitor_index]
screen = pygame.display.set_mode((screen_width, screen_height), pygame.NOFRAME)
move_window_to_monitor(screen, monitor_index)
pygame.display.set_caption("Cyclades Interactive")

image_surface = pygame.surfarray.make_surface(image_data)
image_surface = pygame.transform.scale(image_surface, (image_width, image_height))
image_rect = image_surface.get_rect(topleft=(image_x, image_y))

cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# ------- Connect to Database -------
credentials = load_credentials()
engine = credentials.pop("engine")

if engine == "postgresql":
    import psycopg2
    conn = psycopg2.connect(**credentials)
elif engine == "mysql":
    import mysql.connector
    conn = mysql.connector.connect(**credentials)
else:
    raise ValueError(f"Unsupported database engine: {engine}")

cursor = conn.cursor()

# ------- Utility Functions -------
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
    return [
        (mmsi, geo_to_pixel(lat, lon, transform), image_path, name, destination, eta, nav_status)
        for mmsi, lat, lon, image_path, name, destination, eta, nav_status in ship_positions
    ]

def is_near_ship(ship_pos, x, y, threshold=20):
    ship_x, ship_y = ship_pos
    return np.hypot(ship_x - x, ship_y - y) <= threshold

def is_index_touching_thumb(hand_landmarks):
    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    distance = np.sqrt((index_tip.x - thumb_tip.x)**2 + (index_tip.y - thumb_tip.y)**2 + (index_tip.z - thumb_tip.z)**2)
    return distance < 0.075

def refresh_ship_positions():
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=10)
    return fetch_ship_positions(start_time, end_time)

# Ship tracking state
near_ship_start_time = None
current_ship_mmsi = None
selected_ship_mmsi = None
selected_ship_start_time = None

font_main = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 18)
screen_refresh_event = pygame.USEREVENT
pygame.time.set_timer(screen_refresh_event, 60000)

# ------- Main Application Loop -------
running = True
ship_positions = refresh_ship_positions()

while running and cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(frame_rgb)
    
    cv2.polylines(frame, [polygon_points_array], isClosed=True, color=(255, 0, 0), thickness=2)

    # Update ship map
    map_surface = pygame.surfarray.make_surface(image_data)
    map_surface = pygame.transform.scale(map_surface, (image_width, image_height))

    for mmsi, (x, y), img_path, name, dest, eta, nav in ship_positions:
        color = (255, 255, 0) if selected_ship_mmsi == mmsi else (255, 0, 0)
        pygame.draw.circle(map_surface, color, (x, y), 5)

    # Hand detection and interaction
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            h, w, _ = frame.shape
            index_x = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x * w)
            index_y = int(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y * h)

            if cv2.pointPolygonTest(polygon_points_array, (index_x, index_y), False) >= 0:
                cv2.circle(frame, (index_x, index_y), 10, (0, 255, 0), -1)
                map_x = int((index_x - camera_top_left[0]) / (camera_bottom_right[0] - camera_top_left[0]) * image_width)
                map_y = int((index_y - camera_top_left[1]) / (camera_bottom_right[1] - camera_top_left[1]) * image_height)
                pygame.draw.circle(map_surface, (0, 255, 0), (map_x, map_y), 10)

                for mmsi, (sx, sy), img_path, name, dest, eta, nav in ship_positions:
                    if is_near_ship((sx, sy), map_x, map_y):
                        if near_ship_start_time is None:
                            near_ship_start_time = time.time()
                            current_ship_mmsi = mmsi
                        elif current_ship_mmsi == mmsi and time.time() - near_ship_start_time >= 2:
                            selected_ship_mmsi = mmsi
                            selected_ship_start_time = time.time()
                        break
                else:
                    near_ship_start_time = None
                    current_ship_mmsi = None

            if selected_ship_mmsi and is_index_touching_thumb(hand_landmarks):
                selected_ship_mmsi = None
                selected_ship_start_time = None

    # Display overlays
    cv2.imshow("Webcam Feed", frame)
    screen.fill((0, 0, 0))
    screen.blit(map_surface, image_rect)

    if selected_ship_mmsi:
        for mmsi, _, img_path, name, dest, eta, nav in ship_positions:
            if mmsi == selected_ship_mmsi:
                info_x = image_x + image_width - 210
                info_y = image_y + 10
                pygame.draw.rect(screen, (255, 255, 255), (info_x, info_y, 200, 300))

                title_font = pygame.font.SysFont("Arial", 16, bold=True)
                text_font = pygame.font.SysFont("Arial", 10)

                screen.blit(title_font.render(name, True, (0, 0, 0)), (info_x + 10, info_y + 10))

                try:
                    if os.path.exists(img_path):
                        ship_img = pygame.image.load(img_path)
                        ship_img = pygame.transform.scale(ship_img, (180, 100))
                        screen.blit(ship_img, (info_x + 10, info_y + 40))
                    else:
                        pygame.draw.rect(screen, (200, 200, 200), (info_x + 10, info_y + 40, 180, 100))
                        screen.blit(text_font.render("No image", True, (0, 0, 0)), (info_x + 70, info_y + 80))
                except Exception:
                    pass

                if nav == "Moored":
                    screen.blit(text_font.render("Moored / Στάσιμο", True, (0, 0, 0)), (info_x + 10, info_y + 150))
                else:
                    screen.blit(text_font.render("Destination:", True, (0, 0, 0)), (info_x + 10, info_y + 150))
                    screen.blit(text_font.render(dest, True, (0, 0, 0)), (info_x + 10, info_y + 170))
                    screen.blit(text_font.render("ETA:", True, (0, 0, 0)), (info_x + 10, info_y + 190))
                    screen.blit(text_font.render(eta, True, (0, 0, 0)), (info_x + 10, info_y + 210))

                if time.time() - selected_ship_start_time >= 15:
                    selected_ship_mmsi = None
                    selected_ship_start_time = None
                break

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        elif event.type == screen_refresh_event:
            ship_positions = refresh_ship_positions()

    if cv2.waitKey(1) & 0xFF == ord('q'):
        running = False

# Show Closing Message
screen.fill((0, 0, 0))
closing_font = pygame.font.SysFont("Arial", 48, bold=True)
text_surface = closing_font.render("App is Closing .....", True, (255, 255, 255))
text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
screen.blit(text_surface, text_rect)
pygame.display.flip()
time.sleep(2)

# Shutdown 
cap.release()
pygame.quit()
cv2.destroyAllWindows()
cursor.close()
conn.close()
sys.exit(0)
