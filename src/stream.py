import cv2

def open_stream(url: str) -> cv2.VideoCapture:
  
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        cap.release()
        raise ConnectionError("Cannot access camera stream. Ensure the camera and access devide are on the same network ")
    return cap
