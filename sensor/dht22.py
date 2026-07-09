import time
import board
import adafruit_dht

SENSOR_PIN = board.D4

dht = adafruit_dht.DHT22(SENSOR_PIN, use_pulseio=False)


def read_dht22():
    try:
        temperature = dht.temperature
        humidity = dht.humidity
        if temperature is not None and humidity is not None:
            return {"temperature_c": round(temperature, 1), "humidity_pct": round(humidity, 1)}
    except RuntimeError as e:
        pass
    return None


def main():
    print("DHT22 温湿度センサー 読み取り開始 (Ctrl+C で停止)")
    try:
        while True:
            result = read_dht22()
            if result:
                print(f"気温: {result['temperature_c']} C  |  湿度: {result['humidity_pct']} %")
            else:
                print("読み取り失敗（リトライ中...）")
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("\n停止しました")
    finally:
        dht.exit()


if __name__ == "__main__":
    main()
