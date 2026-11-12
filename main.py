import cv2 
import time
from datetime import datetime
from pathlib import Path


from src.config import load_config, build_stream_url
from src.stream import open_stream


ESC = 27
FONT = cv2.FONT_HERSHEY_SIMPLEX
SCREENSHOT_DIR = Path("screenshots")
CONFIRM_TIME = 2.0


def resize_to_width(frame, width):
    # extracting dimensions: height and width
    h, w = frame.shape[:2]
    # resizing the image: 
    # round to ensure new height is always an int
    return cv2.resize(frame, (width, round(h * width / w)))


def draw_text(frame, text, pos):
    cv2.putText(frame, text, pos, FONT, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, text, pos, FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    
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
        draw_text(frame, text, (10, 25 + i * 25))
        

def save_screenshot(frame):
    # check for screenshot dir, if not found create it
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    # getting current date and miliseconds time to create timestamp
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")[:-3]
    # append stamp to screenshot name
    path = SCREENSHOT_DIR / f"screenshot_{stamp}.png"
    
    if not cv2.imwrite(str(path), frame):
        return None
    return path


def main():
    cfg = load_config()
    name = cfg["camera"]["name"]
    width = cfg["display"]["width"]

    cap = open_stream(build_stream_url(cfg))
    fps = 0.0
    prev = time.perf_counter()
    message, message_until = "", 0.0

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

            if now < message_until:
                draw_text(frame, message, (10, frame.shape[0] - 15))


            # close stream window when ESC key entered
            cv2.imshow("IP camera", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ESC:
                break

            if key in (ord("s"), ord("S")):
                path = save_screenshot(frame)
                message = f"Saved {path.name}" if path else "Screenshot failed"
                message_until = time.perf_counter() + CONFIRM_TIME


    # using finally to ensure block runs on all exit conditions
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()