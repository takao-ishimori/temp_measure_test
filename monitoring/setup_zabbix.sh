#!/bin/bash
set -e

echo "===== Zabbix 6.0 LTS セットアップ (Raspberry Pi) ====="

echo "[1/4] Zabbix リポジトリ追加..."
wget -q https://repo.zabbix.com/zabbix/6.0/raspbian/pool/main/z/zabbix-release/zabbix-release_6.0-4+debian11_all.deb
sudo dpkg -i zabbix-release_6.0-4+debian11_all.deb
sudo apt-get update

echo "[2/4] Zabbix サーバー + エージェント + Web インストール..."
sudo apt-get install -y zabbix-server-mysql zabbix-frontend-php zabbix-agent mariadb-server

echo "[3/4] MariaDB 設定..."
sudo systemctl start mariadb
sudo mysql -e "CREATE DATABASE IF NOT EXISTS zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'zabbix'@'localhost' IDENTIFIED BY 'zabbix_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | sudo mysql zabbix

echo "[4/4] Zabbix 設定反映..."
sudo sed -i 's/# DBPassword=/DBPassword=zabbix_pass/' /etc/zabbix/zabbix_server.conf
sudo sed -i 's|# php_value date.timezone Europe/Riga|php_value date.timezone Asia/Tokyo|' /etc/apache2/conf-available/zabbix-frontend-php.conf

sudo systemctl restart zabbix-server zabbix-agent apache2
sudo systemctl enable zabbix-server zabbix-agent apache2

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "===== Zabbix セットアップ完了 ====="
echo "Web画面: http://${IP}/zabbix"
echo "初期設定: Next → Next → パスワード zabbix_pass → Next → Finish"
echo "ログイン: Admin / zabbix"
