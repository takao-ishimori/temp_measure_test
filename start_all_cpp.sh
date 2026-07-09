#!/bin/bash
set -e

BASE="$(cd "$(dirname "$0")" && pwd)"
IP=$(hostname -I | awk '{print $1}')

echo "===== temp_measure 一括起動 (C++版) ====="
echo ""

echo "既存プロセスを停止中..."
pkill -f mqtt_publisher 2>/dev/null || true
pkill -f mqtt_subscriber 2>/dev/null || true
pkill -f dashboard_server 2>/dev/null || true
pkill -f system_monitor 2>/dev/null || true
sleep 1

echo "[1/5] C++ バイナリ ビルド..."
cd "$BASE/mqtt"
g++ -std=c++11 -o mqtt_pub mqtt_publisher.cpp -lwiringPi -lmosquitto
g++ -std=c++11 -o mqtt_sub mqtt_subscriber.cpp ../database/db_manager.cpp \
    -lmosquitto -lsqlite3 -I../database -lm
cd "$BASE"

echo "[2/5] MQTT受信(DB保存) C++版 起動..."
sudo "$BASE/mqtt/mqtt_sub" &
sleep 0.5

echo "[3/5] MQTT送信(センサー) C++版 起動..."
sudo "$BASE/mqtt/mqtt_pub" &
sleep 0.5

echo "[4/5] システムモニター 起動..."
python "$BASE/monitoring/system_monitor.py" &
sleep 0.5

echo "[5/5] ダッシュボード 起動..."
python "$BASE/monitoring/dashboard_server.py" &
sleep 0.5

echo ""
echo "ダッシュボード: http://${IP}:8080/dashboard"
echo "Zabbix:         http://${IP}/zabbix"
echo "Ctrl+C で一括停止"
echo ""

cleanup() {
    echo ""
    echo "停止中..."
    sudo pkill -9 -f mqtt_sub 2>/dev/null || true
    sudo pkill -9 -f mqtt_pub 2>/dev/null || true
    pkill -9 -f system_monitor 2>/dev/null || true
    pkill -9 -f dashboard_server 2>/dev/null || true
    sudo fuser -k 1883/tcp 2>/dev/null || true
    sudo fuser -k 8080/tcp 2>/dev/null || true
    echo "すべてのプロセスを停止しました"
    exit 0
}

trap cleanup SIGINT SIGTERM

while true; do
    sleep 1
done
