import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "dht22_data.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def insert_reading(temperature_c, humidity_pct):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO dht22_readings (temperature_c, humidity_pct) VALUES (?, ?)",
        (temperature_c, humidity_pct),
    )
    conn.commit()
    conn.close()


def get_all_readings():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, temperature_c, humidity_pct FROM dht22_readings ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def export_csv(output_path="dht22_export.csv"):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, temperature_c, humidity_pct FROM dht22_readings ORDER BY id"
    ).fetchall()
    conn.close()

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "timestamp", "temperature_c", "humidity_pct"])
        writer.writerows(rows)

    print(f"CSV出力完了: {output_path}  ({len(rows)} 件)")


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        """
        SELECT
            COUNT(*),
            ROUND(AVG(temperature_c), 2),
            ROUND(MIN(temperature_c), 2),
            ROUND(MAX(temperature_c), 2),
            ROUND(AVG(humidity_pct), 2),
            ROUND(MIN(humidity_pct), 2),
            ROUND(MAX(humidity_pct), 2)
        FROM dht22_readings
        """
    ).fetchone()
    conn.close()
    return row
