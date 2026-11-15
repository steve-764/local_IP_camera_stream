import queue
import threading

import cv2


class Recorder:
    def __init__(self, path, size, fps, max_queue=60):
        self.dropped = 0
        self.error = None
        self._writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)

        if not self._writer.isOpened():
            self._writer.release()
            raise OSError("Could not create recording file.")
        self._queue = queue.Queue(maxsize=max_queue)
        self._thread = threading.Thread(target=self._work, daemon=True)
        self._thread.start()


    def write(self, frame):
        try:

            self._queue.put_nowait(frame.copy())
        except queue.Full:
            self.dropped += 1


    def _work(self):
        while True:
            frame = self._queue.get()
            if frame is None:
                break
            if self.error is None:
                try:
                    self._writer.write(frame)
                except Exception as e:
                    self.error = e
        self._writer.release()


    def stop(self):
        self._queue.put(None)
        self._thread.join()
