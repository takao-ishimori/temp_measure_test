import json
import sys
import os
import paho.mqtt.client as mqtt

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))
from db_manager import init_db, insert_reading

BROKER = "localhost"
PORT   = 1883

count = 0


def on_connect(client, userdata, flags, rc):
    print(f"MQTT ブローカーに接続 (rc={rc})")
    client.subscribe("sensor/temperature")
    client.subscribe("sensor/humidity")
    client.subscribe("sensor/distance")


def on_message(client, userdata, msg):
    global count
    topic = msg.topic
    payload = json.loads(msg.payload.decode("utf-8"))
    value = payload["value"]
    unit = payload["unit"]

    count += 1
    print(f"[{count:>4}] {topic} = {value} {unit}")

    if topic == "sensor/temperature":
        userdata["temp"] = value
    elif topic == "sensor/humidity":
        userdata["hum"] = value

    if userdata["temp"] is not None and userdata["hum"] is not None:
        insert_reading(userdata["temp"], userdata["hum"])
        print(f"          → DB保存完了 ({userdata['temp']} C, {userdata['hum']} %)")
        userdata["temp"] = None
        userdata["hum"] = None


def main():
    init_db()
    userdata = {"temp": None, "hum": None}

    client = mqtt.Client(userdata=userdata)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    print(f"MQTT サブスクライバー 開始 (Ctrl+C で停止)")
    print(f"ブローカー: {BROKER}:{PORT}")

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        client.disconnect()
        print("停止しました")


if __name__ == "__main__":
    main()
