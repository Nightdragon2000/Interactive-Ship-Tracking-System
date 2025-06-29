import os
import json

def load_credentials():
    path = os.path.join(os.path.dirname(__file__), "credentials.json")
    if not os.path.exists(path):
        raise FileNotFoundError("Database credentials file not found.")
    with open(path, "r") as f:
        return json.load(f)

def setup_database(config):
    try:
        engine = config["engine"]
        if engine == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                dbname=config["database"],
                user=config["user"],
                password=config["password"],
                host=config["host"],
                port=config["port"]
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ships (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP,
                    mmsi BIGINT,
                    latitude NUMERIC(9,6),
                    longitude NUMERIC(9,6),
                    speed NUMERIC(5,2),
                    image_path TEXT,
                    name TEXT,
                    destination TEXT,
                    eta TEXT,
                    navigation_status TEXT
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            return True, "PostgreSQL: Connected and table 'ships' created."

        elif engine == "mysql":
            import mysql.connector
            conn = mysql.connector.connect(
                host=config["host"],
                port=config["port"],
                user=config["user"],
                password=config["password"],
                database=config["database"]
            )
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ships (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME,
                    mmsi BIGINT,
                    latitude DECIMAL(9,6),
                    longitude DECIMAL(9,6),
                    speed DECIMAL(5,2),
                    image_path TEXT,
                    name TEXT,
                    destination TEXT,
                    eta TEXT,
                    navigation_status TEXT
                );
            """)
            conn.commit()
            cur.close()
            conn.close()
            return True, "MySQL: Connected and table 'ships' created."

        else:
            return False, f"Unsupported engine: {engine}"

    except Exception as e:
        return False, str(e)
