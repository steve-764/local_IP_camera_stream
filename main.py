import cv2 
import time
from datetime import datetime
from pathlib import Path


from src.config import ConfigError,load_config, build_stream_url, camera_label
from src.stream import open_stream
from src.recorder import Recorder


ESC = 27
FONT = cv2.FONT_HERSHEY_SIMPLEX
SCREENSHOT_DIR = Path("screenshots")
CONFIRM_TIME = 2.0
RECORDINGS_DIR = Path("recordings")
MAX_RECONNECTS = 5
RECONNECT_DELAY = 2.0


def resize_to_width(frame, width):
    # extracting dimensions: height and width
    h, w = frame.shape[:2]
    # resizing the image based on width
    # round to ensure new height is always an int
    return cv2.resize(frame, (width, round(h * width / w)))


def draw_text(frame, text, pos):
    # set the font, size and position of text displayed on the screen
    # cv2.putText(frame, text, pos, FONT, 0.6, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(frame, text, pos, FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)


def timestamp():
    # collect current date and time
    return datetime.now().strftime("%Y%m%d_%H%M%S_")

    
def draw_overlay(frame, name, clock_text, fps):
    # function to overlay framerate, camera name, time etc
    h, w = frame.shape[:2]

    lines = [
        name, 
        clock_text,
        f"{w}x{h}",
        f"{fps:.1f} FPS",
    ]
    for i, text in enumerate(lines):
        draw_text(frame, text, (10, 25 + i * 25))
        

def save_screenshot(frame):
    try:
        # check for screenshot dir, if not found create it
        SCREENSHOT_DIR.mkdir(exist_ok=True)
        # use timestamp funct to name screenshot file
        path = SCREENSHOT_DIR / f"screenshot_{timestamp()}.png"
        return path if cv2.imwrite(str(path), frame) else None
    except OSError:
        return None


def draw_rec(frame, time):
    w = frame.shape[1]
    minutes, seconds = divmod(int(time), 60)

    # creating red dot to indicate recording
    cv2.circle(frame, (w - 130, 20), 8, (0, 0, 255), -1)
    draw_text(frame, f"REC {minutes:02d}:{seconds:02d}", (w - 115, 26))


def start_recording(frame, fps):
    try:
       RECORDINGS_DIR.mkdir(exist_ok=True)
       path = RECORDINGS_DIR / f"recording_{timestamp()}.mp4"
       h, w = frame.shape[:2]
       return Recorder(path, (w, h), fps), path
    except OSError:
        return None, None 


def finish_recording(recorder, path):
    recorder.stop()
    note = f"{recorder.dropped} frames droped" if recorder.dropped else ""
    print(f"Recording saved: {path}{note}")


def reconnect(url, label):
    # attempts to reopen the stream
    for attempt in range(1, MAX_RECONNECTS + 1):
        print(f"Connection lost! Reconnnecting ({attempt}/{MAX_RECONNECTS})")
        # if ESC pressed while attempting to reconnect
        if cv2.waitKey(int(RECONNECT_DELAY * 1000)) & 0xFF == ESC:
           print("Reconect cancelled") 
           return None

        try: 
            cap = open_stream(url, label)
            print("Reconnected.")
            return cap
        except ConnectionError:
            pass

    print(f"Could not reconnect after {MAX_RECONNECTS} attempts. ")
    return None


def run():
    cfg = load_config()
    name = cfg["camera"]["name"]
    width = cfg["display"]["width"]
    url = build_stream_url(cfg)
    label = camera_label(cfg)

    clock_text, clock_second = "", 0
    cap = open_stream(url, label)
    fps = 0.0
    prev = time.perf_counter()
    message, message_until = "", 0.0
    recorder, rec_path, rec_start = None, None, 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None: 
                cap.release()
                cap = reconnect(url, label)
                if cap is None:
                    print("Stream ended or frame read failed")
                    break
                prev = time.perf_counter()
                continue

            now = time.perf_counter()
            instant = 1.0 / (now - prev) if now > prev else 0.0
            prev = now
            fps = instant if fps == 0.0 else 0.95 * fps + 0.05 * instant

            # writing the fps counter once every second rather than per frame
            second = int(time.time())
            if second != clock_second:
                clock_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                clock_second = second

            frame = resize_to_width(frame, width)
            draw_overlay(frame, name, clock_text, fps)


            if recorder and recorder.error:
                finish_recording(recorder, rec_path)
                recorder = None
                message = "Recodding error: write error"
                message_until = time.perf_counter() + CONFIRM_TIME
            if recorder:
                recorder.write(frame)
                draw_rec(frame, now - rec_start)
            if now < message_until:
                draw_text(frame, message, (10, frame.shape[0] - 15))
            cv2.imshow("IP Camera", frame)

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
                if recorder is None:
                    recorder, rec_path = start_recording(frame, fps or 15.0)
                    rec_start = time.perf_counter()
                    message = "Recording started" if recorder else "Recording failed!"
                else:
                    finish_recording(recorder, rec_path)
                    message = f"Saved {rec_path}"
                    recorder = None
                message_until = time.perf_counter() + CONFIRM_TIME

    # using finally to ensure block runs on all exit conditions
    finally:
        if recorder:
            finish_recording(recorder, rec_path)
        if cap is not None:
            cap.release()
        cv2.destroyAllWindows()


def main():
    try: 
        run()
        return 0
    except (ConfigError, ConnectionError) as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Program stopped by user!")
        return 0
    except Exception as e:
        print("Unexpected error: {e}")
    return 1


if __name__ == "__main__":
    main()