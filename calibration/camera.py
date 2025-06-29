import cv2
from tkinter import messagebox
import json
import os

# Default rectangle corners
rectangle_top_left_corner = (100, 100)
rectangle_bottom_right_corner = (300, 300)
dragging_corner = None
offset_x, offset_y = 0, 0

# Save camera or projector coordinates to the JSON file
def save_coordinates(camera_coordinates=None):
    path = os.path.join(os.path.dirname(__file__), 'coordinates.json')
    data = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print("Warning: JSON file is empty or corrupted.")

    if camera_coordinates:
        data['camera'] = camera_coordinates

    with open(path, 'w') as f:
        json.dump(data, f, indent=4)
    print("Camera coordinates saved.")

# Mouse callback function to move or resize rectangle
def select_rectangle(event, x, y, flags, param):
    global rectangle_top_left_corner, rectangle_bottom_right_corner, dragging_corner, offset_x, offset_y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Click near corners = resize, click inside = move
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

def camera_calibration():
    global rectangle_top_left_corner, rectangle_bottom_right_corner

    cap = cv2.VideoCapture(0)  

    if not cap.isOpened():
        print("Error: No camera detected.")
        messagebox.showerror("Camera Error", "Could not open video device.")
        return

    cv2.namedWindow("Camera Calibration")
    cv2.setMouseCallback("Camera Calibration", select_rectangle)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        x1 = int(rectangle_top_left_corner[0])
        y1 = int(rectangle_top_left_corner[1])
        tl = (x1, y1)

        x2 = int(rectangle_bottom_right_corner[0])
        y2 = int(rectangle_bottom_right_corner[1])
        br = (x2, y2)


        # Draw rectangle + red dots at corners
        cv2.rectangle(frame, tl, br, (255, 0, 0), 2)
        cv2.circle(frame, tl, 5, (0, 0, 255), -1)
        cv2.circle(frame, br, 5, (0, 0, 255), -1)

        cv2.imshow("Camera Calibration", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13:  # Enter
            # Make sure top-left is above and to the left of bottom-right
            tl_corrected = (min(tl[0], br[0]), min(tl[1], br[1]))
            br_corrected = (max(tl[0], br[0]), max(tl[1], br[1]))
            camera_coordinates = {"tl_corner": tl_corrected, "br_corner": br_corrected}
            save_coordinates(camera_coordinates)
            messagebox.showinfo("Done", "Camera calibration saved.")
            break
        elif key == 27:  # Esc
            print("Canceled by user.")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    camera_calibration()
