# Cyclades Interactive System

## Overview

The **Cyclades Interactive System** was developed as a thesis project to explore innovative ways of interacting with real-time geospatial data. It projects live AIS ship positions onto a 3D-printed model of the Cyclades islands and allows users to interact using hand gestures detected by a webcam. This immersive system enhances the understanding of maritime traffic and spatial relationships in a physical-digital hybrid environment.

**Note:** While this system is designed for the Cyclades region, its modular architecture allows adaptation to other geographic areas. You can georeference a different map, modify AIS sources, or customize interaction components to suit your use case.


## Features

- Real-time AIS data decoding and live mapping
- Projection of ships on a physical Cyclades model
- Webcam-based gesture interaction
- Unified configuration interface for projector, camera, database, and georeferencing
- Clean and modular user interface
- Built with Python, Tkinter, MediaPipe, Pygame, PostgreSQL/MySQL


## Installation

### First-Time Setup (Windows)

Download the repository files and run the setup script to prepare the environment and launch the system:

```bat
first_time_setup.bat
```

This script will:
- Create a virtual environment (`venv`)
- Install required dependencies from `requirements.txt`
- Launch the main graphical interface (`launcher.py`)

### Regular Use

After the first-time setup, you can run the system using:

```bat
run.bat
```

Or directly with Python:

```bash
python launcher.py
```



## Help

Access the in-app help from the launcher. Here's a quick summary:

- **Configuration Panel**:
  - Calibrate the projector and camera
  - Assign geospatial coordinates to a map image
  - Configure the database backend

- **Launch Application**:
  - Starts the visualization system
  - Displays ship movements on the physical model
  - Enables webcam gesture interaction
  - Shows AIS data (if the receiver is detected)



## Author

**Afroditi Kalantzi**  
Department of Product and Systems Design Engineering  
University of the Aegean



## License

This project is intended for academic and experimental use.  
For reuse, modification, or citation, please contact the author.
