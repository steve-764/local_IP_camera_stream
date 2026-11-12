import cv2 
from src.config import load_config, build_stream_url
from src.stream import open_stream


ESC = 27


def main():

    cap = open_stream(build_stream_url(load_config()))

    try:
        while True:
            ok, frame = cap.read()
            if not ok: 
                print("Stream ended or frame read failed")
                break

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