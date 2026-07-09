import time
import json
import os
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT   = 1883
STATS_FILE = os.path.join(os.path.dirname(__file__), "system_stats.json")


def get_cpu_usage():
    with open("/proc/stat", "r") as f:
        line = f.readline()
    parts = line.split()
    total = sum(int(x) for x in parts[1:])
    idle = int(parts[4])
    return round((1.0 - idle / total) * 100, 1) if total > 0 else 0.0


def get_memory():
    mem = {}
    with open("/proc/meminfo", "r") as f:
        for line in f:
            if "MemTotal" in line:
                mem["total"] = int(line.split()[1])
            if "MemAvailable" in line:
                mem["available"] = int(line.split()[1])
                break
    used = mem.get("total", 1) - mem.get("available", 0)
    pct = round(used / mem.get("total", 1) * 100, 1)
    return pct


def get_disk():
    stat = os.statvfs("/")
    total = stat.f_blocks * stat.f_frsize
    free  = stat.f_bavail * stat.f_frsize
    used  = total - free
    return round(used / total * 100, 1) if total > 0 else 0.0


def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except FileNotFoundError:
        return None


def get_loadavg():
    with open("/proc/loadavg", "r") as f:
        parts = f.read().split()
        return round(float(parts[0]), 2)


def get_uptime():
    with open("/proc/uptime", "r") as f:
        seconds = float(f.read().split()[0])
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return f"{h}h {m}m"


def write_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    print("システムモニター 開始 (Ctrl+C で停止)")

    def pub(topic, value, unit):
        client.publish(topic, json.dumps({"value": value, "unit": unit}))

    try:
        while True:
            cpu = get_cpu_usage()
            mem = get_memory()
            disk = get_disk()
            temp = get_cpu_temp()
            loadavg = get_loadavg()
            uptime = get_uptime()

            pub("system/cpu", cpu, "%")
            pub("system/memory", mem, "%")
            pub("system/disk", disk, "%")
            if temp is not None:
                pub("system/cpu_temp", temp, "C")
            pub("system/loadavg", loadavg, "")

            write_stats({
                "cpu": cpu, "memory": mem, "disk": disk,
                "cpu_temp": temp, "loadavg": loadavg, "uptime": uptime
            })

            print(f"CPU:{cpu}% MEM:{mem}% DISK:{disk}% TEMP:{temp}C LOAD:{loadavg}")
            time.sleep(5)
    except KeyboardInterrupt:
        client.disconnect()
        print("停止しました")


if __name__ == "__main__":
    main()
