import cv2
import numpy as np


def find_liquid_top(frame, debug=False):
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

    if debug:
        cv2.imwrite("debug_mask.jpg", mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, mask

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)

    if h < 10 or w > h * 3:
        return None, mask

    return (x, y, w, h), mask


def estimate_temperature(frame, temp_min=0.0, temp_max=50.0, scale_bottom=None, scale_top=None):
    liquid, mask = find_liquid_top(frame, debug=True)
    if liquid is None:
        return None

    _, liquid_top, _, _ = liquid
    frame_h = frame.shape[0]

    if scale_bottom is not None and scale_top is not None:
        effective_h = scale_bottom - scale_top
        ratio = (scale_bottom - liquid_top) / effective_h
    else:
        ratio = 1.0 - (liquid_top / frame_h)

    ratio = max(0.0, min(1.0, ratio))
    temperature = temp_min + ratio * (temp_max - temp_min)
    return round(temperature, 1)


def main():
    import sys

    if len(sys.argv) < 2:
        print("使い方: python stick_image.py 画像.jpg [-30 55] [--calib 下Y 上Y]")
        print("例:      python stick_image.py thermo.jpg -30 55 --calib 900 100")
        return

    img_path = sys.argv[1]

    scale_bottom = None
    scale_top = None
    args = sys.argv[2:]

    t_min = 0.0
    t_max = 50.0
    i = 0
    while i < len(args):
        if args[i] == "--calib" and i + 2 < len(args):
            scale_bottom = int(args[i+1])
            scale_top = int(args[i+2])
            i += 3
        else:
            if t_min == 0.0 and t_max == 50.0:
                try:
                    t_min = float(args[i])
                    t_max = float(args[i+1])
                    i += 2
                except (ValueError, IndexError):
                    i += 1
            else:
                i += 1

    frame = cv2.imread(img_path)
    if frame is None:
        print(f"画像を開けませんでした: {img_path}")
        return

    deco_top = scale_top if scale_top is not None else 0
    deco_btm = scale_bottom if scale_bottom is not None else frame.shape[0]
    cv2.line(frame, (0, deco_top), (frame.shape[1], deco_top), (0, 255, 0), 2)
    cv2.line(frame, (0, deco_btm), (frame.shape[1], deco_btm), (0, 255, 0), 2)
    cv2.imwrite("debug_scale.jpg", frame)

    temp = estimate_temperature(frame, t_min, t_max, scale_bottom, scale_top)
    print(f"画像: {img_path}")
    print(f"範囲: {t_min}℃ 〜 {t_max}℃")
    if scale_bottom is not None:
        print(f"目盛り位置: 下={scale_bottom}px 上={scale_top}px")
    print(f"推定温度: {temp} C")
    print("debug_mask.jpg   → 赤色検出マスク")
    print("debug_scale.jpg  → 目盛り位置の線（緑線）")


if __name__ == "__main__":
    main()
