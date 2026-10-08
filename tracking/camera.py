"""
Webcam reader with background startup, frame retries and automatic reconnection.

Reading a frame from the webcam means waiting about 20 ms for the camera.
Instead of making the game wait, a background "thread" (a second worker
inside the same program) reads frames all the time and keeps the newest one.
The game takes a copy of the newest picture without waiting. Missing or stale
pictures pause the game while this worker retries, instead of closing it.

On Windows there are two camera systems (camera_systems()): DirectShow,
which opens a webcam quickly, and Media Foundation, Windows' own, which is
slow to open but works with every webcam. Each webcam is tried with both
before the next webcam is tried, so a webcam that only works with one of
them still works without changing any setting. Windows also gets a small
picture size and a one-picture buffer (less delay), and, when a webcam
opens but sends nothing, a hint about Windows' camera privacy setting.
"""

import sys
import threading
import time

import cv2

from settings import (WINDOWS_DIRECTSHOW, WINDOWS_CAMERA_SIZE, CAMERA_FALLBACK_INDICES, CAMERA_WARMUP_TIME,
                      CAMERA_STALE_TIME, CAMERA_RECONNECT_TIME, CAMERA_RETRY_INTERVAL,
                      CAMERA_READ_RETRY, CAMERA_STOP_TIMEOUT)


# The camera systems' names, for the messages.
SYSTEM_NAMES = {cv2.CAP_DSHOW: "DirectShow", cv2.CAP_MSMF: "Media Foundation"}
PRIVACY_HINT = ("Windows: Settings > Privacy & security > Camera > allow desktop apps "
                "to use the camera. Close other apps that use it (Teams, Zoom, browser).")


def camera_systems():
    """
    The camera systems to try, in order. None = let OpenCV choose (Linux,
    Mac). On Windows: DirectShow first (it opens a webcam in a moment;
    Media Foundation can take 10+ seconds), then Media Foundation (it works
    with every webcam), or the other way round with WINDOWS_DIRECTSHOW = False.
    """
    if sys.platform != "win32":
        return [None]
    if WINDOWS_DIRECTSHOW:
        return [cv2.CAP_DSHOW, cv2.CAP_MSMF]
    return [cv2.CAP_MSMF, cv2.CAP_DSHOW]


def open_device(index, system=None):
    """
    Open webcam number `index` with OpenCV, with that camera system (None =
    OpenCV chooses). On Windows it also asks for WINDOWS_CAMERA_SIZE and a
    buffer of one picture, so the game always gets the newest one.
    """
    if system is None:
        return cv2.VideoCapture(index)
    capture = cv2.VideoCapture(index, system)
    width, height = WINDOWS_CAMERA_SIZE
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def describe(index, system):
    """'Camera 0', or 'Camera 0 (DirectShow)' on Windows."""
    return f"Camera {index}" if system is None else f"Camera {index} ({SYSTEM_NAMES.get(system, system)})"


class Camera:
    def __init__(self, index):
        self.index = index
        # Preserve the preferred camera. Fallback is only for initial discovery;
        # after receiving pictures, reconnection stays with that same device.
        self.indices = tuple(dict.fromkeys((index, *CAMERA_FALLBACK_INDICES)))
        # Every (webcam, camera system) to try, the preferred webcam's first.
        self.attempts = [(i, system) for i in self.indices for system in camera_systems()]
        self.next_attempt = 0
        self.selected_index = None
        self.selected_system = None
        self.pending_index = index
        self.pending_system = self.attempts[0][1]
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
        index, system = self.selected_index, self.selected_system
        if index is None:
            index, system = self.attempts[self.next_attempt]
            self.next_attempt = (self.next_attempt + 1) % len(self.attempts)
        name = describe(index, system)
        capture = None
        try:
            capture = open_device(index, system)
            if not capture.isOpened():
                capture.release()
                self.set_status(f"{name} could not open; retrying. Check other camera apps.",
                                PRIVACY_HINT if system is not None else None)
                return False
        except cv2.error as error:
            if capture is not None:
                capture.release()
            self.set_status(f"{name} could not open; retrying.", str(error))
            return False
        self.capture = capture
        self.pending_index, self.pending_system = index, system
        self.opened_at = time.monotonic()
        self.set_status(f"{name} opened; waiting for its first picture...")
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
                    self.set_status(f"{describe(self.pending_index, self.pending_system)} read failed; retrying.", str(error))
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
                    self.selected_system = self.pending_system
                    if recovering:
                        print(f"{describe(self.index, self.selected_system)} is sending pictures.")
                    continue

                # A temporary false/empty read is not a permanent disconnection.
                with self.lock:
                    last_good = self.last_frame_time
                reference = self.opened_at if last_good is None else last_good
                timeout = CAMERA_WARMUP_TIME if last_good is None else CAMERA_RECONNECT_TIME
                if now - reference >= timeout:
                    name = describe(self.pending_index, self.pending_system)
                    if last_good is None and self.pending_system is not None:
                        # Opened but never sent a picture: on Windows that is
                        # often the privacy setting, or the other camera system works.
                        self.set_status(f"{name} sends no pictures; trying the next way. {PRIVACY_HINT}")
                    else:
                        self.set_status(f"{name} stopped sending pictures; reconnecting...")
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
