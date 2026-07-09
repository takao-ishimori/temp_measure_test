import cv2
import numpy as np


class StickThermometerReader:
    def __init__(self, camera_id=0, temp_min=0.0, temp_max=50.0):
        self.cap = cv2.VideoCapture(camera_id)
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.roi = None
        if not self.cap.isOpened():
            raise RuntimeError("カメラを開けませんでした")

    def capture_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def set_roi(self, x, y, w, h):
        self.roi = (x, y, w, h)

    def find_liquid_top(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 80, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 80, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)

        if h < 10 or w > h * 3:
            return None

        return (x, y, w, h)

    def estimate_temperature(self, frame):
        if self.roi is not None:
            rx, ry, rw, rh = self.roi
            frame = frame[ry:ry+rh, rx:rx+rw]
            y_offset = ry
            frame_h = rh
        else:
            y_offset = 0
            frame_h = frame.shape[0]

        liquid = self.find_liquid_top(frame)
        if liquid is None:
            return None

        _, liquid_top, _, liquid_h = liquid
        absolute_top = y_offset + liquid_top

        temp_range = self.temp_max - self.temp_min
        ratio = 1.0 - (absolute_top / frame_h)
        ratio = max(0.0, min(1.0, ratio))

        temperature = self.temp_min + ratio * temp_range
        return round(temperature, 1)

    def save_snapshot(self, frame, filename="snapshot.jpg"):
        cv2.imwrite(filename, frame)

    def release(self):
        self.cap.release()


def main():
    import sys
    t_min = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    t_max = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0

    print(f"棒状温度計 読み取り開始 (Ctrl+C で停止) 範囲: {t_min}℃ 〜 {t_max}℃")
    reader = StickThermometerReader(camera_id=0, temp_min=t_min, temp_max=t_max)
    count = 0

    try:
        while True:
            frame = reader.capture_frame()
            if frame is None:
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
