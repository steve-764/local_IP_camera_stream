import cv2

def open_stream(url: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        cap.release()
        raise ConnectionError("Cannot access camera stream. Check network ")
    return cap
