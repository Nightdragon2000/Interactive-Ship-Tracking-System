import cv2
import json
import os
from tkinter import messagebox

COORDS_FILE = os.path.join(os.path.dirname(__file__), 'coordinates.json')
RECTANGLE_TOP_LEFT = (100, 100)
RECTANGLE_BOTTOM_RIGHT = (300, 300)

dragging_corner = None
offset_x, offset_y = 0, 0
rectangle_top_left_corner = RECTANGLE_TOP_LEFT
rectangle_bottom_right_corner = RECTANGLE_BOTTOM_RIGHT


def save_coordinates(camera_coordinates=None):
    data = {}

    if os.path.exists(COORDS_FILE):
        try:
            with open(COORDS_FILE, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Error : JSON file is empty.")

    if camera_coordinates:
        data['camera'] = camera_coordinates

    with open(COORDS_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print("Camera coordinates saved.")

def select_rectangle(event, x, y, flags, param):
    global rectangle_top_left_corner, rectangle_bottom_right_corner
    global dragging_corner, offset_x, offset_y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check for resizing near corners
        if abs(rectangle_top_left_corner[0] - x) < 10 and abs(rectangle_top_left_corner[1] - y) < 10:
            dragging_corner = 'start'
        elif abs(rectangle_bottom_right_corner[0] - x) < 10 and abs(rectangle_bottom_right_corner[1] - y) < 10:
            dragging_corner = 'end'
        elif rectangle_top_left_corner[0] < x < rectangle_bottom_right_corner[0] and rectangle_top_left_corner[1] < y < rectangle_bottom_right_corner[1]:
            dragging_corner = 'move'
            offset_x = x - rectangle_top_left_corner[0]
            offset_y = y - rectangle_top_left_corner[1]
        else:
            dragging_corner = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging_corner == 'start':
            rectangle_top_left_corner = (x, y)
        elif dragging_corner == 'end':
            rectangle_bottom_right_corner = (x, y)
        elif dragging_corner == 'move':
            width = rectangle_bottom_right_corner[0] - rectangle_top_left_corner[0]
            height = rectangle_bottom_right_corner[1] - rectangle_top_left_corner[1]
            rectangle_top_left_corner = (x - offset_x, y - offset_y)
            rectangle_bottom_right_corner = (rectangle_top_left_corner[0] + width, rectangle_top_left_corner[1] + height)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging_corner = None

# ------- Main Function -------
def camera_calibration():
    global rectangle_top_left_corner, rectangle_bottom_right_corner

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No camera detected.")
        messagebox.showerror("Error", "No camera detected.")
        return

    cv2.namedWindow("Camera Calibration")
    cv2.setMouseCallback("Camera Calibration", select_rectangle)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        # Draw rectangle and corner circles
        cv2.rectangle(frame, rectangle_top_left_corner, rectangle_bottom_right_corner, (255, 0, 0), 2)
        cv2.circle(frame, rectangle_top_left_corner, 5, (0, 0, 255), -1)
        cv2.circle(frame, rectangle_bottom_right_corner, 5, (0, 0, 255), -1)

        cv2.imshow("Camera Calibration", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            tl = rectangle_top_left_corner
            br = rectangle_bottom_right_corner
            tl_corrected = (min(tl[0], br[0]), min(tl[1], br[1]))
            br_corrected = (max(tl[0], br[0]), max(tl[1], br[1]))
            camera_coordinates = {"tl_corner": tl_corrected, "br_corner": br_corrected}
            save_coordinates(camera_coordinates)
            messagebox.showinfo("Success", "Camera calibration saved.")
            break
        elif key == 27:  
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    camera_calibration()
