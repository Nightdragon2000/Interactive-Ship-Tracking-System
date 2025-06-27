import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox # Added messagebox
from PIL import Image, ImageTk
import rasterio
import numpy as np
import os
import json
import cv2
import pygame 
import psycopg2
import mysql.connector
from rasterio.transform import from_gcps

# Define the path for the JSON file
camera_and_projector_json_path = os.path.join(os.path.dirname(__file__), 'coordinates.json')
# Define the path for the georeferenced image (placeholder, needs actual path)
georeferenced_image_path = os.path.join(os.path.dirname(__file__), 'images', 'georeferenced', 'georeferenced_map.tif') # Path for the output georeferenced image

#--------------------------------- Helper Functions ---------------------------------#

# Function to save coordinates to a JSON file
def save_coordinates_to_json(camera_coordinates=None, projector_coordinatess=None):
    data = {}
    if os.path.exists(camera_and_projector_json_path):
        try:
            with open(camera_and_projector_json_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {camera_and_projector_json_path}. Starting with empty data.")
            data = {}

    if camera_coordinates:
        data['camera'] = camera_coordinates

    if projector_coordinatess:
        data['projector'] = projector_coordinatess

    with open(camera_and_projector_json_path, 'w') as f:
        json.dump(data, f, indent=4) # Added indent for readability
    print("Coordinates saved to", camera_and_projector_json_path)

#--------------------------------- Camera Calibration ---------------------------------#
# Starting coordinates for rectangle
rectangle_top_left_corner = (100, 100)
rentangle_bottom_right_corner = (300, 300)
dragging_corner = None
offset_x, offset_y = 0, 0 # Initialize offset_x and offset_y

# Function to handle mouse events for selecting rectangle
def select_rectangle(event, x, y, flags, param):
    global rectangle_top_left_corner, rentangle_bottom_right_corner, dragging_corner, offset_x, offset_y

    if event == cv2.EVENT_LBUTTONDOWN:
        # Check corners first for precise selection
        if abs(rectangle_top_left_corner[0] - x) < 10 and abs(rectangle_top_left_corner[1] - y) < 10:
            dragging_corner = 'start'
        elif abs(rentangle_bottom_right_corner[0] - x) < 10 and abs(rentangle_bottom_right_corner[1] - y) < 10:
            dragging_corner = 'end'
        # Then check if inside the rectangle for moving
        elif rectangle_top_left_corner[0] < x < rentangle_bottom_right_corner[0] and rectangle_top_left_corner[1] < y < rentangle_bottom_right_corner[1]:
            dragging_corner = 'move'
            offset_x = x - rectangle_top_left_corner[0]
            offset_y = y - rectangle_top_left_corner[1]
        else:
            dragging_corner = None

    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging_corner == 'start':
            rectangle_top_left_corner = (x, y)
        elif dragging_corner == 'end':
            rentangle_bottom_right_corner = (x, y)
        elif dragging_corner == 'move':
            width = rentangle_bottom_right_corner[0] - rectangle_top_left_corner[0]
            height = rentangle_bottom_right_corner[1] - rectangle_top_left_corner[1]
            rectangle_top_left_corner = (x - offset_x, y - offset_y)
            rentangle_bottom_right_corner = (rectangle_top_left_corner[0] + width, rectangle_top_left_corner[1] + height)

    elif event == cv2.EVENT_LBUTTONUP:
        dragging_corner = None

# Function to calibrate the camera
def camera_calibration():
    global rectangle_top_left_corner, rentangle_bottom_right_corner
    cap = cv2.VideoCapture(0) # Use default camera (index 0)
    if not cap.isOpened():
        print("Error: Could not open video device")
        messagebox.showerror("Camera Error", "Could not open video device. Make sure a camera is connected.")
        return

    cv2.namedWindow("Create Rectangle")
    cv2.setMouseCallback("Create Rectangle", select_rectangle)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Error: Can't receive frame (stream end?). Exiting ...")
            break

        frame = cv2.flip(frame, 1) # Flip horizontally for a mirror effect

        # Ensure coordinates are valid integers for drawing
        try:
            tl_corner_int = tuple(map(int, rectangle_top_left_corner))
            br_corner_int = tuple(map(int, rentangle_bottom_right_corner))
        except ValueError:
             print("Warning: Invalid coordinates detected, resetting to default.")
             rectangle_top_left_corner = (100, 100)
             rentangle_bottom_right_corner = (300, 300)
             tl_corner_int = tuple(map(int, rectangle_top_left_corner))
             br_corner_int = tuple(map(int, rentangle_bottom_right_corner))

        # Draw the rectangle and corner circles
        cv2.rectangle(frame, tl_corner_int, br_corner_int, (255, 0, 0), 2)
        cv2.circle(frame, tl_corner_int, 5, (0, 0, 255), -1)
        cv2.circle(frame, br_corner_int, 5, (0, 0, 255), -1)

        cv2.imshow("Create Rectangle", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == 13: # Enter key pressed
            # Ensure coordinates are ordered correctly (top-left, bottom-right)
            final_tl_x = min(tl_corner_int[0], br_corner_int[0])
            final_tl_y = min(tl_corner_int[1], br_corner_int[1])
            final_br_x = max(tl_corner_int[0], br_corner_int[0])
            final_br_y = max(tl_corner_int[1], br_corner_int[1])
            final_tl_corner = (final_tl_x, final_tl_y)
            final_br_corner = (final_br_x, final_br_y)

            camera_coordinates = {"tl_corner": final_tl_corner, "br_corner": final_br_corner}
            save_coordinates_to_json(camera_coordinates=camera_coordinates)
            messagebox.showinfo("Success", "Camera calibration completed successfully!") # Added success popup
            break
        elif key == 27: # Esc key pressed
            print("Camera calibration cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()

#--------------------------------- Projector Calibration ---------------------------------#

def projector_calibration():
    global georeferenced_image_path # Ensure global access if needed
    if not georeferenced_image_path or not os.path.exists(georeferenced_image_path):
        # Prompt user to select the file if not found
        messagebox.showerror("Error", "Georeferenced image path not set or file not found.")
        georeferenced_image_path = filedialog.askopenfilename(title="Select Georeferenced Image", 
                                                          filetypes=[("GeoTIFF files", "*.tif"), ("All files", "*.*")])
        if not georeferenced_image_path:
            return  # User cancelled selection
        if not os.path.exists(georeferenced_image_path):
            messagebox.showerror("Error", "Selected file does not exist.")
            return

    try:
        # Try to open the image with rasterio
        with rasterio.open(georeferenced_image_path) as src:
            # Read the image data
            image_data = src.read()
            print(f"Image loaded: {georeferenced_image_path}")
            print(f"Image shape: {image_data.shape}")
    except rasterio.RasterioIOError as e:
        messagebox.showerror("File Error", f"Could not open georeferenced image: {e}")
        return
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error opening image: {e}")
        return

    # Ensure we have at least 3 bands (RGB)
    if image_data.shape[0] < 3:
        # Convert single band to RGB if needed
        print("Converting single band to RGB")
        band = image_data[0]
        # Normalize to 0-255 range if needed
        if band.dtype != np.uint8:
            band = ((band - band.min()) / (band.max() - band.min()) * 255).astype(np.uint8)
        image_data = np.stack([band, band, band], axis=0)

    # Transpose to get height x width x channels format for pygame
    image_data = np.transpose(image_data[:3, :, :], (1, 2, 0)).astype(np.uint8)
    
    # Apply requested rotation (90 degrees left) and vertical flip
    image_data = np.rot90(image_data, 1)  # Rotate 90 degrees left (k=1)
    image_data = np.flipud(image_data)    # Flip vertically

    # Initialize pygame
    pygame.init()
    pygame.font.init()  # Initialize font module

    # Font setup
    font_size = 24  # Increased font size for better visibility
    font = pygame.font.SysFont(None, font_size)  # Use default system font
    text_color = (255, 0, 0)  # Red
    counter_color = (255, 255, 0)  # Yellow for counter

    # Instructions text
    instructions = [
        "Move with left click and drag.",
        "Scale with mouse wheel or +/- keys.",
        "Press Enter when finished.",
        "Press ESC to cancel."
    ]
    instruction_surfaces = [font.render(text, True, text_color) for text in instructions]

    # Get screen dimensions
    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    print(f"Screen dimensions: {screen_width}x{screen_height}")

    # Attempt to create fullscreen display
    try:
        screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        pygame.display.set_caption("Projector Calibration")
    except pygame.error as e:
        messagebox.showerror("Display Error", f"Could not set fullscreen mode: {e}")
        pygame.quit()
        return

    # Initial image setup
    try:
        # Create pygame surface from numpy array
        image_surface_original = pygame.surfarray.make_surface(image_data)
        print(f"Created pygame surface: {image_surface_original.get_width()}x{image_surface_original.get_height()}")
    except ValueError as e:
        messagebox.showerror("Image Error", f"Could not create Pygame surface: {e}. Check image data format.")
        pygame.quit()
        return
    except Exception as e:
        messagebox.showerror("Error", f"Unexpected error creating surface: {e}")
        pygame.quit()
        return

    # Make a copy of the original surface for scaling
    image_surface = image_surface_original.copy()
    image_rect = image_surface.get_rect()
    image_rect.center = screen.get_rect().center  # Center initially

    # Scaling parameters
    scale_factor = 1.0
    min_scale = 0.1
    max_scale = 5.0

    # Interaction state
    running = True
    dragging = False
    offset_x, offset_y = 0, 0
    
    # Counter for frames
    frame_count = 0
    clock = pygame.time.Clock()

    def scale_image(surface, scale):
        """Scale the image surface by the given factor"""
        try:
            new_size = (int(surface.get_width() * scale), int(surface.get_height() * scale))
            # Use smoothscale for better quality if performance allows
            return pygame.transform.smoothscale(surface, new_size)
        except Exception as e:
            print(f"Error scaling image: {e}")
            return surface  # Return original if scaling fails

    # Main loop
    while running:
        # Increment frame counter
        frame_count += 1
        
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    new_scale = min(scale_factor * 1.1, max_scale)  # Scale multiplicatively
                    if new_scale != scale_factor:
                        scale_factor = new_scale
                        old_center = image_rect.center
                        image_surface = scale_image(image_surface_original, scale_factor)
                        image_rect = image_surface.get_rect(center=old_center)
                elif event.key == pygame.K_MINUS:
                    new_scale = max(scale_factor * 0.9, min_scale)  # Scale multiplicatively
                    if new_scale != scale_factor:
                        scale_factor = new_scale
                        old_center = image_rect.center
                        image_surface = scale_image(image_surface_original, scale_factor)
                        image_rect = image_surface.get_rect(center=old_center)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Save coordinates on Enter key press
                    # Coordinates are relative to the top-left of the screen
                    top_left = image_rect.topleft
                    bottom_right = image_rect.bottomright
                    save_coordinates_to_json(projector_coordinatess={"tl_corner": top_left, "br_corner": bottom_right})
                    messagebox.showinfo("Success", "Projector calibration completed successfully!")
                    running = False  # Exit after saving

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    if image_rect.collidepoint(event.pos):
                        dragging = True
                        mouse_x, mouse_y = event.pos
                        offset_x = image_rect.x - mouse_x
                        offset_y = image_rect.y - mouse_y
                elif event.button == 4:  # Scroll up (Zoom in)
                    new_scale = min(scale_factor * 1.1, max_scale)
                    if new_scale != scale_factor:
                        scale_factor = new_scale
                        old_center = image_rect.center
                        image_surface = scale_image(image_surface_original, scale_factor)
                        image_rect = image_surface.get_rect(center=old_center)
                elif event.button == 5:  # Scroll down (Zoom out)
                    new_scale = max(scale_factor * 0.9, min_scale)
                    if new_scale != scale_factor:
                        scale_factor = new_scale
                        old_center = image_rect.center
                        image_surface = scale_image(image_surface_original, scale_factor)
                        image_rect = image_surface.get_rect(center=old_center)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    mouse_x, mouse_y = event.pos
                    image_rect.x = mouse_x + offset_x
                    image_rect.y = mouse_y + offset_y

        # Drawing
        screen.fill((0, 0, 0))  # Black background
        
        # Draw the image if it exists
        if image_surface and image_rect:
            screen.blit(image_surface, image_rect)

        # Draw instructions in the top-left corner
        text_y = 10  # Starting y position for the first line
        for surface in instruction_surfaces:
            screen.blit(surface, (10, text_y))
            text_y += font_size + 2  # Move down for the next line

        # Draw frame counter in the top-right corner
        counter_text = f"Frame: {frame_count}"
        counter_surface = font.render(counter_text, True, counter_color)
        counter_rect = counter_surface.get_rect(topright=(screen_width - 10, 10))
        screen.blit(counter_surface, counter_rect)
        
        # Draw scale factor indicator
        scale_text = f"Scale: {scale_factor:.2f}x"
        scale_surface = font.render(scale_text, True, counter_color)
        scale_rect = scale_surface.get_rect(topright=(screen_width - 10, 10 + font_size + 5))
        screen.blit(scale_surface, scale_rect)

        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)  # 60 FPS

    # Clean up pygame
    pygame.quit()
    print("Projector calibration finished.")


#--------------------------------- Database Connection Setup ---------------------------------#

# Global variables for config (scoped within the function or passed as arguments if needed elsewhere)
DB_TYPE = ""
DB_HOST = ""
DB_PORT = 0
DB_USER = ""
DB_PASSWORD = ""
DB_NAME = ""

def save_config():
    global DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    config_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(config_dir, "db_config.py")
    try:
        with open(config_path, 'w') as f:
            f.write("# Database configuration generated by setup.py\n")
            f.write(f"DB_TYPE = '{DB_TYPE}'\n")
            f.write(f"DB_HOST = '{DB_HOST}'\n")
            f.write(f"DB_PORT = {DB_PORT}\n")
            f.write(f"DB_USER = '{DB_USER}'\n")
            # Avoid storing plain passwords in config files if possible
            # Consider environment variables or more secure methods
            f.write(f"DB_PASSWORD = '{DB_PASSWORD}'\n")
            f.write(f"DB_NAME = '{DB_NAME}'\n")
        print(f"Configuration saved to {config_path}")
    except IOError as e:
        messagebox.showerror("Config Save Error", f"Could not save database configuration: {e}")

def setup_postgresql_database():
    global DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    if not psycopg2:
        messagebox.showerror("Dependency Error", "psycopg2 library is not installed. Please install it (pip install psycopg2-binary) and try again.")
        return False
    try:
        # Connect to the default 'postgres' database first to check/create the target database
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database="postgres")
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}") # Be cautious with direct string formatting for DB names
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        cursor.close()
        conn.close()

        # Connect to the target database to create the table
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ships_syros (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            mmsi VARCHAR(20) NOT NULL,
            latitude DOUBLE PRECISION,
            longitude DOUBLE PRECISION,
            name VARCHAR(255),
            image_path VARCHAR(255),
            navigation_status VARCHAR(100),
            destination VARCHAR(255),
            eta VARCHAR(100),
            speed DOUBLE PRECISION
        )
        """)
        # Consider adding index creation if it doesn't exist
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ships_mmsi_timestamp ON ships_syros(mmsi, timestamp)")
        conn.commit()
        print("Table 'ships_syros' created or already exists.")
        print("PostgreSQL database setup completed successfully!")
        save_config()
        cursor.close()
        conn.close()
        return True
    except psycopg2.Error as e:
        messagebox.showerror("PostgreSQL Error", f"Error setting up PostgreSQL database: {e}")
        return False
    except Exception as e:
        messagebox.showerror("Setup Error", f"An unexpected error occurred during PostgreSQL setup: {e}")
        return False

def setup_mysql_database():
    global DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    if not mysql.connector:
        messagebox.showerror("Dependency Error", "mysql-connector-python library is not installed. Please install it (pip install mysql-connector-python) and try again.")
        return False
    try:
        # Connect without specifying database first to check/create it
        conn = mysql.connector.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
        exists = cursor.fetchone()
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}") # Be cautious with direct string formatting
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        cursor.execute(f"USE {DB_NAME}")

        # Create table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ships (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME NOT NULL,
            mmsi VARCHAR(20) NOT NULL,
            latitude DOUBLE,
            longitude DOUBLE,
            name VARCHAR(255),
            image_path VARCHAR(255),
            navigation_status VARCHAR(100),
            destination VARCHAR(255),
            eta VARCHAR(100),
            speed DOUBLE
        )
        """)
        # Check if index exists before creating (more robust)
        cursor.execute("""
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='ships' AND index_name='idx_ships_mmsi_timestamp';
        """)
        if not cursor.fetchone()[0]:
             cursor.execute("CREATE INDEX idx_ships_mmsi_timestamp ON ships(mmsi, timestamp)")
             print("Index 'idx_ships_mmsi_timestamp' created.")
        else:
             print("Index 'idx_ships_mmsi_timestamp' already exists.")

        conn.commit()
        print("Table 'ships' created or already exists.")
        print("MySQL database setup completed successfully!")
        save_config()
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        messagebox.showerror("MySQL Error", f"Error setting up MySQL database: {e}")
        return False
    except Exception as e:
        messagebox.showerror("Setup Error", f"An unexpected error occurred during MySQL setup: {e}")
        return False

def database_connection(parent_window): # Accept parent window as argument
    global DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME

    # Use simpledialog for input within the Tkinter context
    db_choice = simpledialog.askstring("Database Setup", "Choose database type:\n1. PostgreSQL\n2. MySQL", parent=parent_window) # Use the passed parent_window

    if db_choice not in ['1', '2']:
        messagebox.showwarning("Invalid Choice", "Invalid choice. Please enter 1 or 2.")
        return # Exit if choice is invalid

    # Get DB details using simpledialog
    DB_HOST_input = simpledialog.askstring("Database Setup", "Host:", initialvalue="localhost", parent=parent_window)
    DB_HOST = DB_HOST_input if DB_HOST_input else "localhost"

    if db_choice == '1':
        DB_TYPE = "postgresql"
        DB_PORT_input = simpledialog.askstring("Database Setup", "Port:", initialvalue="5432", parent=parent_window)
        try:
            DB_PORT = int(DB_PORT_input) if DB_PORT_input else 5432
        except ValueError:
            messagebox.showerror("Invalid Input", "Port must be a number.", parent=parent_window)
            return
        DB_USER_input = simpledialog.askstring("Database Setup", "Username:", initialvalue="postgres", parent=parent_window)
        DB_USER = DB_USER_input if DB_USER_input else "postgres"
        DB_PASSWORD = simpledialog.askstring("Database Setup", "Password:", show='*', parent=parent_window) # Use show='*'
        DB_NAME_input = simpledialog.askstring("Database Setup", "Database name:", initialvalue="Ship_DB", parent=parent_window)
        DB_NAME = DB_NAME_input if DB_NAME_input else "Ship_DB"

        if setup_postgresql_database():
            messagebox.showinfo("Success", "PostgreSQL setup successful!")
        # Error messages are handled within setup_postgresql_database

    elif db_choice == '2':
        DB_TYPE = "mysql"
        DB_PORT_input = simpledialog.askstring("Database Setup", "Port:", initialvalue="3306", parent=parent_window)
        try:
            DB_PORT = int(DB_PORT_input) if DB_PORT_input else 3306
        except ValueError:
            messagebox.showerror("Invalid Input", "Port must be a number.", parent=parent_window)
            return
        DB_USER_input = simpledialog.askstring("Database Setup", "Username:", initialvalue="root", parent=parent_window)
        DB_USER = DB_USER_input if DB_USER_input else "root"
        DB_PASSWORD = simpledialog.askstring("Database Setup", "Password:", show='*', parent=parent_window)
        DB_NAME_input = simpledialog.askstring("Database Setup", "Database name:", initialvalue="Ship_DB", parent=parent_window)
        DB_NAME = DB_NAME_input if DB_NAME_input else "Ship_DB"

        if setup_mysql_database():
            messagebox.showinfo("Success", "MySQL setup successful!")
        # Error messages are handled within setup_mysql_database

#--------------------------------- Georeference Tool ---------------------------------#


# Global variables for georeferencing tool
image_on_canvas = None
img_display = None
img_original = None
original_file_path = None
scale_factor = 1.0
last_x, last_y = 0, 0
initial_placement_done = False
points_needed = 4
selected_points = []
point_counter_text = None
temporary_dot_id = None
root = None
canvas = None
instruction_text = None

# Function to update the displayed image (for scaling and moving)
def update_image_display():
    global img_original, img_display, image_on_canvas, scale_factor, canvas, root
    
    # Safety checks
    if img_original is None:
        print("Warning: No original image available for display")
        return
    if not canvas or not canvas.winfo_exists():
        print("Warning: Canvas does not exist or has been destroyed")
        return
    
    try:
        # Calculate new size based on scale factor
        new_width = int(img_original.width * scale_factor)
        new_height = int(img_original.height * scale_factor)
        
        # Avoid making the image too small
        if new_width < 1 or new_height < 1:
            return
            
        # Resize the image
        img_resized = img_original.resize((new_width, new_height), Image.LANCZOS)
        
        # Convert to Tkinter compatible format
        img_display = ImageTk.PhotoImage(img_resized)
        
        # Store references at multiple levels to prevent garbage collection
        # This is critical to prevent 'pyimage doesn't exist' errors
        if canvas and canvas.winfo_exists():
            canvas.img_reference = img_display  # Store on canvas
        if root and root.winfo_exists():
            root.img_reference = img_display    # Store on root
        
        # Add to root's image reference list to prevent garbage collection
        if root and root.winfo_exists() and hasattr(root, '_image_references'):
            root._image_references.append(img_display)
        
        # Store in the all_image_references dictionary on the root window
        if root and root.winfo_exists() and hasattr(root, 'all_image_references'):
            root.all_image_references[id(img_display)] = img_display
        
        # Store in the persistent dictionary attached to run_georeference_tool
        # This ensures references are maintained across different contexts and function calls
        if hasattr(run_georeference_tool, 'image_references'):
            run_georeference_tool.image_references[id(img_display)] = img_display
        
        # If image is already on canvas, update it
        if canvas and canvas.winfo_exists() and image_on_canvas and canvas.type(image_on_canvas) == 'image':  # Verify item exists and is an image
            canvas.itemconfig(image_on_canvas, image=img_display)
        elif canvas and canvas.winfo_exists():
            # Create or recreate the image if needed
            if image_on_canvas:
                print("Warning: Image canvas item no longer exists or is invalid, recreating")
            # Create the image at the center of the canvas
            image_on_canvas = canvas.create_image(canvas.winfo_width()//2, canvas.winfo_height()//2, image=img_display)
            canvas.img_reference = img_display  # Ensure reference is maintained
            
        # Force a Tkinter update to ensure the image is displayed
        if root and root.winfo_exists():
            root.update_idletasks()
    except tk.TclError as e:
        print(f"Tkinter error during image update: {e}")
    except Exception as e:
        print(f"Error updating image display: {e}")
        # Don't re-raise to prevent application crash

# Function to update the point counter display
def update_point_counter():
    global point_counter_text, selected_points, points_needed, canvas
    
    if not canvas or not canvas.winfo_exists():
        return
        
    try:
        # Create or update the counter text
        counter_text = f"Points: {len(selected_points)}/{points_needed}"
        if point_counter_text and canvas.type(point_counter_text) == 'text':
            canvas.itemconfig(point_counter_text, text=counter_text)
        else:
            # Create new counter text in top-right corner
            point_counter_text = canvas.create_text(
                canvas.winfo_width() - 10, 10, 
                text=counter_text, 
                fill="blue", 
                anchor="ne"
            )
    except Exception as e:
        print(f"Error updating point counter: {e}")

# Function to update the positions of selected points (dots) on the canvas
def update_dot_positions():
    global selected_points, scale_factor, image_on_canvas, canvas, img_original, root
    
    # Safety checks
    if not canvas or not canvas.winfo_exists():
        print("Warning: Canvas does not exist or has been destroyed")
        return
    if not image_on_canvas or not img_original:
        return
        
    try:
        # Verify image item still exists on canvas
        if canvas.type(image_on_canvas) != 'image':
            print("Warning: Image canvas item is invalid or no longer exists")
            return
            
        # Get canvas coordinates of the image center
        img_coords = canvas.coords(image_on_canvas)
        if not img_coords: # Check if coords are available
            print("Warning: Could not get image coordinates")
            return 
            
        img_center_x, img_center_y = img_coords[0], img_coords[1]

        # Get current displayed image dimensions
        displayed_width = int(img_original.width * scale_factor)
        displayed_height = int(img_original.height * scale_factor)

        # Calculate top-left corner of the displayed image on canvas
        img_top_left_x = img_center_x - displayed_width / 2
        img_top_left_y = img_center_y - displayed_height / 2
        
        # Update each dot position
        for i, point_data in enumerate(selected_points):
            pixel_coords, real_coords, dot_id = point_data
            
            # Calculate new position based on current image position and scale
            new_x = img_top_left_x + (pixel_coords[0] * scale_factor)
            new_y = img_top_left_y + (pixel_coords[1] * scale_factor)
            
            # Update dot position on canvas
            if dot_id and canvas.type(dot_id) == 'oval':
                # Get current dot size (maintain consistent visual size)
                dot_coords = canvas.coords(dot_id)
                if dot_coords and len(dot_coords) == 4:
                    dot_width = (dot_coords[2] - dot_coords[0]) / 2
                    dot_height = (dot_coords[3] - dot_coords[1]) / 2
                    
                    # Update dot position
                    canvas.coords(dot_id, 
                                new_x - dot_width, new_y - dot_height,
                                new_x + dot_width, new_y + dot_height)
    except Exception as e:
        print(f"Error updating dot positions: {e}")
        # Don't re-raise to prevent application crash

# Function to open an image file for georeferencing
def open_image():
    global img_original, img_display, image_on_canvas, scale_factor, points_needed, selected_points, initial_placement_done, original_file_path, root, canvas
    
    # Ask user to select a file
    file_path = filedialog.askopenfilename()
    if not file_path:
        if root: root.destroy() # Exit if no file selected
        return # User cancelled

    try:
        # Open the image using Pillow
        img_original = Image.open(file_path)
        original_file_path = file_path # Store the path
        # Ensure filename attribute exists for later use if needed by Pillow itself
        if not hasattr(img_original, 'filename'):
            img_original.filename = file_path 
            
        scale_factor = 1.0 # Reset scale
        points_needed = 4 # Reset points needed
        selected_points = [] # Clear previous points
        initial_placement_done = False # Reset placement flag for new image
        
        # Clear any existing image references to prevent memory leaks
        if hasattr(root, 'all_image_references'):
            root.all_image_references.clear()
        
        # Create a small initial display image to ensure references are established
        # This helps prevent 'pyimage doesn't exist' errors
        small_display = ImageTk.PhotoImage(img_original.resize((1, 1), Image.LANCZOS))
        
        # Store references at multiple levels to prevent garbage collection
        root.small_display_reference = small_display
        if not hasattr(root, '_image_references'):
            root._image_references = []
        root._image_references.append(small_display)
        
        # Store in the persistent dictionary
        if hasattr(run_georeference_tool, 'image_references'):
            run_georeference_tool.image_references[id(small_display)] = small_display
            if hasattr(root, 'all_image_references'):
                root.all_image_references[id(small_display)] = small_display
        
        # Make sure canvas exists before updating
        if canvas and canvas.winfo_exists():
            update_point_counter() # Update counter display
            # Initial display is now handled by handle_configure
            root.update_idletasks()
            update_image_display() # Force an initial image display
        else:
            print("Warning: Canvas does not exist or has been destroyed")
            
        # Show the main window now that an image is loaded
        root.deiconify()
        # Ensure canvas dimensions are updated AFTER deiconify
        root.update_idletasks()
    except Exception as e:
        print(f"Error opening image: {e}")
        messagebox.showerror("Image Error", f"Failed to open image: {e}")
        if root: root.destroy() # Exit if image fails to load

def run_georeference_tool():
    # Global variables to store image state
    global image_on_canvas, img_display, img_original, original_file_path, scale_factor, last_x, last_y, initial_placement_done, points_needed, selected_points, point_counter_text, temporary_dot_id, root, canvas, instruction_text

    # Create a new Tkinter root window specifically for this tool
    # This ensures we have a fresh context each time the tool is run
    if 'root' in globals() and root is not None and root.winfo_exists():
        try:
            root.destroy()  # Clean up any existing window
        except tk.TclError:
            pass  # Ignore if already destroyed

    # Reset all global variables to ensure clean state
    image_on_canvas = None
    img_display = None
    img_original = None
    original_file_path = None # Add global variable for path
    scale_factor = 1.0
    last_x, last_y = 0, 0
    initial_placement_done = False # Flag for initial centering
    points_needed = 4
    selected_points = [] # List to store tuples: ( (pixel_x, pixel_y), real_coords, dot_id )
    point_counter_text = None # Canvas text item for the counter
    temporary_dot_id = None # ID of the dot drawn before confirmation
    
    # Create a new root window
    root = tk.Tk()
    root.title("Image Georeferencing Tool")
    root.geometry("800x600")  # Set initial window size
    
    # Create a dictionary to store all image references for this session
    # This prevents garbage collection of images while the window is open
    root.all_image_references = {}
    
    # Create a list to store image references
    root._image_references = []
    
    # Create the main frame
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Create canvas for the image
    canvas = tk.Canvas(main_frame, bg="#f0f0f0")
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Create a frame for buttons
    button_frame = tk.Frame(root)
    button_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    # Add Open Image button
    open_button = tk.Button(button_frame, text="Open Image", command=open_image)
    open_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    # Add instruction text on canvas
    instruction_text = canvas.create_text(
        10, 10, anchor="nw", 
        text="Open an image to begin georeferencing.", 
        fill="black"
    )
    
    # Bind events to canvas
    canvas.bind("<MouseWheel>", zoom)
    canvas.bind("<ButtonPress-3>", handle_image_drag_start)  # Right click
    canvas.bind("<B3-Motion>", handle_image_drag_motion)     # Right click drag
    
    # Handle window resize events
    def handle_configure(event):
        # Only update if we have an image and the canvas exists
        if img_original is not None and canvas and canvas.winfo_exists():
            # Force update of image display on resize
            update_image_display()
            # Update dot positions after resize
            update_dot_positions()
    
    # Bind the configure event to handle window resizing
    canvas.bind("<Configure>", handle_configure)
    
    # Make sure the window stays on top when launched from main script
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(root.attributes, '-topmost', False)
    
    # Handle window close event properly
    def on_closing():
        global root, canvas, img_display, img_original, image_on_canvas
        print("Cleaning up resources...")
        # Clear image references
        if hasattr(root, 'all_image_references'):
            root.all_image_references.clear()
        if hasattr(root, '_image_references'):
            root._image_references.clear()
        # Reset variables
        img_display = None
        img_original = None
        image_on_canvas = None
        # Destroy the window
        root.destroy()
    
    # Set the close window handler
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Initialize or access the persistent image references dictionary
    # This dictionary will be attached to the function object to persist between calls
    if not hasattr(run_georeference_tool, 'image_references'):
        run_georeference_tool.image_references = {}
    
    # Create a local reference to the persistent dictionary
    image_references = run_georeference_tool.image_references

    # Using the global open_image function defined earlier
    # Using the global update_image_display function defined earlier
    # Using the global update_dot_positions function defined earlier
                    print("Warning: Image canvas item no longer exists or is invalid, recreating")
                # Create the image at the center of the canvas
                image_on_canvas = canvas.create_image(canvas.winfo_width()//2, canvas.winfo_height()//2, image=img_display)
                canvas.img_reference = img_display  # Ensure reference is maintained
                
            # Force a Tkinter update to ensure the image is displayed
            root.update_idletasks()
        except tk.TclError as e:
            print(f"Tkinter error during image update: {e}")
        except Exception as e:
            print(f"Error updating image display: {e}")
            # Don't re-raise to prevent application crash

    # Function to handle mouse wheel scrolling (zoom)
    def zoom(event):
        global scale_factor
        # Zoom in
        if event.delta > 0:
            scale_factor *= 1.1
        # Zoom out
        elif event.delta < 0:
            scale_factor /= 1.1
        update_image_display()
        update_dot_positions() # Update dot positions after zooming

    # Function to handle image dragging start (Right Click Press)
    def handle_image_drag_start(event):
        global last_x, last_y
        # Record starting position on button press
        last_x = event.x
        last_y = event.y

    # Function to handle image dragging motion (Right Click Motion)
    def handle_image_drag_motion(event):
        global last_x, last_y, canvas, image_on_canvas
        # Calculate movement delta
        dx = event.x - last_x
        dy = event.y - last_y
        # Move the image
        if image_on_canvas: # Ensure image exists
            canvas.move(image_on_canvas, dx, dy)
        # Update last position for next motion event
        last_x = event.x
        last_y = event.y
        update_dot_positions() # Update dot positions after moving image

    # Using the global update_dot_positions function defined earlier

            # Get current displayed image dimensions
            displayed_width = int(img_original.width * scale_factor)
            displayed_height = int(img_original.height * scale_factor)

            # Calculate top-left corner of the displayed image on canvas
            img_top_left_x = img_center_x - displayed_width / 2
            img_top_left_y = img_center_y - displayed_height / 2

            dot_radius = 3 # Same radius as used in get_pixel_coords
            
            # Create a new list to store updated point data
            updated_points = []
            
            for point_data in selected_points:
                original_coords, real_coords, dot_id = point_data
                original_x, original_y = original_coords

                # Calculate canvas coordinates based on original pixel coords, scale, and image position
                canvas_x = img_top_left_x + (original_x * scale_factor)
                canvas_y = img_top_left_y + (original_y * scale_factor)

                # Check if dot still exists on canvas
                valid_dot = False
                try:
                    if canvas.type(dot_id) == 'oval':
                        # Move the dot on the canvas
                        canvas.coords(dot_id, canvas_x - dot_radius, canvas_y - dot_radius, 
                                      canvas_x + dot_radius, canvas_y + dot_radius)
                        canvas.tag_raise(dot_id) # Ensure dot stays on top
                        valid_dot = True
                    else:
                        # Dot ID exists but is not an oval - recreate it
                        print(f"Recreating dot ID {dot_id} as it's not a valid oval")
                        new_dot_id = canvas.create_oval(canvas_x - dot_radius, canvas_y - dot_radius, 
                                                       canvas_x + dot_radius, canvas_y + dot_radius, 
                                                       fill='red', outline='red')
                        # Update point data with new dot ID
                        point_data = (original_coords, real_coords, new_dot_id)
                        valid_dot = True
                except tk.TclError as e:
                    # Dot ID is invalid - recreate it
                    print(f"Recreating dot due to error: {e}")
                    new_dot_id = canvas.create_oval(canvas_x - dot_radius, canvas_y - dot_radius, 
                                                   canvas_x + dot_radius, canvas_y + dot_radius, 
                                                   fill='red', outline='red')
                    # Update point data with new dot ID
                    point_data = (original_coords, real_coords, new_dot_id)
                    valid_dot = True
                    
                if valid_dot:
                    updated_points.append(point_data)
            
            # Update the global selected_points with only valid points
            selected_points = updated_points
        except tk.TclError as e:
            print(f"Tkinter error during dot position update: {e}")
        except Exception as e:
            print(f"Error updating dot positions: {e}")
            # Don't re-raise to prevent application crash

    # Function to update the point counter display position and text
    def update_point_counter():
        global point_counter_text, points_needed, canvas, root
        
        # Safety checks
        if not canvas or not canvas.winfo_exists():
            print("Warning: Canvas does not exist or has been destroyed")
            return
            
        try:
            canvas_width = canvas.winfo_width()
            if canvas_width <= 1:  # Canvas not properly sized yet
                canvas_width = 800  # Use a default width
                
            # Check if counter exists and is valid
            counter_exists = False
            if point_counter_text is not None:
                try:
                    counter_type = canvas.type(point_counter_text)
                    counter_exists = (counter_type == 'text')
                except tk.TclError:
                    counter_exists = False
            
            # Create or recreate counter as needed
            if not counter_exists:
                # If the counter was deleted or is invalid, recreate it
                point_counter_text = canvas.create_text(canvas_width - 10, 10, anchor='ne', 
                                                      text=f"Points left: {points_needed}", 
                                                      fill='red', font=('Arial', 10))
                print("Created new point counter text")
            else:
                # Update existing counter
                canvas.coords(point_counter_text, canvas_width - 10, 10)  # Position top-right
                canvas.itemconfig(point_counter_text, text=f"Points left: {points_needed}", fill='red')
                
            # Store reference to prevent garbage collection
            canvas.counter_reference = point_counter_text
            
            # Ensure counter is on top
            canvas.tag_raise(point_counter_text)
            
        except tk.TclError as e:
            print(f"Tkinter error updating point counter: {e}")
        except Exception as e:
            print(f"Error updating point counter: {e}")
            # Don't re-raise to prevent application crash

    # Function to handle left-click for coordinates
    def get_pixel_coords(event):
        global img_original, img_display, scale_factor, image_on_canvas, points_needed, selected_points, temporary_dot_id, canvas, root

        # Safety checks
        if not canvas or not canvas.winfo_exists():
            print("Warning: Canvas does not exist or has been destroyed")
            return
        if not img_original or not image_on_canvas or points_needed <= 0:
            return # Don't select if no image or all points selected
            
        try:
            # Verify image item still exists on canvas
            if canvas.type(image_on_canvas) != 'image':
                print("Warning: Image canvas item is invalid or no longer exists")
                # Attempt to recover by recreating the image
                update_image_display()
                return
                
            # If a temporary dot exists from a previous cancelled click, remove it
            if temporary_dot_id:
                try:
                    canvas.delete(temporary_dot_id)
                except tk.TclError:
                    pass # Ignore if already deleted
                temporary_dot_id = None

            # Get canvas coordinates of the image center
            img_coords = canvas.coords(image_on_canvas)
            if not img_coords:
                print("Warning: Could not get image coordinates")
                return
                
            img_center_x, img_center_y = img_coords[0], img_coords[1]

            # Get current displayed image dimensions
            displayed_width = int(img_original.width * scale_factor)
            displayed_height = int(img_original.height * scale_factor)

            # Calculate top-left corner of the displayed image on canvas
            img_top_left_x = img_center_x - displayed_width / 2
            img_top_left_y = img_center_y - displayed_height / 2

            # Calculate click coordinates relative to the displayed image's top-left
            click_relative_x = event.x - img_top_left_x
            click_relative_y = event.y - img_top_left_y

            # Convert relative click coordinates to original image coordinates
            original_x = int(click_relative_x / scale_factor)
            original_y = int(click_relative_y / scale_factor)

            # Check if click is within the image bounds
            if 0 <= original_x < img_original.width and 0 <= original_y < img_original.height:
                # Draw a temporary dot at the click location on canvas
                dot_radius = 3
                temporary_dot_id = canvas.create_oval(event.x - dot_radius, event.y - dot_radius, 
                                                      event.x + dot_radius, event.y + dot_radius, 
                                                      fill='red', outline='red')
                canvas.tag_raise(temporary_dot_id) # Ensure dot is visible
                
                # Store reference to prevent garbage collection
                canvas.temp_dot_reference = temporary_dot_id
                
                # Ensure image reference is maintained before dialog blocks execution
                # This is critical to prevent 'pyimage doesn't exist' errors during modal dialog
                if img_display:
                    # Store references at multiple levels to prevent garbage collection
                    canvas.img_reference = img_display  # Store on canvas
                    root.img_reference = img_display    # Store on root
                    
                    # Also store in the function's image_references dictionary
                    if hasattr(run_georeference_tool, 'image_references'):
                        run_georeference_tool.image_references[id(img_display)] = img_display

                # Show prompt asking for real coordinates
                prompt_text = f"Pixel coordinates (x, y): ({original_x}, {original_y})\nEnter real-world coordinates (e.g., X,Y) for point {5 - points_needed}:"
                # Make the dialog transient to the root window
                real_coords = simpledialog.askstring("Enter Real Coordinates", prompt_text, parent=root)
                
                if real_coords:
                    # User entered coordinates - make dot permanent (conceptually)
                    print(f"Point {5 - points_needed}: Pixel=({original_x}, {original_y}), Real={real_coords}")
                    selected_points.append( ( (original_x, original_y), real_coords, temporary_dot_id ) )
                    points_needed -= 1
                    update_point_counter()
                    temporary_dot_id = None # Dot is now permanent, clear temp ID
                    if points_needed == 0:
                        print("All 4 points selected. Press Enter to finish or close the window.")
                else:
                    # User cancelled - remove the temporary dot
                    print("Coordinate entry cancelled.")
                    if temporary_dot_id:
                        try:
                            canvas.delete(temporary_dot_id)
                        except tk.TclError:
                            pass # Ignore if already deleted
                        temporary_dot_id = None
            # else: click was outside the image area on the canvas
        except tk.TclError as e:
            print(f"Tkinter error during coordinate selection: {e}")
            if temporary_dot_id:
                try:
                    canvas.delete(temporary_dot_id)
                except:
                    pass
                temporary_dot_id = None
        except Exception as e:
            print(f"Error during coordinate selection: {e}")
            # Don't re-raise to prevent application crash

    # Function to handle initial image placement and counter update
    def handle_configure(event):
        global image_on_canvas, img_display, initial_placement_done, img_original, scale_factor, canvas, instruction_text, point_counter_text
        
        # Safety check for canvas existence
        if not canvas or not canvas.winfo_exists():
            print("Warning: Canvas does not exist or has been destroyed")
            return
            
        try:
            if img_original and not initial_placement_done:
                # Calculate new size based on scale factor (needed for initial display)
                new_width = int(img_original.width * scale_factor)
                new_height = int(img_original.height * scale_factor)
                if new_width < 1 or new_height < 1:
                    return # Avoid issues if scale is too small initially
                    
                # Create a new PhotoImage to avoid garbage collection issues
                img_resized = img_original.resize((new_width, new_height), Image.LANCZOS)
                img_display = ImageTk.PhotoImage(img_resized)
                
                # Store reference at multiple levels to prevent garbage collection
                # This is critical to prevent 'pyimage doesn't exist' errors
                canvas.img_reference = img_display  # Store on canvas
                root.img_reference = img_display    # Store on root
                
                # Also store in the function's image_references dictionary
                if hasattr(run_georeference_tool, 'image_references'):
                    run_georeference_tool.image_references[id(img_display)] = img_display
                
                # Use event dimensions for accurate centering
                canvas_width = event.width
                canvas_height = event.height
                
                # Check if image_on_canvas exists before creating
                if image_on_canvas is None:
                    image_on_canvas = canvas.create_image(canvas_width // 2, canvas_height // 2, 
                                                         anchor='center', image=img_display)
                else:
                    canvas.coords(image_on_canvas, canvas_width // 2, canvas_height // 2)
                    canvas.itemconfig(image_on_canvas, image=img_display)
                
                # Ensure counter is created if it doesn't exist
                if point_counter_text is None:
                    point_counter_text = canvas.create_text(canvas_width - 10, 10, anchor='ne', 
                                                          text=f"Points left: {points_needed}", 
                                                          fill='red', font=('Arial', 10))
                    
                canvas.tag_raise(instruction_text) # Ensure text is on top
                canvas.tag_raise(point_counter_text) # Ensure counter is on top
                update_point_counter() # Position and update counter
                update_dot_positions() # Update dot positions on initial placement
                initial_placement_done = True # Mark as done
            elif initial_placement_done: # Also update counter and dots on subsequent resizes
                # Ensure counter exists even on resize
                canvas_width = event.width
                if point_counter_text is None or not canvas.type(point_counter_text):
                    # Recreate counter if it doesn't exist or is invalid
                    point_counter_text = canvas.create_text(canvas_width - 10, 10, anchor='ne', 
                                                          text=f"Points left: {points_needed}", 
                                                          fill='red', font=('Arial', 10))
                update_point_counter()
                update_dot_positions()
        except tk.TclError as e:
            print(f"Tkinter error during configure: {e}")
        except Exception as e:
            print(f"Error during window configure: {e}")
            # Don't re-raise to prevent application crash

    # Function to handle exit confirmation on Enter press
    def confirm_exit(event=None): # Added event=None for direct call possibility
        global points_needed, selected_points, img_original, root, original_file_path # Add root, original_file_path
        if points_needed == 0:
            print("All 4 points selected. Proceeding with georeferencing...")
            try:
                # Prepare Ground Control Points (GCPs)
                gcps = []
                for i, point_data in enumerate(selected_points):
                    pixel, real_str, _ = point_data
                    # Parse real-world coordinates (assuming comma-separated X,Y)
                    try:
                        real_x, real_y = map(float, real_str.split(','))
                        # Create rasterio GCP object
                        # Note: rasterio uses (col, row) for pixel coords, which corresponds to (x, y)
                        gcps.append(rasterio.control.GroundControlPoint(row=pixel[1], col=pixel[0], 
                                                                         x=real_x, y=real_y, 
                                                                         id=str(i+1)))
                    except ValueError:
                        messagebox.showerror("Coordinate Error", f"Invalid real-world coordinate format for point {i+1}: '{real_str}'. Please use 'X,Y'.", parent=root)
                        return # Stop processing if format is wrong

                # Calculate the transformation
                transform = from_gcps(gcps)

                # Define output path using the global variable and create directory if needed
                output_path = georeferenced_image_path
                output_dir = os.path.dirname(output_path)
                os.makedirs(output_dir, exist_ok=True)

                # Read original image metadata with rasterio
                if not original_file_path:
                     messagebox.showerror("Error", "Could not retrieve original image file path for georeferencing.", parent=root)
                     if root: root.destroy()
                     return

                with rasterio.open(original_file_path) as src:
                    profile = src.profile
                    profile.update({
                        'driver': 'GTiff',
                        'height': src.height,
                        'width': src.width,
                        'transform': transform,
                        'crs': src.crs # Keep original CRS if exists, otherwise None
                        # Consider adding a default CRS if needed, e.g., 'EPSG:4326'
                        # 'crs': 'EPSG:4326'
                    })

                    # Write the georeferenced file
                    with rasterio.open(output_path, 'w', **profile) as dst:
                        dst.write(src.read())

                print(f"Georeferenced image saved to: {output_path}")
                messagebox.showinfo("Success", f"Georeferenced image saved successfully to:\n{output_path}", parent=root)

            except ImportError:
                messagebox.showerror("Error", "Rasterio library not found. Please install it (`pip install rasterio numpy`) to use georeferencing.", parent=root)
            except Exception as e:
                messagebox.showerror("Georeferencing Error", f"An error occurred during georeferencing: {e}", parent=root)
                print(f"Georeferencing Error: {e}")
            
            # Exit after attempting georeferencing
            if root: root.destroy()

        else:
            if messagebox.askyesno("Confirm Exit", 
                                   f"You have not selected all 4 points ({points_needed} left).\nAre you sure you want to exit? Progress will not be saved.", parent=root):
                if root: root.destroy()

    # --- Main Program Setup within main() ---

    # Create the main window
    root = tk.Tk()
    root.withdraw() # Hide the main window initially
    root.title("Simple Image Viewer - 4 Point Selection") # Updated title

    # Create a canvas widget to display the image
    canvas = tk.Canvas(root, width=1000, height=800, bg='grey') # Increased default size further
    canvas.pack(fill=tk.BOTH, expand=True)
    
    # Create a dictionary to store all image references at the root level
    # This ensures they won't be garbage collected
    root.all_image_references = {}
    if hasattr(run_georeference_tool, 'image_references'):
        root.all_image_references.update(run_georeference_tool.image_references)

    # Add instructions text
    instruction_font = ('Arial', 10)
    instruction_text = canvas.create_text(10, 10, anchor='nw', 
                                          text="Left-click: Select point\nRight-click drag: Move\nMouse wheel: Zoom\nEnter: Finish (if 4 points selected) or Exit", # Updated instructions
                                          fill='red', font=instruction_font) # Changed color to red

    # Add point counter text (initially hidden, updated later)
    point_counter_text = canvas.create_text(0, 0, anchor='ne', 
                                            text=f"Points left: {points_needed}", 
                                            fill='lightblue', font=instruction_font) # Changed color

    # Bind mouse events to the canvas
    canvas.bind("<MouseWheel>", zoom) # For zooming
    canvas.bind("<ButtonPress-3>", handle_image_drag_start) # Right-click press to start move
    canvas.bind("<B3-Motion>", handle_image_drag_motion) # Right-click drag to move
    canvas.bind("<Button-1>", get_pixel_coords) # Left-click select
    canvas.bind("<Configure>", handle_configure) # Handle resize/initial placement

    # Bind Enter key to exit confirmation
    root.bind('<Return>', confirm_exit)

    # Also handle window close button press
    root.protocol("WM_DELETE_WINDOW", confirm_exit)

    # Open file dialog before starting the main loop
    # The window will be shown by open_image if a file is selected
    open_image()

    # Start the Tkinter event loop only if an image was loaded
    if img_original: 
        root.mainloop()
    else:
        print("No image selected or failed to load. Exiting.")
        # Ensure root is destroyed if it exists but mainloop wasn't started
        if root and root.winfo_exists():
             root.destroy()
