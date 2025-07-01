import os
import json

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")

def load_credentials():
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError("Database credentials file not found.")

    with open(CREDENTIALS_PATH, "r") as f:
        return json.load(f)

# ------- Table Definition -------
SHIP_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS ships (
        id {id_type} PRIMARY KEY,
        timestamp {timestamp_type},
        mmsi BIGINT,
        latitude {latlon_type},
        longitude {latlon_type},
        speed {speed_type},
        image_path TEXT,
        name TEXT,
        destination TEXT,
        eta TEXT,
        navigation_status TEXT
    );
"""

# ------- Setup Database Function -------
def setup_database(config):
    """
    Create a connection to the database and initialize the ships table.
    
    Supported engines: 'postgresql', 'mysql'
    """
    try:
        engine = config.get("engine")
        
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

            cur.execute(SHIP_TABLE_SQL.format(
                id_type="SERIAL",
                timestamp_type="TIMESTAMP",
                latlon_type="NUMERIC(9,6)",
                speed_type="NUMERIC(5,2)"
            ))

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

            cur.execute(SHIP_TABLE_SQL.format(
                id_type="INT AUTO_INCREMENT",
                timestamp_type="DATETIME",
                latlon_type="DECIMAL(9,6)",
                speed_type="DECIMAL(5,2)"
            ))

            conn.commit()
            cur.close()
            conn.close()

            return True, "MySQL: Connected and table 'ships' created."

        else:
            return False, f"Unsupported database engine: '{engine}'"

    except Exception as e:
        return False, str(e)
