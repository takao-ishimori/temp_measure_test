import cv2
import numpy as np
import math


class DialThermometerReader:
    def __init__(self, camera_id=0, temp_min=-25.0, temp_max=55.0):
        self.cap = cv2.VideoCapture(camera_id)
        self.temp_min = temp_min
        self.temp_max = temp_max
        if not self.cap.isOpened():
            raise RuntimeError("カメラを開けませんでした")

    def capture_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def find_dial_center(self, gray):
        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
            param1=50, param2=30, minRadius=50, maxRadius=300
        )
        if circles is not None:
            circles = np.uint16(np.around(circles))
            return circles[0][0]
        return None

    def find_needle_angle(self, gray, center, radius):
        cx, cy = center
        inner_radius = int(radius * 0.1)
        outer_radius = int(radius * 0.9)

        mask = np.zeros_like(gray)
        cv2.circle(mask, (cx, cy), outer_radius, 255, -1)
        cv2.circle(mask, (cx, cy), inner_radius, 0, -1)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        enhanced = cv2.bitwise_and(enhanced, enhanced, mask=mask)

        edges = cv2.Canny(enhanced, 30, 90)

        best_angle = None
        best_sum = 0

        for angle in range(0, 360, 2):
            rad = math.radians(angle)
            sum_val = 0
            count = 0
            for r in range(inner_radius, outer_radius, 2):
                x = int(cx + r * math.cos(rad))
                y = int(cy - r * math.sin(rad))
                if 0 <= x < edges.shape[1] and 0 <= y < edges.shape[0]:
                    sum_val += edges[y, x]
                    count += 1
            if count > 0 and sum_val > best_sum:
                best_sum = sum_val
                best_angle = angle

        return best_angle

    def angle_to_temperature(self, angle_deg):
        if angle_deg is None:
            return None

        start_angle = 180.0
        end_angle   = 360.0

        a = angle_deg
        if a < start_angle and a < 90:
            a += 360

        ratio = (a - start_angle) / (end_angle - start_angle)
        ratio = max(0.0, min(1.0, ratio))
        temperature = self.temp_min + ratio * (self.temp_max - self.temp_min)
        return round(temperature, 1)

    def estimate_temperature(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        center = self.find_dial_center(blurred)
        if center is None:
            return None

        cx, cy, radius = center[0], center[1], center[2]
        angle = self.find_needle_angle(blurred, (cx, cy), radius)

        return self.angle_to_temperature(angle)

    def save_snapshot(self, frame, filename="snapshot.jpg"):
        cv2.imwrite(filename, frame)

    def release(self):
        self.cap.release()


def main():
    print("ダイヤル温度計 読み取り開始 (Ctrl+C で停止)")
    reader = DialThermometerReader(camera_id=0, temp_min=-25.0, temp_max=55.0)
    count = 0
    try:
        while True:
            frame = reader.capture_frame()
            if frame is None:
                print("フレーム取得失敗")
                break
            temp = reader.estimate_temperature(frame)
            count += 1
            if temp is not None:
                print(f"[{count:>4}] 推定温度: {temp} C")
            if count % 30 == 0:
                reader.save_snapshot(frame, "snapshot.jpg")
    except KeyboardInterrupt:
        pass
    finally:
        reader.release()
        print("停止しました")


if __name__ == "__main__":
    main()
