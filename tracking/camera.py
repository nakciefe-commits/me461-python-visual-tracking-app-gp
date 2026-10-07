"""
Webcam reader with background startup, frame retries and automatic reconnection.

Reading a frame from the webcam means waiting about 20 ms for the camera.
Instead of making the game wait, a background "thread" (a second worker
inside the same program) reads frames all the time and keeps the newest one.
The game takes a copy of the newest picture without waiting. Missing or stale
pictures pause the game while this worker retries, instead of closing it.
"""

import sys
import threading
import time

import cv2

from settings import (WINDOWS_DIRECTSHOW, CAMERA_FALLBACK_INDICES, CAMERA_WARMUP_TIME,
                      CAMERA_STALE_TIME, CAMERA_RECONNECT_TIME, CAMERA_RETRY_INTERVAL,
                      CAMERA_READ_RETRY, CAMERA_STOP_TIMEOUT)


def open_device(index):
    """
    Open webcam number `index` with OpenCV. On Windows the default camera
    system (Media Foundation) can take 10+ seconds to open a webcam;
    DirectShow opens it much faster. If a webcam does not work with it, set
    WINDOWS_DIRECTSHOW = False in settings.py.
    """
    if sys.platform == "win32" and WINDOWS_DIRECTSHOW:
        return cv2.VideoCapture(index, cv2.CAP_DSHOW)
    return cv2.VideoCapture(index)


class Camera:
    def __init__(self, index):
        self.index = index
        # Preserve the preferred camera. Fallback is only for initial discovery;
        # after receiving pictures, reconnection stays with that same device.
        self.indices = tuple(dict.fromkeys((index, *CAMERA_FALLBACK_INDICES)))
        self.next_index = 0
        self.selected_index = None
        self.pending_index = index
        self.capture = None
        self.frame = None
        self.last_frame_time = None
        self.opened_at = None
        self.status = f"Connecting to camera {index}..."
        self.running = True  # means the worker is alive, not that pictures are available
        self.lock = threading.Lock()
        self.stop = threading.Event()
        # Only this worker opens, reads and releases OpenCV's capture object.
        self.thread = threading.Thread(target=self.keep_reading, daemon=True)
        self.thread.start()

    def set_status(self, message, detail=None):
        """Log changes once, so a connection problem has a useful terminal message."""
        with self.lock:
            changed = message != self.status
            self.status = message
        if changed and message:
            print(message)
            if detail:
                print(detail)  # keep long OpenCV driver details in the terminal

    def open_capture(self):
        """Try one device. isOpened() alone does not prove it produces images."""
        index = self.selected_index
        if index is None:
            index = self.indices[self.next_index]
            self.next_index = (self.next_index + 1) % len(self.indices)
        capture = None
        try:
            capture = open_device(index)
            if not capture.isOpened():
                capture.release()
                self.set_status(f"Camera {index} could not open; retrying. Check other camera apps.")
                return False
        except cv2.error as error:
            if capture is not None:
                capture.release()
            self.set_status(f"Camera {index} could not open; retrying.", str(error))
            return False
        self.capture = capture
        self.pending_index = index
        self.opened_at = time.monotonic()
        self.set_status(f"Camera {index} opened; waiting for its first picture...")
        return True

    def close_capture(self):
        """Clear old pictures and release on the worker, never during another read."""
        if self.capture is not None:
            self.capture.release()
            self.capture = None
        with self.lock:
            self.frame = None
            self.last_frame_time = None

    def keep_reading(self):
        """Tolerate dropped frames, then reopen if the stream stays unavailable."""
        try:
            while not self.stop.is_set():
                if self.capture is None and not self.open_capture():
                    self.stop.wait(CAMERA_RETRY_INTERVAL)
                    continue
                try:
                    ok, frame = self.capture.read()
                except cv2.error as error:
                    ok, frame = False, None
                    self.set_status(f"Camera {self.pending_index} read failed; retrying.", str(error))
                if self.stop.is_set():
                    break
                now = time.monotonic()
                if ok and frame is not None and frame.size > 0:
                    with self.lock:
                        self.frame = frame
                        self.last_frame_time = now
                        recovering = bool(self.status)
                        self.status = ""
                    self.selected_index = self.index = self.pending_index
                    if recovering:
                        print(f"Camera {self.index} is sending pictures.")
                    continue

                # A temporary false/empty read is not a permanent disconnection.
                with self.lock:
                    last_good = self.last_frame_time
                reference = self.opened_at if last_good is None else last_good
                timeout = CAMERA_WARMUP_TIME if last_good is None else CAMERA_RECONNECT_TIME
                if now - reference >= timeout:
                    self.set_status(f"Camera {self.pending_index} stopped sending pictures; reconnecting...")
                    self.close_capture()
                    self.stop.wait(CAMERA_RETRY_INTERVAL)
                else:
                    self.stop.wait(CAMERA_READ_RETRY)
        finally:
            self.close_capture()
            self.running = False

    def read(self):
        """Return a fresh frame copy, or None immediately while awaiting pictures."""
        with self.lock:
            if (self.stop.is_set() or self.frame is None or self.last_frame_time is None
                    or time.monotonic() - self.last_frame_time >= CAMERA_STALE_TIME):
                return None
            # Face overlays must not modify the worker's saved picture.
            return self.frame.copy()

    def release(self):
        """Request shutdown; the worker releases its own capture safely."""
        self.stop.set()
        self.thread.join(timeout=CAMERA_STOP_TIMEOUT)
