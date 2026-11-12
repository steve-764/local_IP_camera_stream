import cv2


OPEN_TIMEOUT_MS = 6000
READ_TIMEOUT_MS = 6000


def open_stream(url: str , label: str) -> cv2.VideoCapture:
    params = [
        cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, OPEN_TIMEOUT_MS,
        cv2.CAP_PROP_READ_TIMEOUT_MSEC, READ_TIMEOUT_MS,
    ]
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        cap.release()
        raise ConnectionError("Cannot access camera stream. Ensure the camera and access devide are on the same network ")
    return cap
