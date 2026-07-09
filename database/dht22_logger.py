import time
import sys
import os

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "sensor"))

import board
import adafruit_dht
from db_manager import init_db, insert_reading, export_csv, get_stats

SENSOR_PIN = board.D4
dht = adafruit_dht.DHT22(SENSOR_PIN, use_pulseio=False)


def main():
    init_db()
    count = 0

    print("DHT22 + SQLite データ収集 開始 (Ctrl+C で停止・CSV出力)")
    try:
        while True:
            try:
                temp = dht.temperature
                hum = dht.humidity
                if temp is not None and hum is not None:
                    insert_reading(round(temp, 1), round(hum, 1))
                    count += 1
                    print(f"[{count:>4}] 気温: {temp:.1f} C  |  湿度: {hum:.1f} %  → 保存完了")
            except RuntimeError:
                pass
            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        dht.exit()
        stats = get_stats()
        print(f"\n===== 収集終了 =====")
        print(f"総データ数: {stats[0]} 件")
        print(f"温度 平均: {stats[1]}  最小: {stats[2]}  最大: {stats[3]} (C)")
        print(f"湿度 平均: {stats[4]}  最小: {stats[5]}  最大: {stats[6]} (%)")
        export_csv()


if __name__ == "__main__":
    main()
