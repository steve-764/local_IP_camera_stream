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
RECORDINGS_DIR = Path("recordings")


def resize_to_width(frame, width):
    # extracting dimensions: height and width
    h, w = frame.shape[:2]
    # resizing the image based on width
    # round to ensure new height is always an int
    return cv2.resize(frame, (width, round(h * width / w)))


def draw_text(frame, text, pos):
    cv2.putText(frame, text, pos, FONT, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, text, pos, FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)


def timestamp():
    # collect current date and time 
    return datetime.now().strftime("%Y%m%d_%H%M%S_")[:-3]

    
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
    # use timestamp funct to name screenshot file
    path = SCREENSHOT_DIR / f"screenshot_{timestamp()}.png"
    
    if not cv2.imwrite(str(path), frame):
        return None
    return path


def draw_rec(frame, time):
    w = frame.shape[1]
    minutes, seconds = divmod(int(time), 60)

    # creating red dot to indicate recording
    cv2.circle(frame, (w - 130, 20), 8, (0, 0, 255), -1)
    draw_text(frame, f"REC {minutes:02d}:{seconds:02d}", (w - 115, 26))


def start_recording(frame, fps):
    RECORDINGS_DIR.mkdir(exist_ok=True)
    path = RECORDINGS_DIR / f"recording_{timestamp()}.mp4"

    h, w = frame.shape[:2]
    # saving the recording path, video encoding codec, fps and resolution to writer
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    
    if not writer.isOpened():
        return None, None
    return writer, path


def main():
    cfg = load_config()
    name = cfg["camera"]["name"]
    width = cfg["display"]["width"]

    cap = open_stream(build_stream_url(cfg))
    fps = 0.0
    prev = time.perf_counter()
    message, message_until = "", 0.0
    writer, rec_path, rec_start = None, None, 0.0

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

            #
            if writer:
                writer.write(frame)
                draw_rec(frame, now - rec_start)

            if now < message_until:
                draw_text(frame, message, (10, frame.shape[0] - 15))
            
            cv2.imshow("IP camera", frame)

            # close stream window when ESC key entered
            key = cv2.waitKey(1) & 0xFF
            # stopping the video stream
            if key == ESC:
                break

            # making a screenshot
            if key in (ord("s"), ord("S")):
                path = save_screenshot(frame)
                message = f"Saved {path.name}" if path else "Screenshot failed"
                message_until = time.perf_counter() + CONFIRM_TIME

            # making a recording
            if key in (ord("r"), ord("R")):
                if writer is None:
                    writer, rec_path = start_recording(frame, fps or 30.0)
                    rec_start = time.perf_counter()
                    message = "Recording started" if writer else "Recording failed"
                else:
                    writer.release()
                    writer = None
                    message = f"Saved {rec_path}"

                message_until = time.perf_counter() + CONFIRM_TIME


    # using finally to ensure block runs on all exit conditions
    finally:
        if writer:
            writer.release()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()