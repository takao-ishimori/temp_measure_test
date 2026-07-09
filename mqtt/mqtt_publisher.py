import time
import json
import board
import adafruit_dht
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

DHT_PIN   = board.D4
TRIG_PIN  = 23
ECHO_PIN  = 24
BROKER    = "localhost"
PORT      = 1883

dht = adafruit_dht.DHT22(DHT_PIN, use_pulseio=False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.output(TRIG_PIN, GPIO.LOW)


def measure_distance():
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    timeout = time.time() + 0.1
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.time() > timeout:
            return None
    pulse_start = time.time()

    timeout = time.time() + 0.1
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.time() > timeout:
            return None
    pulse_end = time.time()

    duration = pulse_end - pulse_start
    return round(duration * 17150, 1)


def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    print("MQTT パブリッシャー 開始 (Ctrl+C で停止)")
    print(f"ブローカー: {BROKER}:{PORT}")
    print("トピック: sensor/temperature, sensor/humidity, sensor/distance")

    try:
        while True:
            try:
                temp = dht.temperature
                hum  = dht.humidity
                if temp is not None and hum is not None:
                    temp = round(temp, 1)
                    hum  = round(hum, 1)
                    client.publish("sensor/temperature", json.dumps({
                        "value": temp, "unit": "C"
                    }))
                    client.publish("sensor/humidity", json.dumps({
                        "value": hum, "unit": "%"
                    }))
                    print(f"気温: {temp} C  |  湿度: {hum} %  → 送信完了")
            except RuntimeError:
                pass

            dist = measure_distance()
            if dist is not None and 0 < dist < 400:
                client.publish("sensor/distance", json.dumps({
                    "value": dist, "unit": "cm"
                }))
                print(f"距離: {dist} cm  → 送信完了")

            time.sleep(2.0)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        dht.exit()
        GPIO.cleanup()
        print("停止しました")


if __name__ == "__main__":
    main()
