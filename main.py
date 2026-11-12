import cv2 
from src.config import load_config, build_stream_url
from src.stream import open_stream


def main():
    cfg = load_config()
    cap = open_stream(build_stream_url(cfg))


    while True:
        ok, frame = cap.read()
        if not ok: 
            print("Stream ended or frame read failed")
            break

        cv2.imshow("IP camera", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()