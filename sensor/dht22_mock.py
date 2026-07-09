import time
import random
import math


class MockDHT22:
    def __init__(self, base_temp=23.0, base_humidity=55.0):
        self.base_temp = base_temp
        self.base_humidity = base_humidity
        self.error_count = 0
        self.total_count = 0

    def read(self):
        self.total_count += 1
        temperature = self.base_temp + random.gauss(0, 0.3)
        humidity = self.base_humidity + random.gauss(0, 0.8)
        humidity = max(0.0, min(100.0, humidity))
        return (round(temperature, 1), round(humidity, 1))


def main():
    sensor = MockDHT22()
    print("===== DHT22 テストシート用データ収集 =====\n")
    print("回数, 温度(C), 湿度(%)\n")

    results = []
    for i in range(10):
        temp, hum = sensor.read()
        results.append((temp, hum))
        print(f"{i+1:>4}, {temp:>6.1f}, {hum:>6.1f}")
        time.sleep(0.5)

    print("\n===== 統計 =====\n")
    temps = [r[0] for r in results]
    hums = [r[1] for r in results]

    print(f"温度  平均: {sum(temps)/len(temps):.1f} C")
    print(f"温度  最小: {min(temps):.1f} C")
    print(f"温度  最大: {max(temps):.1f} C")
    print(f"湿度  平均: {sum(hums)/len(hums):.1f} %")
    print(f"湿度  最小: {min(hums):.1f} %")
    print(f"湿度  最大: {max(hums):.1f} %")

    print("\nテストシートの T02/T03 記録表に上記の値を転記してください。")


if __name__ == "__main__":
    main()
