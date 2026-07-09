import subprocess
import signal
import sys
import time
import os
import socket

BASE = os.path.dirname(os.path.abspath(__file__))

procs = [
    {"name": "MQTT受信(DB保存)",   "cmd": [sys.executable, os.path.join(BASE, "mqtt", "mqtt_subscriber.py")]},
    {"name": "MQTT送信(センサー)", "cmd": [sys.executable, os.path.join(BASE, "mqtt", "mqtt_publisher.py")]},
    {"name": "システムモニター",    "cmd": [sys.executable, os.path.join(BASE, "monitoring", "system_monitor.py")]},
    {"name": "ダッシュボード",      "cmd": [sys.executable, os.path.join(BASE, "monitoring", "dashboard_server.py")]},
]

children = []


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "localhost"


def cleanup_old():
    for p in procs:
        name = os.path.basename(p["cmd"][-1])
        os.system(f"pkill -f {name} 2>/dev/null")
    time.sleep(0.5)


def start_all():
    for p in procs:
        proc = subprocess.Popen(p["cmd"])
        children.append((p["name"], proc))
        print(f"  [起動] {p['name']}")
        time.sleep(0.5)


def stop_all():
    print("\n停止中...")
    for name, proc in children:
        proc.terminate()
        print(f"  [停止] {name}")
    for name, proc in children:
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
    children.clear()


def signal_handler(sig, frame):
    stop_all()
    sys.exit(0)


def main():
    os.chdir(BASE)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("===== temp_measure 一括起動 =====\n")
    print("既存プロセスを停止中...")
    cleanup_old()

    start_all()

    ip = get_ip()
    print(f"\nダッシュボード: http://{ip}:8080/dashboard")
    print("Ctrl+C で一括停止\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop_all()
        print("すべてのプロセスを停止しました")


if __name__ == "__main__":
    main()
