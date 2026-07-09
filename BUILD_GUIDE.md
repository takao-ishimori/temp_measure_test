# temp_measure 完全構築手順書

Raspberry Pi ゼロ状態から全機能構築までの全手順を記録。

---

## 0. 初期環境

| 項目 | 値 |
|------|-----|
| ハード | Raspberry Pi 4 Model B |
| OS | Raspberry Pi OS (Debian 11 Bullseye) |
| PC接続 | VSCode Remote-SSH (WiFi経由) |
| ユーザー | t.i |
| IP | 192.168.40.183 |

```bash
# SSH有効化（ラズパイ側）
sudo raspi-config
# → Interface Options → SSH → Enable

# IP確認
hostname -I
```

```bash
# PC側 VSCode
# 拡張機能: Remote-SSH をインストール
# 左下 >< → Connect to Host → ssh t.i@192.168.40.183
```

---

## 1. DHT22 温湿度センサー

### 1.1 配線（3ピンモジュール・抵抗内蔵）

```
DHT22       Raspberry Pi
VCC   →     3.3V (ピン1)
S     →     GPIO4 (ピン7)
GND   →     GND  (ピン6)
```

### 1.2 Python版

```bash
pip install adafruit-circuitpython-dht

# sensor/dht22.py を実行
python sensor/dht22.py
```

```python
# sensor/dht22.py
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
    except RuntimeError:
        pass
    return None

def main():
    print("DHT22 読み取り開始 (Ctrl+C で停止)")
    try:
        while True:
            result = read_dht22()
            if result:
                print(f"気温: {result['temperature_c']} C | 湿度: {result['humidity_pct']} %")
            time.sleep(2.0)
    except KeyboardInterrupt:
        print("停止")
    finally:
        dht.exit()

if __name__ == "__main__":
    main()
```

### 1.3 C++版

```bash
# wiringPi インストール
git clone https://github.com/WiringPi/WiringPi.git
cd WiringPi
./build

# コンパイル
g++ -std=c++11 -o dht22 sensor/dht22.cpp -lwiringPi

# 実行
sudo ./dht22
```

```cpp
// sensor/dht22.cpp
#include <wiringPi.h>
#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

#define DHT22_PIN 7

static int dht22_data[5] = {0};

static int read_dht22_raw(void)
{
    uint8_t last_state = HIGH;
    uint8_t counter = 0, j = 0;
    pinMode(DHT22_PIN, OUTPUT);
    digitalWrite(DHT22_PIN, LOW);
    delay(18);
    digitalWrite(DHT22_PIN, HIGH);
    delayMicroseconds(40);
    pinMode(DHT22_PIN, INPUT);

    for (int i = 0; i < 85; i++) {
        counter = 0;
        while (digitalRead(DHT22_PIN) == last_state) {
            counter++;
            delayMicroseconds(1);
            if (counter == 255) break;
        }
        last_state = digitalRead(DHT22_PIN);
        if (counter == 255) break;
        if ((i >= 4) && (i % 2 == 0)) {
            dht22_data[j / 8] <<= 1;
            if (counter > 16) dht22_data[j / 8] |= 1;
            j++;
        }
    }
    if (j >= 40 && dht22_data[4] == ((dht22_data[0] + dht22_data[1] + dht22_data[2] + dht22_data[3]) & 0xFF))
        return 1;
    return 0;
}

int dht22_read(float *temperature, float *humidity)
{
    if (!read_dht22_raw()) return 0;
    *humidity    = (float)((dht22_data[0] << 8) + dht22_data[1]) / 10.0f;
    *temperature = (float)(((dht22_data[2] & 0x7F) << 8) + dht22_data[3]) / 10.0f;
    if (dht22_data[2] & 0x80) *temperature = -(*temperature);
    return 1;
}

int main()
{
    if (wiringPiSetup() == -1) { printf("wiringPi err\n"); return 1; }
    printf("DHT22 開始 (Ctrl+C)\n");
    float t, h;
    for (;;) {
        if (dht22_read(&t, &h))
            printf("気温: %.1f C | 湿度: %.1f %%\n", t, h);
        delay(2000);
    }
}
```

---

## 2. HC-SR04 超音波距離センサー

### 2.1 配線（ECHOは分圧必須）

```
HC-SR04            Raspberry Pi
VCC   ──────────── 5V   (ピン4)
TRIG  ──────────── GPIO23 (ピン16)
ECHO  ─┬─[1kΩ]─┬── GPIO24 (ピン18)
       │        │
       └──[2kΩ]─┘
                 │
GND   ─────────── GND  (ピン6)
```

### 2.2 Python版

```bash
# RPi.GPIO は標準で入っている
python sensor/hc_sr04.py
```

```python
# sensor/hc_sr04.py
import time
import RPi.GPIO as GPIO

TRIG_PIN, ECHO_PIN = 23, 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.output(TRIG_PIN, GPIO.LOW)
time.sleep(0.1)

def measure_distance():
    GPIO.output(TRIG_PIN, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, GPIO.LOW)

    timeout = time.time() + 0.1
    while GPIO.input(ECHO_PIN) == GPIO.LOW:
        if time.time() > timeout: return None
    pulse_start = time.time()
    timeout = time.time() + 0.1
    while GPIO.input(ECHO_PIN) == GPIO.HIGH:
        if time.time() > timeout: return None
    pulse_end = time.time()
    return round((pulse_end - pulse_start) * 17150, 1)

def main():
    print("HC-SR04 開始 (Ctrl+C)")
    try:
        while True:
            dist = measure_distance()
            if dist: print(f"距離: {dist} cm")
            time.sleep(0.5)
    except KeyboardInterrupt:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
```

### 2.3 C++版

```bash
g++ -std=c++11 -o hc_sr04 sensor/hc_sr04.cpp -lwiringPi
sudo ./hc_sr04
```

---

## 3. SQLite データベース

### 3.1 スキーマ定義

```sql
-- database/schema.sql
CREATE TABLE IF NOT EXISTS dht22_readings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    temperature_c REAL    NOT NULL,
    humidity_pct  REAL    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_timestamp ON dht22_readings(timestamp);
```

### 3.2 Python版 DBマネージャー

```bash
# SQLite3 は標準ライブラリ
python database/dht22_logger.py
```

```python
# database/db_manager.py
import sqlite3, csv, os

DB_PATH = os.path.join(os.path.dirname(__file__), "dht22_data.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit(); conn.close()

def insert_reading(temperature_c, humidity_pct):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO dht22_readings (temperature_c, humidity_pct) VALUES (?, ?)",
                 (temperature_c, humidity_pct))
    conn.commit(); conn.close()

def get_all_readings():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, timestamp, temperature_c, humidity_pct FROM dht22_readings ORDER BY id").fetchall()
    conn.close(); return rows

def export_csv(output_path="dht22_export.csv"):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT id, timestamp, temperature_c, humidity_pct FROM dht22_readings ORDER BY id").fetchall()
    conn.close()
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "timestamp", "temperature_c", "humidity_pct"])
        writer.writerows(rows)
    print(f"CSV出力: {output_path} ({len(rows)}件)")

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT COUNT(*), ROUND(AVG(temperature_c),2), ROUND(MIN(temperature_c),2), ROUND(MAX(temperature_c),2), ROUND(AVG(humidity_pct),2) FROM dht22_readings").fetchone()
    conn.close(); return row
```

### 3.3 C++版 DBマネージャー

```bash
sudo apt-get install -y libsqlite3-dev
g++ -std=c++11 -o dht22_logger database/dht22_logger.cpp database/db_manager.cpp -lwiringPi -lsqlite3
sudo ./dht22_logger
```

```cpp
// database/db_manager.h
#ifndef DB_MANAGER_H
#define DB_MANAGER_H
#ifdef __cplusplus
extern "C" {
#endif
int  db_init(void);
int  db_insert(float temperature_c, float humidity_pct);
int  db_count(void);
void db_stats(void);
void db_export_csv(const char *filename);
void db_close(void);
#ifdef __cplusplus
}
#endif
#endif
```

```cpp
// database/db_manager.cpp
#include "db_manager.h"
#include <sqlite3.h>
#include <stdio.h>
#include <math.h>

static sqlite3 *db = NULL;

int db_init(void) {
    sqlite3_open("dht22_data.db", &db);
    const char *sql = "CREATE TABLE IF NOT EXISTS dht22_readings (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL DEFAULT (datetime('now','localtime')), temperature_c REAL NOT NULL, humidity_pct REAL NOT NULL);";
    sqlite3_exec(db, sql, NULL, NULL, NULL);
    return 1;
}

int db_insert(float t, float h) {
    float tr = roundf(t * 10) / 10;
    float hr = roundf(h * 10) / 10;
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db, "INSERT INTO dht22_readings (temperature_c, humidity_pct) VALUES (?,?)", -1, &stmt, NULL);
    sqlite3_bind_double(stmt, 1, tr);
    sqlite3_bind_double(stmt, 2, hr);
    sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return 1;
}

int db_count(void) {
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db, "SELECT COUNT(*) FROM dht22_readings", -1, &stmt, NULL);
    sqlite3_step(stmt);
    int c = sqlite3_column_int(stmt, 0);
    sqlite3_finalize(stmt);
    return c;
}

void db_stats(void) {
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db, "SELECT AVG(temperature_c), MIN(temperature_c), MAX(temperature_c), AVG(humidity_pct) FROM dht22_readings", -1, &stmt, NULL);
    if (sqlite3_step(stmt) == SQLITE_ROW)
        printf("温度 平均:%.2f 最小:%.2f 最大:%.2f\n湿度 平均:%.2f\n",
               sqlite3_column_double(stmt,0), sqlite3_column_double(stmt,1),
               sqlite3_column_double(stmt,2), sqlite3_column_double(stmt,3));
    sqlite3_finalize(stmt);
}

void db_export_csv(const char *filename) {
    FILE *fp = fopen(filename, "w");
    fprintf(fp, "id,timestamp,temperature_c,humidity_pct\n");
    sqlite3_stmt *stmt;
    sqlite3_prepare_v2(db, "SELECT id,timestamp,temperature_c,humidity_pct FROM dht22_readings ORDER BY id", -1, &stmt, NULL);
    int count = 0;
    while (sqlite3_step(stmt) == SQLITE_ROW) {
        fprintf(fp, "%d,%s,%.1f,%.1f\n",
                sqlite3_column_int(stmt,0), sqlite3_column_text(stmt,1),
                sqlite3_column_double(stmt,2), sqlite3_column_double(stmt,3));
        count++;
    }
    sqlite3_finalize(stmt);
    fclose(fp);
    printf("CSV出力: %s (%d件)\n", filename, count);
}

void db_close(void) { if (db) sqlite3_close(db); }
```

### 3.4 データ確認コマンド

```bash
# SQLite CLI インストール
sudo apt-get install -y sqlite3

# 最新10件表示
sqlite3 ~/database/dht22_data.db "SELECT * FROM dht22_readings ORDER BY id DESC LIMIT 10;"

# CSV内容確認
head -10 ~/dht22_export.csv
```

---

## 4. MQTT 通信

### 4.1 Mosquitto ブローカー構築

```bash
sudo apt-get install -y mosquitto mosquitto-clients
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# 動作確認
mosquitto_sub -t "test" &
mosquitto_pub -t "test" -m "hello"
pkill mosquitto_sub
```

### 4.2 Python パブリッシャー

```bash
pip install paho-mqtt
python mqtt/mqtt_publisher.py
```

```python
# mqtt/mqtt_publisher.py - DHT22 + HC-SR04 → MQTT
import time, json, board, adafruit_dht, RPi.GPIO as GPIO, paho.mqtt.client as mqtt

BROKER, PORT = "localhost", 1883
dht = adafruit_dht.DHT22(board.D4, use_pulseio=False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.OUT); GPIO.setup(24, GPIO.IN)

def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    try:
        while True:
            try:
                t, h = dht.temperature, dht.humidity
                if t and h:
                    client.publish("sensor/temperature", json.dumps({"value": round(t,1), "unit": "C"}))
                    client.publish("sensor/humidity", json.dumps({"value": round(h,1), "unit": "%"}))
            except RuntimeError: pass
            # HC-SR04
            GPIO.output(23, GPIO.HIGH); time.sleep(0.00001); GPIO.output(23, GPIO.LOW)
            t0 = time.time()
            while GPIO.input(24) == GPIO.LOW:
                if time.time() - t0 > 0.1: break
            t1 = time.time()
            while GPIO.input(24) == GPIO.HIGH:
                if time.time() - t0 > 0.2: break
            t2 = time.time()
            dist = round((t2 - t1) * 17150, 1)
            if 0 < dist < 400:
                client.publish("sensor/distance", json.dumps({"value": dist, "unit": "cm"}))
            time.sleep(2)
    except KeyboardInterrupt: pass
    finally: client.loop_stop(); client.disconnect(); dht.exit(); GPIO.cleanup()

if __name__ == "__main__": main()
```

### 4.3 Python サブスクライバー（MQTT → DB保存）

```bash
python mqtt/mqtt_subscriber.py
```

```python
# mqtt/mqtt_subscriber.py - MQTT → SQLite
import json, sys, os, paho.mqtt.client as mqtt
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))
from db_manager import init_db, insert_reading

BROKER, PORT = "localhost", 1883

def on_connect(client, userdata, flags, rc):
    client.subscribe("sensor/temperature")
    client.subscribe("sensor/humidity")
    client.subscribe("sensor/distance")

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload.decode())
    value = payload["value"]
    print(f"{msg.topic} = {value} {payload['unit']}")
    if msg.topic == "sensor/temperature":
        userdata["temp"] = value
    elif msg.topic == "sensor/humidity":
        userdata["hum"] = value
    if userdata["temp"] is not None and userdata["hum"] is not None:
        insert_reading(userdata["temp"], userdata["hum"])
        userdata["temp"] = None; userdata["hum"] = None

def main():
    init_db()
    client = mqtt.Client(userdata={"temp": None, "hum": None})
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    try: client.loop_forever()
    except KeyboardInterrupt: client.disconnect()

if __name__ == "__main__": main()
```

### 4.4 C++ パブリッシャー

```bash
sudo apt-get install -y libmosquitto-dev
g++ -std=c++11 -o mqtt_pub mqtt/mqtt_publisher.cpp -lwiringPi -lmosquitto
sudo ./mqtt_pub
```

### 4.5 C++ サブスクライバー

```bash
g++ -std=c++11 -o mqtt_sub mqtt/mqtt_subscriber.cpp database/db_manager.cpp \
    -lmosquitto -lsqlite3 -ldatabase
sudo ./mqtt_sub
```

---

## 5. 統計分析

```bash
sudo apt-get install -y libopenblas-dev python3-scipy python3-matplotlib fonts-noto-cjk
pip install 'numpy<2' scipy matplotlib

python analytics/stats_analysis.py
```

**分析結果（実測値）**

```
===== Welchのt検定 =====
前半 vs 後半: t=-2.5033, p=0.0135 → 有意差あり

===== Pearson相関 =====
温度 vs 湿度: r=-0.6254, p=0.0006 → 有意な負の相関
```

---

## 6. Web ダッシュボード

```bash
python monitoring/dashboard_server.py &

# ブラウザで開く
http://192.168.40.183:8080/dashboard
```

### 表示内容
- 温度・湿度 リアルタイム時系列グラフ (Chart.js)
- 現在値・件数・最高/最低 統計カード
- CPU使用率・メモリ・ディスク・CPU温度・負荷平均・稼働時間
- 5秒おき自動更新

---

## 7. システムモニター（MQTT経由）

```bash
python monitoring/system_monitor.py &
```

Raspberry Pi の `/proc/stat`, `/proc/meminfo`, `/sys/class/thermal/thermal_zone0/temp` からシステム状態を取得し、MQTT経由でダッシュボードに表示。

---

## 8. Zabbix 6.0 LTS 構築

```bash
# Zabbix リポジトリ
wget https://repo.zabbix.com/zabbix/6.0/raspbian/pool/main/z/zabbix-release/zabbix-release_6.0-4+debian11_all.deb
sudo dpkg -i zabbix-release_6.0-4+debian11_all.deb
sudo apt-get update

# インストール
sudo apt-get install -y zabbix-server-mysql zabbix-frontend-php zabbix-agent \
    mariadb-server php libapache2-mod-php php-mysql php-gd php-xml

# DB設定
sudo mysql -e "CREATE DATABASE zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;"
sudo mysql -e "CREATE USER 'zabbix'@'localhost' IDENTIFIED BY 'zabbix_pass';"
sudo mysql -e "GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost'; FLUSH PRIVILEGES;"
zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz | sudo mysql zabbix

# Apache設定
sudo tee /etc/apache2/conf-available/zabbix-frontend-php.conf << 'EOF'
Alias /zabbix /usr/share/zabbix
<Directory /usr/share/zabbix>
    Options FollowSymLinks; AllowOverride All; Require all granted
</Directory>
<Directory /usr/share/zabbix/conf>
    Require all denied
</Directory>
EOF
sudo a2enconf zabbix-frontend-php

# PHP設定
PHP_INI=/etc/php/7.4/apache2/php.ini
sudo sed -i 's/^post_max_size = .*/post_max_size = 16M/' $PHP_INI
sudo sed -i 's/^max_execution_time = .*/max_execution_time = 300/' $PHP_INI
sudo sed -i 's/^max_input_time = .*/max_input_time = 300/' $PHP_INI

# Zabbix DBパスワード設定
sudo sed -i 's/# DBPassword=/DBPassword=zabbix_pass/' /etc/zabbix/zabbix_server.conf

# PHPタイムゾーン
sudo sed -i 's|;date.timezone =|date.timezone = Asia/Tokyo|' $PHP_INI

# 全サービス再起動
sudo systemctl restart mariadb zabbix-server zabbix-agent apache2
sudo systemctl enable zabbix-server zabbix-agent apache2

# アクセス
# http://192.168.40.183/zabbix  (Admin / zabbix)
```

### Zabbix トラブルシュート

```bash
# ログインできない場合
sudo mysql -e "USE zabbix; UPDATE users SET passwd='5fce1b3e34b520afeffb37ce08c7cd66', attempt_failed=0, attempt_clock=0 WHERE username='Admin';"

# デフォルトパスワードにリセット → Admin / zabbix
```

---

## 9. 一括起動スクリプト

```bash
python start_all.py
```

**起動する4プロセス**
1. MQTT サブスクライバー（DB保存）
2. MQTT パブリッシャー（センサー読み取り）
3. システムモニター（CPU/メモリ/ディスク）
4. Web ダッシュボードサーバー

**Ctrl+C で4プロセス一括停止**

---

## 10. プロジェクト構成（最終形）

```
~/temp_measure/
├── README.md
├── TEST_SHEET.md
├── AI_RULES.md
├── start_all.py
├── sensor/          # DHT22 + HC-SR04 (Python / C++)
├── mqtt/            # Mosquitto 連携 (Python / C++)
├── database/        # SQLite + CSV (Python / C++)
├── monitoring/      # ダッシュボード + システム監視 + Zabbix
├── analytics/       # 統計分析 (t検定・相関)
└── opencv/          # アナログ温度計読み取り (開発中)
```

---

## 11. テストシート

```bash
# テスト仕様書
cat TEST_SHEET.md
```

| No | テスト項目 | 結果 |
|----|-----------|------|
| T01 | センサー接続確認 | 合格 |
| T02 | 温度読み取り (10回) | 合格 |
| T03 | 湿度読み取り (10回) | 合格 |
| T04 | 5分連続動作 | 未実施 |
| T05 | エラー耐性 | 未実施 |
| T06 | 温度変化検出 (指で温め) | 合格 |
| T07 | Python/C++ 結果比較 | 合格 |

---

## 12. 技術スタック一覧

| 層 | 技術 | 言語 |
|----|------|------|
| センサー | GPIO, DHT22, HC-SR04 | Python / C++ |
| 通信 | MQTT (Mosquitto) | Python / C++ |
| データ | SQLite, CSV | SQL, Python / C++ |
| 統計 | t検定, Pearson相関, 記述統計 | Python (scipy) |
| 可視化 | Chart.js ダッシュボード | HTML/JS |
| 監視 | Zabbix 6.0 LTS | - |
| 開発基盤 | VSCode Remote-SSH, WiringPi | - |

---

## 13. 残タスク

| 優先度 | 項目 |
|--------|------|
| 高 | Docker コンテナ化 |
| 高 | GitHub Actions CI/CD |
| 中 | Oracle Cloud 無料VMデプロイ |
| 低 | OpenCV アナログ温度計合流 |

---

> 最終更新: 2026-06-28
