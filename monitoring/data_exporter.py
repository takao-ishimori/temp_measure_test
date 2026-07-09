import sqlite3
import json
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "dht22_data.db")
OUT_PATH = os.path.join(os.path.dirname(__file__), "data.json")


def export_json():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, temperature_c, humidity_pct "
        "FROM dht22_readings ORDER BY id DESC LIMIT 100"
    ).fetchall()
    conn.close()

    data = [
        {"id": r[0], "timestamp": r[1], "temperature_c": r[2], "humidity_pct": r[3]}
        for r in rows
    ]

    with open(OUT_PATH, "w") as f:
        json.dump(data, f)
    print(f"JSON出力: {len(data)} 件 → {OUT_PATH}")


def main():
    print("データエクスポート開始 (Ctrl+C で停止)")
    try:
        while True:
            export_json()
            time.sleep(5)
    except KeyboardInterrupt:
        print("停止しました")


if __name__ == "__main__":
    main()
