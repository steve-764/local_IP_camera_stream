import cv2 
import time
from datetime import datetime


from src.config import load_config, build_stream_url
from src.stream import open_stream


ESC = 27
FONT = cv2.FONT_HERSHEY_SIMPLEX

def resize_to_width(frame, width):
    # extracting dimensions: height and width
    h, w = frame.shape[:2]
    # resizing the image: 
    # round to ensure new height is always an int
    return cv2.resize(frame, (width, round(h * width / w)))


def draw_overlay(frame, name, fps):
    # function to overlay framerate, camera name, time etc
    h, w = frame.shape[:2]

    lines = [
        name, 
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f"{w}x{h}",
        f"{fps:.1f} FPS",
    ]
    for i, text in enumerate(lines):
        pos = (10, 25 + i * 25)
        cv2.putText(frame, text, pos, FONT, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, text, pos, FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)


def main():
    cfg = load_config()
    name = cfg["camera"]["name"]
    width = cfg["display"]["width"]

    cap = open_stream(build_stream_url(cfg))
    fps = 0.0
    prev = time.perf_counter()
    
    try:
        while True:
            ok, frame = cap.read()
            if not ok: 
                print("Stream ended or frame read failed")
                break


            now = time.perf_counter()
            instant = 1.0 / (now - prev) if now > prev else 0.0
            prev = now
            fps = instant if fps == 0.0 else 0.9 * fps + 0.1 * instant


            frame = resize_to_width(frame, width)
            draw_overlay(frame, name, fps)

            
            # close stream window when ESC key entered
            cv2.imshow("IP camera", frame)
            if cv2.waitKey(1) & 0xFF == ESC:
                break

    # using finally to ensure block runs on all exit conditions
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()