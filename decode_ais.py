import serial
from pyais import decode
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os
from database.db_setup import load_credentials


# Configure the serial connection
serial_port = "COM5"
baud_rate = 4800

# Open the serial connection
ser = serial.Serial(serial_port, baud_rate, timeout=2)

# Load credentials from credentials.json
credentials = load_credentials()
engine = credentials["engine"]

# Connect to the appropriate database
if engine == "postgresql":
    import psycopg2
    conn = psycopg2.connect(
        host=credentials["host"],
        database=credentials["database"],
        user=credentials["user"],
        password=credentials["password"],
        port=credentials["port"]
    )
    cursor = conn.cursor()

elif engine == "mysql":
    import mysql.connector
    conn = mysql.connector.connect(
        host=credentials["host"],
        database=credentials["database"],
        user=credentials["user"],
        password=credentials["password"],
        port=int(credentials["port"])
    )
    cursor = conn.cursor()

else:
    raise ValueError("Unsupported database engine: must be 'postgresql' or 'mysql'.")

print(f"Connected to {engine} database.")

try:
    while True:
        line = ser.readline().decode("ascii", errors="replace").strip()

        if line:
            try:
                ais_message = decode(line)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                mmsi = ais_message.mmsi
                lat = ais_message.lat
                lon = ais_message.lon
                speed = ais_message.speed

                url = f'https://www.vesselfinder.com/vessels/details/{mmsi}'
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://www.google.com/',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                }

                response = requests.get(url, headers=headers)
                soup = BeautifulSoup(response.content, 'html.parser')

                ship_name = None
                ship_image_url = None
                navigation_status = None
                destination = None
                eta = None

                ship_info_div = soup.find('div', class_='col vfix-top npr')
                if ship_info_div:
                    img_tag = ship_info_div.find('img', class_='main-photo')
                    if img_tag:
                        ship_name = img_tag.get('title', '').strip()
                        ship_image_url = img_tag.get('src', '')

                nav_status_div = soup.select_one('body > div.body-wrapper > div > main > div > section:nth-child(4) > div > div.col.vfix-top.lpr > div > div.flx > table.aparams')
                if nav_status_div:
                    for tr in nav_status_div.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > 1 and tds[0].text.strip() == 'Navigation Status':
                            span_tag = tds[1].find('span')
                            if span_tag:
                                navigation_status = span_tag.text.strip()
                            break

                vi_r1_div = soup.find('div', class_='vi__r1 vi__sbt')
                if vi_r1_div:
                    a_tag = vi_r1_div.find('a', class_='_npNa')
                    if a_tag:
                        destination = a_tag.text.split(',')[0].strip()
                    value_div = vi_r1_div.find('div', class_='_value')
                    if value_div:
                        span_tag = value_div.find('span')
                        if span_tag:
                            eta = span_tag.text.strip().split(':', 1)[-1].strip()

                image_path = None
                if ship_image_url:
                    image_response = requests.get(ship_image_url, stream=True)
                    if image_response.status_code == 200:
                        image_dir = './Images/Ships_MMSI'
                        os.makedirs(image_dir, exist_ok=True)
                        image_path = os.path.join(image_dir, f'{mmsi}.jpg')
                        with open(image_path, 'wb') as image_file:
                            for chunk in image_response.iter_content(1024):
                                image_file.write(chunk)

                insert_values = (timestamp, mmsi, lat, lon, speed, ship_name, image_path, navigation_status, destination, eta)
                print("🚢 Inserting into DB:", insert_values)

                cursor.execute(
                    """
                    INSERT INTO ships (timestamp, mmsi, latitude, longitude, speed, name, image_path, navigation_status, destination, eta) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    insert_values
                )
                conn.commit()

            except Exception as e:
                print(f"❌ Failed to decode or insert message: {line}")
                print(f"Error: {e}")

except KeyboardInterrupt:
    print("🛑 Script interrupted by user.")

finally:
    ser.close()
    print("Serial port closed.")
    cursor.close()
    conn.close()
    print(f"{engine.capitalize()} connection closed.")
