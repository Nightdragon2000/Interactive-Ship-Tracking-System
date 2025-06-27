import rasterio
import pygame
import sys
import numpy as np
import os

# Define the path to the GeoTIFF file
image_path = r'c:\Users\Administrator\Desktop\modify_thesis_for_git\images\georeferenced\georeferenced_map.tif'

# Define the geographic coordinates (longitude, latitude)
# Note: Rasterio uses (lon, lat) order
lon,lat = 37.583170, 24.756412



# Marker color
MARKER_COLOR = (255, 0, 0) # Red
MARKER_RADIUS = 5

try:
    # Open the GeoTIFF file
    with rasterio.open(image_path) as src:
        print(f"Opened image: {image_path}")
        print(f"CRS: {src.crs}")
        print(f"Bounds: {src.bounds}")
        print(f"Transform:\n{src.transform}")

        # Convert geographic coordinates to pixel coordinates
        try:
            row, col = src.index(lon, lat)
            print(f"Geographic coordinates (lon, lat): ({lon}, {lat})")
            print(f"Calculated pixel coordinates (col, row): ({col}, {row})")
        except IndexError:
            print(f"Error: Coordinates ({lon}, {lat}) are outside the image bounds.")
            sys.exit(1)

        # Read image data
        # Read all bands if it's RGB, otherwise read the first band
        if src.count >= 3:
            # Read RGB bands and stack them correctly for Pygame (needs Height x Width x 3)
            img_data = np.stack([src.read(1), src.read(2), src.read(3)], axis=-1)
            # Ensure data is in uint8 format for Pygame
            if img_data.dtype != np.uint8:
                 # Basic scaling for display, might need adjustment based on data range
                 img_data = ((img_data - img_data.min()) / (img_data.max() - img_data.min()) * 255).astype(np.uint8)
            # Pygame expects Width x Height, rasterio gives Height x Width
            img_data = np.transpose(img_data, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_data)
        else:
            # Read single band and convert to 3-channel grayscale for Pygame
            img_band = src.read(1)
            # Ensure data is in uint8 format for Pygame
            if img_band.dtype != np.uint8:
                # Basic scaling for display
                img_band = ((img_band - img_band.min()) / (img_band.max() - img_band.min()) * 255).astype(np.uint8)
            # Stack into 3 channels
            img_data = np.stack([img_band]*3, axis=-1)
            # Pygame expects Width x Height
            img_data = np.transpose(img_data, (1, 0, 2))
            img_surface = pygame.surfarray.make_surface(img_data)

        # Get image dimensions
        width, height = src.width, src.height

    # Initialize Pygame
    pygame.init()

    # Set up the display window
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(f'Image Viewer: {os.path.basename(image_path)}')

    # Game loop flag
    running = True

    # Main loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw the image onto the screen
        screen.blit(img_surface, (0, 0))

        # Draw the marker at the calculated pixel coordinates
        # Pygame uses (x, y) which corresponds to (col, row)
        pygame.draw.circle(screen, MARKER_COLOR, (int(col), int(row)), MARKER_RADIUS)

        # Update the display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()

except rasterio.RasterioIOError as e:
    print(f"Error opening or reading the image file: {e}")
    if 'not recognized as a supported file format' in str(e):
        print("Hint: Ensure GDAL drivers are correctly installed and accessible.")
except ImportError:
    print("Error: Pygame or Rasterio library not found. Please install them (`pip install pygame rasterio numpy`).")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # Ensure pygame quits even if errors occur after initialization
    if 'pygame' in locals() and pygame.get_init():
        pygame.quit()