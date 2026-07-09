import sqlite3
import os
import sys
import math
import csv
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "dht22_data.db")


def load_data():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT temperature_c, humidity_pct FROM dht22_readings ORDER BY id"
    ).fetchall()
    conn.close()
    return rows


def desc_stats(values, name):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1) if n > 1 else 0
    std_dev = math.sqrt(variance)
    sorted_v = sorted(values)
    median = sorted_v[n // 2] if n % 2 == 1 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2

    def percentile(data, p):
        k = (len(data) - 1) * p / 100.0
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        return data[int(f)] * (c - k) + data[int(c)] * (k - f)

    q1 = percentile(sorted_v, 25)
    q3 = percentile(sorted_v, 75)
    min_val = sorted_v[0]
    max_val = sorted_v[-1]

    print(f"\n===== {name} 基本統計量 (n={n}) =====")
    print(f"平均:     {mean:.2f}")
    print(f"中央値:   {median:.2f}")
    print(f"標準偏差: {std_dev:.2f}")
    print(f"分散:     {variance:.2f}")
    print(f"最小値:   {min_val:.2f}")
    print(f"第1四分位数: {q1:.2f}")
    print(f"第3四分位数: {q3:.2f}")
    print(f"最大値:   {max_val:.2f}")
    print(f"範囲:     {max_val - min_val:.2f}")

    return {"n": n, "mean": mean, "median": median, "std": std_dev,
            "q1": q1, "q3": q3, "min": min_val, "max": max_val}


def welch_ttest(group1, group2):
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        print("サンプルサイズ不足のためt検定をスキップします")
        return

    m1 = sum(group1) / n1
    m2 = sum(group2) / n2
    v1 = sum((x - m1) ** 2 for x in group1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in group2) / (n2 - 1)

    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0:
        print("標準誤差がゼロのためt検定をスキップします")
        return

    t_stat = (m1 - m2) / se

    df_num = (v1 / n1 + v2 / n2) ** 2
    df_den = ((v1 / n1) ** 2) / (n1 - 1) + ((v2 / n2) ** 2) / (n2 - 1)
    df = df_num / df_den if df_den != 0 else 1

    import scipy.stats as stats
    p_value = 2 * stats.t.sf(abs(t_stat), df)

    print(f"\n===== Welchのt検定（対応なし）=====")
    print(f"グループ1: n={n1}, 平均={m1:.2f}")
    print(f"グループ2: n={n2}, 平均={m2:.2f}")
    print(f"平均差: {abs(m1 - m2):.2f}")
    print(f"t値: {t_stat:.4f}")
    print(f"自由度: {df:.1f}")
    print(f"p値: {p_value:.4f}")
    if p_value < 0.05:
        print(f"→ * p < 0.05 で有意差あり（帰無仮説を棄却）")
    else:
        print(f"→   有意差なし（帰無仮説を棄却できない）")


def pearson_correlation(x, y):
    n = len(x)
    if n < 3:
        print("サンプルサイズ不足のため相関分析をスキップします")
        return

    mx = sum(x) / n
    my = sum(y) / n
    cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (n - 1)
    sx = math.sqrt(sum((xi - mx) ** 2 for xi in x) / (n - 1))
    sy = math.sqrt(sum((yi - my) ** 2 for yi in y) / (n - 1))
    r = cov / (sx * sy) if sx * sy != 0 else 0

    import scipy.stats as stats
    t_stat = r * math.sqrt((n - 2) / (1 - r * r)) if abs(r) < 1 else 0
    p_value = 2 * stats.t.sf(abs(t_stat), n - 2) if n > 2 else 1

    print(f"\n===== Pearson相関分析 (温度 vs 湿度) =====")
    print(f"相関係数 r: {r:.4f}")
    print(f"t値: {t_stat:.4f}")
    print(f"p値: {p_value:.4f}")
    if p_value < 0.05:
        print(f"→ * p < 0.05 で有意な相関あり")
    else:
        print(f"→   有意な相関なし")
    if abs(r) < 0.2:
        print(f"→   ほとんど相関なし")
    elif abs(r) < 0.4:
        print(f"→   弱い相関")
    elif abs(r) < 0.7:
        print(f"→   中程度の相関")
    else:
        print(f"→   強い相関")

    return r


def plot_graphs(temps, hums, output_dir):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        os.makedirs(output_dir, exist_ok=True)
        n = len(temps)
        x_axis = list(range(n))

        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle("DHT22 温度・湿度 統計分析レポート", fontsize=14)

        axes[0, 0].plot(x_axis, temps, color="red", alpha=0.6, linewidth=0.8)
        window = max(5, n // 20)
        if n > window:
            ma = np.convolve(temps, np.ones(window) / window, mode="valid")
            axes[0, 0].plot(range(window - 1, n), ma, color="darkred",
                            linewidth=2, label=f"移動平均 (n={window})")
        axes[0, 0].set_title("温度 時系列推移")
        axes[0, 0].set_xlabel("測定回数")
        axes[0, 0].set_ylabel("温度 (C)")
        axes[0, 0].legend()

        axes[0, 1].hist(temps, bins=20, color="skyblue", edgecolor="black", alpha=0.7)
        axes[0, 1].axvline(sum(temps) / n, color="red", linestyle="--", label="平均")
        axes[0, 1].set_title("温度 ヒストグラム")
        axes[0, 1].set_xlabel("温度 (C)")
        axes[0, 1].set_ylabel("度数")
        axes[0, 1].legend()

        axes[1, 0].scatter(temps, hums, alpha=0.5, s=10, c="blue")
        axes[1, 0].set_title("温度 vs 湿度 散布図")
        axes[1, 0].set_xlabel("温度 (C)")
        axes[1, 0].set_ylabel("湿度 (%)")

        axes[1, 1].boxplot([temps, hums], labels=["温度 (C)", "湿度 (%)"])
        axes[1, 1].set_title("箱ひげ図")
        axes[1, 1].set_ylabel("値")

        plt.tight_layout()
        out_path = os.path.join(output_dir, "stats_report.png")
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"\nグラフ保存: {out_path}")
    except ImportError:
        print("matplotlib がインストールされていません。グラフ出力をスキップします。")


def main():
    rows = load_data()
    if len(rows) < 5:
        print(f"データが少なすぎます（{len(rows)}件）。データを十分に集めてから再実行してください。")
        return

    temps = [r[0] for r in rows]
    hums  = [r[1] for r in rows]

    print(f"データ件数: {len(rows)}")
    print("=" * 50)

    desc_stats(temps, "温度 (C)")
    desc_stats(hums, "湿度 (%)")

    mid = len(temps) // 2
    welch_ttest(temps[:mid], temps[mid:])

    pearson_correlation(temps, hums)

    plot_graphs(temps, hums, os.path.join(os.path.dirname(__file__), "output"))

    print("\n" + "=" * 50)
    print("分析完了")


if __name__ == "__main__":
    main()
