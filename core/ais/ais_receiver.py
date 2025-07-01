import os
import sys
import serial
import requests
from bs4 import BeautifulSoup
from pyais import decode
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.db_setup import load_credentials

SERIAL_PORT = "COM5"
BAUD_RATE = 4800
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "..",".." "images", "ships")

# ------- Database Connection -------
def connect_database(credentials):
    engine = credentials["engine"]

    if engine == "postgresql":
        import psycopg2
        conn = psycopg2.connect(
            host=credentials["host"],
            database=credentials["database"],
            user=credentials["user"],
            password=credentials["password"],
            port=credentials["port"]
        )
    elif engine == "mysql":
        import mysql.connector
        conn = mysql.connector.connect(
            host=credentials["host"],
            database=credentials["database"],
            user=credentials["user"],
            password=credentials["password"],
            port=int(credentials["port"])
        )
    else:
        raise ValueError("Unsupported database engine: must be 'postgresql' or 'mysql'.")

    return conn, conn.cursor()

# ------- Ship Info Extraction -------
def fetch_ship_details(mmsi):
    url = f"https://www.vesselfinder.com/vessels/details/{mmsi}"
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.google.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    name = image_url = nav_status = destination = eta = None

    ship_info = soup.find('div', class_='col vfix-top npr')
    if ship_info:
        img = ship_info.find('img', class_='main-photo')
        if img:
            name = img.get('title', '').strip()
            image_url = img.get('src', '')

    nav_table = soup.select_one(
        'body > div.body-wrapper > div > main > div > section:nth-child(4) > div > div.col.vfix-top.lpr > div > div.flx > table.aparams'
    )
    if nav_table:
        for row in nav_table.find_all('tr'):
            tds = row.find_all('td')
            if len(tds) > 1 and tds[0].text.strip() == 'Navigation Status':
                span = tds[1].find('span')
                if span:
                    nav_status = span.text.strip()
                break

    vi_info = soup.find('div', class_='vi__r1 vi__sbt')
    if vi_info:
        dest_tag = vi_info.find('a', class_='_npNa')
        if dest_tag:
            destination = dest_tag.text.split(',')[0].strip()
        eta_tag = vi_info.find('div', class_='_value')
        if eta_tag:
            span = eta_tag.find('span')
            if span:
                eta = span.text.strip().split(':', 1)[-1].strip()

    return name, image_url, nav_status, destination, eta

def save_ship_image(mmsi, url):
    os.makedirs(IMAGE_DIR, exist_ok=True)
    local_path = os.path.join(IMAGE_DIR, f"{mmsi}.jpg")

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(local_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return local_path
    except Exception:
        pass  

    return None

# ------- Main Loop -------
def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"Listening on {SERIAL_PORT} @ {BAUD_RATE} baud...\n")
    except serial.SerialException as e:
        print(f"❌ Failed to open serial port: {e}")
        return

    credentials = load_credentials()
    conn, cursor = connect_database(credentials)
    print(f"Connected to {credentials['engine']} database.")
    print("--------------------------------------------------\n")

    try:
        while True:
            line = ser.readline().decode("ascii", errors="replace").strip()
            if not line:
                continue

            try:
                msg = decode(line)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                mmsi = msg.mmsi
                lat = msg.lat
                lon = msg.lon
                speed = msg.speed

                name, image_url, nav_status, destination, eta = fetch_ship_details(mmsi)
                image_path = save_ship_image(mmsi, image_url) if image_url else None

                print(f"{timestamp} | MMSI {mmsi} - {name or 'Unknown'}")
                print(f"Position: ({lat}, {lon}) | Speed: {speed}")
                if destination:
                    print(f"Destination: {destination} | ETA: {eta}")
                if nav_status:
                    print(f"Navigation Status: {nav_status}")
                print("Image:", "Downloaded" if image_path else "Not available")

                cursor.execute(
                    """
                    INSERT INTO ships (
                        timestamp, mmsi, latitude, longitude, speed,
                        name, image_path, navigation_status, destination, eta
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (timestamp, mmsi, lat, lon, speed, name, image_path, nav_status, destination, eta)
                )
                conn.commit()
                print("Inserted into database.")
                print("--------------------------------------------------")

            except Exception as err:
                print(f"Error processing AIS message: {err}")
                print("--------------------------------------------------")

    except KeyboardInterrupt:
        print("\nStopping receiver...")

    finally:
        ser.close()
        cursor.close()
        conn.close()
        print("All connections closed. Receiver stopped.")


if __name__ == "__main__":
    main()
