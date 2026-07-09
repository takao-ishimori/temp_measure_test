#!/bin/bash
set -e

echo "===== Grafana セットアップ ====="

echo "[1/4] Grafana リポジトリを追加..."
sudo apt-get update
sudo apt-get install -y software-properties-common wget
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

echo "[2/4] Grafana インストール..."
sudo apt-get update
sudo apt-get install -y grafana

echo "[3/4] Grafana 起動..."
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

echo "[4/4] プラグインインストール..."
sudo grafana-cli plugins install yesoreyeram-infinity-datasource
sudo systemctl restart grafana-server

echo ""
echo "===== セットアップ完了 ====="
echo "Grafana: http://localhost:3000  (ID: admin / PW: admin)"
echo ""
echo "次にやること:"
echo "  1. ブラウザで http://ラズパイのIP:3000 を開く"
echo "  2. ログイン (admin / admin)"
echo "  3. データAPIを起動: python monitoring/data_api.py &"
