"""
Head tracker test window: shows which way the head is pointing, for tuning.

Run it with:   .venv/bin/python head_test.py
Keys:          c = recalibrate,  q / Esc = quit

First it calibrates: sit normally and look at the screen for a few seconds.
Then it shows DOWN / SCREEN / LEFT / RIGHT and the angles. If a direction is
wrong, change the numbers in settings.py.
"""

import time

import cv2

from camera import Camera
from head_tracker import HeadTracker, Calibration
from settings import CAMERA_INDEX, CALIBRATION_TIME

WINDOW = "Head tracker test"
last_printed = None   # last direction printed to the terminal

# Colours are (Blue, Green, Red) in OpenCV.
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (0, 0, 255)
YELLOW = (0, 255, 255)


def text(frame, message, y, colour=WHITE, size=0.8, thickness=2):
    cv2.putText(frame, message, (10, y), cv2.FONT_HERSHEY_SIMPLEX, size, colour, thickness)


def main():
    camera = Camera(CAMERA_INDEX)
    if not camera.is_open():
        print("Could not open the webcam. Try changing CAMERA_INDEX in settings.py.")
        return

    tracker = HeadTracker()
    calibration = Calibration(tracker, CALIBRATION_TIME)
    start_time = time.time()
    previous_time = start_time
    last_timestamp_ms = -1

    while True:
        frame = camera.read()
        if frame is None:
            print("The webcam stopped sending pictures.")
            break

        now = time.time()
        dt = now - previous_time
        previous_time = now

        # MediaPipe needs a timestamp that grows on every frame.
        timestamp_ms = max(int((now - start_time) * 1000), last_timestamp_ms + 1)
        last_timestamp_ms = timestamp_ms
        face_found = tracker.read_angles(frame, timestamp_ms)
        face_visible = tracker.face_visible(timestamp_ms)  # short gaps don't count
        tracker.draw_face(frame, GREEN if face_found else YELLOW)

        # Mirror for display only; detection already ran on the real frame.
        frame = cv2.flip(frame, 1)

        if not calibration.done():
            calibration.add(face_visible, dt)
            text(frame, "Look at the screen", 60, YELLOW, 1.2, 3)
            if face_visible:
                text(frame, f"Calibrating... {calibration.seconds_left():.1f}", 110, YELLOW)
            else:
                text(frame, "FACE NOT FOUND", 110, RED)
        else:
            show_direction(frame, tracker, now, timestamp_ms, face_found)

        text(frame, f"FPS: {1 / max(dt, 0.001):.0f}", frame.shape[0] - 15, GREEN, 0.6, 1)
        text(frame, "c = recalibrate   q = quit", frame.shape[0] - 45, WHITE, 0.6, 1)

        cv2.imshow(WINDOW, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 = Esc
            break
        if key == ord("c"):
            calibration.restart()
        # Stop when the window's X button is clicked (imshow would reopen it).
        if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
            break

    camera.release()
    tracker.close()
    cv2.destroyAllWindows()


def show_direction(frame, tracker, now, timestamp_ms, face_found):
    """Write the direction, angles and tracking state onto the (mirrored) frame."""
    global last_printed
    direction = tracker.current_direction(now, timestamp_ms, face_found)
    if direction is None:
        text(frame, "FACE NOT FOUND", 60, RED, 1.5, 3)
        return

    if not face_found and tracker.lost_while_looking_down():
        text(frame, "face hidden, head down -> DOWN", 180, YELLOW, 0.6, 1)
    elif not face_found:
        text(frame, "face lost... (keeping last direction)", 180, YELLOW, 0.6, 1)

    yaw, pitch = tracker.relative_angles()
    text(frame, direction, 60, GREEN, 1.8, 4)
    text(frame, f"yaw {yaw:+.1f}  pitch {pitch:+.1f}", 110)
    text(frame, f"raw: {tracker.raw_direction()}", 145, WHITE, 0.6, 1)
    # Print to the terminal only when the direction changes.
    if direction != last_printed:
        print(direction)
        last_printed = direction


if __name__ == "__main__":
    main()
