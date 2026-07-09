# コードの計算式・アドレス指定の意味

## DHT22 のビット取り出し（C++）

```cpp
dht22_data[j / 8] <<= 1;
if (counter > 16) dht22_data[j / 8] |= 1;
```

**意味**: DHT22はパルスの長さで0/1を送ってくる。26〜28μs=0、70μs=1。
`counter > 16` で「パルスが長いなら1、短いなら0」と判定。
`j/8` は「何バイト目か」、`<<=1` で「1ビット左シフトして空いた最下位に `|= 1` で書き込む」。
→ これはDHT22のデータシート通りの実装。

```cpp
*humidity    = (float)((dht22_data[0] << 8) + dht22_data[1]) / 10.0f;
*temperature = (float)(((dht22_data[2] & 0x7F) << 8) + dht22_data[3]) / 10.0f;
if (dht22_data[2] & 0x80) *temperature = -(*temperature);
```

**意味**: 湿度は上位バイト×256＋下位バイト÷10。温度も同じだが最上位bit(0x80)が1ならマイナス温度。
→ データシートの「湿度=16bit/10、温度=16bit/10、bit15=符号」をそのままコード化。

---

## HC-SR04 の距離計算

```cpp
distance_cm = (float)(end_time - start_time) / 58.0f;
```

**意味**: 音速は約340m/s = 34,000cm/s。往復なので÷2すると17,000cm/s。
`1 / 17000 = 0.0000588...` 秒/cm → 逆数は `1 / 0.0000588 ≈ 58` μs/cm。
つまり「経過マイクロ秒 ÷ 58 = 距離(cm)」。

---

## 温度換算（棒温度計）

```python
ratio = 1.0 - (liquid_top / frame_h)
temperature = temp_min + ratio * (temp_max - temp_min)
```

**意味**: 画像の上端が高温、下端が低温。液柱の先端Y座標が小さいほど温度が高い。
`1.0 - (Y座標/高さ)` で「下端から何%の位置か」を出し、温度範囲に換算。

---

## SQLite バインドパラメータ

```python
conn.execute("INSERT INTO dht22_readings (temperature_c, humidity_pct) VALUES (?, ?)", (t, h))
```

**意味**: `?` はプレースホルダ。文字列連結でSQLを組み立てると**SQLインジェクション**の危険がある。
バインドパラメータなら値が自動でエスケープされ安全。

---

## Flaskを使わず http.server な理由

```python
server = http.server.HTTPServer(("0.0.0.0", port), Handler)
```

**意味**: `pip install flask` が不要。Pythonの標準ライブラリだけで動く。
ラズパイの最小構成でも依存ゼロでWebサーバーが立つ。

---

## `/proc` を直接読む理由

```python
with open("/proc/stat", "r") as f:  # CPU
with open("/proc/meminfo", "r") as f:  # メモリ
```

**意味**: Linuxカーネルが提供する仮想ファイル。`psutil` を入れなくても、このファイルを読むだけで
CPU・メモリ・ディスク・負荷平均が全部わかる。依存ゼロ。
