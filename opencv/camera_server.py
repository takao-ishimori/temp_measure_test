import cv2
import numpy as np
import http.server
import json
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "database"))

CAMERA_ID = 0
HTML_PATH = os.path.join(os.path.dirname(__file__), "camera.html")

calib_y_top = None
calib_y_btm = None
calib_temp_top = 55.0
calib_temp_btm = -30.0


class CameraHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/camera":
            self._serve_html()
        elif self.path == "/api/camera":
            self._serve_jpeg()
        elif self.path == "/api/opencv_temp":
            self._serve_temp()
        elif self.path == "/api/calibration":
            self._json_response({
                "y_top": calib_y_top, "y_btm": calib_y_btm,
                "temp_top": calib_temp_top, "temp_btm": calib_temp_btm
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/calibrate":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            global calib_y_top, calib_y_btm, calib_temp_top, calib_temp_btm
            if "y_top" in body:
                calib_y_top = body["y_top"]
            if "y_btm" in body:
                calib_y_btm = body["y_btm"]
            if "temp_top" in body:
                calib_temp_top = float(body["temp_top"])
            if "temp_btm" in body:
                calib_temp_btm = float(body["temp_btm"])
            self._json_response({"status": "ok"})
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_html(self):
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_jpeg(self):
        cap = cv2.VideoCapture(CAMERA_ID)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            self.send_response(500)
            self.end_headers()
            return

        if calib_y_top is not None and calib_y_btm is not None:
            cv2.line(frame, (0, calib_y_top), (frame.shape[1], calib_y_top),
                     (0, 255, 0), 2)
            cv2.line(frame, (0, calib_y_btm), (frame.shape[1], calib_y_btm),
                     (0, 255, 0), 2)

        _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpeg)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(jpeg.tobytes())

    def _serve_temp(self):
        if calib_y_top is None or calib_y_btm is None:
            self._json_response({"temp": None, "error": "未キャリブレーション"})
            return

        cap = cv2.VideoCapture(CAMERA_ID)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            self._json_response({"temp": None, "error": "フレーム取得失敗"})
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 80, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 80, 50]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask1, mask2)

        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            self._json_response({"temp": None, "error": "赤色未検出"})
            return

        largest = max(contours, key=cv2.contourArea)
        _, top_y, _, h = cv2.boundingRect(largest)

        if h < 10:
            self._json_response({"temp": None, "error": "液柱短すぎ"})
            return

        y1, y2 = sorted([calib_y_top, calib_y_btm])
        if y1 == y2:
            self._json_response({"temp": None, "error": "キャリブレーション点が同じ"})
            return

        ratio = (top_y - y1) / (y2 - y1)
        ratio = max(0.0, min(1.0, ratio))
        temp = calib_temp_btm + ratio * (calib_temp_top - calib_temp_btm)
        self._json_response({"temp": round(temp, 1), "error": None})

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    port = 8090
    server = http.server.HTTPServer(("0.0.0.0", port), CameraHandler)
    print(f"カメラAPI起動: http://localhost:{port}")
    print(f"  画像: http://0.0.0.0:{port}/api/camera")
    print(f"  温度: http://0.0.0.0:{port}/api/opencv_temp")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("停止")


if __name__ == "__main__":
    main()
