"""
Webcam reader that runs in the background.

Reading a frame from the webcam takes about 20 ms of waiting. If the game
waited for it every frame, that time would be lost. Instead, a background
"thread" (a second worker inside the same program) keeps reading frames, and
the game just picks up the newest one. So reading the next picture happens at
the same time as the game processes the current one.
"""

import threading

import cv2


class Camera:
    def __init__(self, index):
        self.capture = cv2.VideoCapture(index)
        self.frame = None        # the newest frame
        self.frame_number = 0    # goes up by one for every new frame
        self.last_given = 0      # frame_number of the frame read() last returned
        self.running = self.capture.isOpened()
        self.failed = False      # True if the webcam stopped sending pictures

        # A Condition lets read() sleep until the thread says "new frame!".
        self.condition = threading.Condition()
        if self.running:
            # daemon=True: the thread will not keep the program alive on exit.
            self.thread = threading.Thread(target=self._keep_reading, daemon=True)
            self.thread.start()

    def is_open(self):
        return self.running

    def _keep_reading(self):
        """Runs in the background thread: read frames forever."""
        while self.running:
            ok, frame = self.capture.read()
            with self.condition:
                if not ok:
                    self.failed = True
                    self.running = False
                else:
                    self.frame = frame
                    self.frame_number += 1
                self.condition.notify_all()

    def read(self, timeout=2.0):
        """
        Wait for a frame newer than the last one returned, and return it.
        Returns None if the webcam stopped or nothing came within `timeout` s.
        """
        with self.condition:
            got_one = self.condition.wait_for(
                lambda: self.frame_number > self.last_given or not self.running, timeout)
            if not got_one or self.frame_number == self.last_given:
                return None
            self.last_given = self.frame_number
            return self.frame

    def release(self):
        self.running = False
        if hasattr(self, "thread"):
            self.thread.join(timeout=1.0)
        self.capture.release()
