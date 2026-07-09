import cv2
import numpy as np


class ThermometerReader:
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise RuntimeError("カメラを開けませんでした")

    def capture_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def detect_scale_marks(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=50,
                                minLineLength=50, maxLineGap=10)
        return lines

    def detect_mercury_level(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        return contours

    def estimate_temperature(self, frame):
        lines = self.detect_scale_marks(frame)
        if lines is None or len(lines) < 2:
            return None
        sorted_lines = sorted(lines, key=lambda l: l[0][1])
        top_line = sorted_lines[0][0]
        bottom_line = sorted_lines[-1][0]
        scale_range_px = abs(bottom_line[1] - top_line[1])
        if scale_range_px == 0:
            return None
        contours = self.detect_mercury_level(frame)
        if not contours:
            return None
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        mercury_center_y = y + h // 2
        ratio = (bottom_line[1] - mercury_center_y) / scale_range_px
        temp_min, temp_max = 0.0, 50.0
        temperature = temp_min + ratio * (temp_max - temp_min)
        return round(temperature, 1)

    def save_snapshot(self, frame, filename="snapshot.jpg"):
        cv2.imwrite(filename, frame)
        print(f"画像保存: {filename}")

    def release(self):
        self.cap.release()


def main():
    print("OpenCV 温度計読み取り 開始 (Ctrl+C で停止)")
    reader = ThermometerReader(camera_id=0)
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
                reader.save_snapshot(frame)
    except KeyboardInterrupt:
        pass
    finally:
        reader.release()
        print("停止しました")


if __name__ == "__main__":
    main()
