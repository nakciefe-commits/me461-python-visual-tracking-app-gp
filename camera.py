"""
Webcam reader that runs in the background.

Reading a frame from the webcam means waiting about 20 ms for the camera.
Instead of making the game wait, a background "thread" (a second worker
inside the same program) reads frames all the time and keeps the newest one.
The game just takes whatever frame is newest.
"""

import sys
import threading
import time

import cv2

from settings import WINDOWS_DIRECTSHOW


class Camera:
    def __init__(self, index):
        if sys.platform == "win32" and WINDOWS_DIRECTSHOW:
            # On Windows the default camera system (Media Foundation) can take
            # 10+ seconds to open a webcam; DirectShow opens it much faster.
            # If a webcam doesn't work with it, set WINDOWS_DIRECTSHOW = False.
            self.capture = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            self.capture = cv2.VideoCapture(index)
        self.frame = None                       # the newest frame
        self.running = self.capture.isOpened()  # False = no webcam, or it stopped
        if self.running:
            # daemon=True: this thread will not keep the program alive on exit.
            threading.Thread(target=self.keep_reading, daemon=True).start()

    def keep_reading(self):
        """Runs in the background thread: read frames until stopped."""
        while self.running:
            ok, frame = self.capture.read()
            if not ok:
                self.running = False   # the webcam stopped sending pictures
            else:
                self.frame = frame

    def read(self):
        """Return the newest frame, or None if the webcam is not working."""
        # Right after starting, the first frame may not have arrived yet.
        waited = 0.0
        while self.frame is None and self.running and waited < 3.0:
            time.sleep(0.01)
            waited += 0.01
        return self.frame if self.running else None

    def release(self):
        self.running = False
        time.sleep(0.1)   # let the thread finish its last read
        self.capture.release()
