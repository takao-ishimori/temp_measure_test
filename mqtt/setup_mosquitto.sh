#!/bin/bash
set -e
echo "Mosquitto MQTT ブローカー セットアップ"
sudo apt-get update
sudo apt-get install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto
echo "MQTT ブローカー稼働中 (ポート 1883)"
echo "確認: mosquitto_sub -t 'test' & mosquitto_pub -t 'test' -m 'hello'"
