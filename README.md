# temp_measure - IoT温湿度監視システム

Raspberry Pi 上で DHT22 温湿度センサー + HC-SR04 超音波距離センサーを制御し、
MQTT / SQLite / Webダッシュボード / Zabbix まで一貫実装したポートフォリオ。

**Python と C++ の両方で全コンポーネントを実装。**

[![Python](https://img.shields.io/badge/Python-3.9-blue)]()
[![C++](https://img.shields.io/badge/C++-11-orange)]()
[![MQTT](https://img.shields.io/badge/MQTT-Mosquitto-purple)]()
[![Zabbix](https://img.shields.io/badge/Zabbix-6.0-red)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## システム構成

```
[DHT22 温度/湿度] ──┐
[HC-SR04 距離]    ──┤
[RPi CPU/MEM/DISK] ──┤
                     ├── MQTT (Mosquitto) ──→ SQLite ──→ CSV / 統計分析
                     │                         │
                     ├── Webダッシュボード ←───┘
                     │   (Chart.js リアルタイムグラフ)
                     │
                     └── Zabbix 6.0 LTS
                         (サーバー/エージェント監視)
```

## 技術スタック

| 層 | 技術 | 言語 |
|----|------|------|
| センサー制御 | GPIO, I2C (DHT22), 超音波 (HC-SR04) | Python / C++ |
| メッセージング | MQTT (Mosquitto) | Python / C++ |
| データベース | SQLite | SQL |
| データ出力 | CSVエクスポート | Python / C++ |
| 統計分析 | t検定 (Welch), Pearson相関, 記述統計 | Python (scipy) |
| 可視化 | Webダッシュボード (Chart.js) | HTML/JS |
| 画像認識 | OpenCV アナログ温度計読み取り（実験的実装） | Python |
| 監視 | Zabbix 6.0 LTS (CPU/メモリ/ディスク) | - |
| CI/CD | GitHub Actions（予定） | YAML |
| コンテナ | Docker / Docker Compose（予定） | Dockerfile |

## ファイル構成

```
temp_measure/
├── sensor/              # センサー制御 (DHT22 + HC-SR04)
│   ├── dht22.py / .cpp
│   ├── hc_sr04.py / .cpp
│   └── dht22_mock.py   # ハードウェア不要のモックテスト
├── mqtt/                # MQTT 連携
│   ├── mqtt_publisher.py / .cpp
│   └── mqtt_subscriber.py / .cpp
├── database/            # SQLite 管理
│   ├── schema.sql
│   └── db_manager.py / .cpp / .h
├── monitoring/          # 監視・可視化
│   ├── dashboard_server.py + dashboard.html
│   ├── system_monitor.py        # ラズパイ状態監視
│   ├── camera_server.py + camera.html  # OpenCV キャリブレーション
│   └── setup_zabbix.sh
├── analytics/           # 統計分析
│   ├── stats_analysis.py
│   └── output/          # 分析グラフ出力
├── opencv/              # アナログ温度計読み取り（開発中）
├── TEST_SHEET.md        # テスト仕様書・結果報告書
├── AI_RULES.md          # AI協働ルール
└── start_all.py         # 一括起動スクリプト
```

## クイックスタート

```bash
# 全プロセス一括起動（センサー→MQTT→DB→ダッシュボード→システム監視）
python start_all.py

# ダッシュボード
http://[RPiのIP]:8080/dashboard

# Zabbix
http://[RPiのIP]/zabbix  (Admin / zabbix)
```

## 実装済み機能

- [x] DHT22 温度・湿度センサー読み取り (Python / C++)
- [x] HC-SR04 超音波距離センサー (Python / C++)
- [x] MQTT メッセージング (Mosquitto ブローカー自前構築)
- [x] SQLite データ保存 + CSV エクスポート
- [x] Web ダッシュボード (Chart.js リアルタイム更新)
- [x] ラズパイ状態監視 (CPU/メモリ/ディスク/CPU温度/負荷)
- [x] 統計分析 (記述統計 / Welchのt検定 / Pearson相関)
- [x] Zabbix 6.0 LTS 導入・設定
- [x] テストシートによる品質管理 (全7項目)
- [x] 一括起動/停止スクリプト

## 開発中・予定

- [ ] Docker コンテナ化
- [ ] GitHub Actions CI/CD
- [ ] OpenCV アナログ温度計読み取り
- [ ] Grafana ダッシュボード連携

## 統計分析 実績（一部抜粋）

```
===== Welchのt検定（対応なし）=====
グループ1 (前半): 平均=29.66℃
グループ2 (後半): 平均=29.69℃
t値: -2.5033  p値: 0.0135
→ p < 0.05 で時間帯による温度差に有意差あり

===== Pearson相関分析 (温度 vs 湿度) =====
相関係数 r: -0.6254  p値: 0.0006
→ p < 0.001 で有意な負の相関（中程度）
```

## ライセンス

MIT
