"""
Body tracker: opens the webcam, finds the body joints, draws a skeleton.

Run it with:   .venv/bin/python tracker.py
Quit with:     q  (or Esc, or the window's X button)

The program is one loop that repeats about 30 times a second:
    1. grab one picture (a "frame") from the webcam
    2. ask MediaPipe where the body joints are in that picture
    3. draw the joints and the bones between them
    4. show the picture on screen
"""

import time

import cv2                      # OpenCV: webcam, drawing, windows
import mediapipe as mp          # MediaPipe: finds the body joints
from mediapipe.tasks.python import vision

# ----------------------------------------------------------------------------
# Settings
# ----------------------------------------------------------------------------
CAMERA_INDEX = 0                      # 0 = first webcam. Try 1 if it is the wrong one.
MODEL_FILE = "pose_landmarker.task"   # the trained neural network MediaPipe uses
MIN_VISIBILITY = 0.5                  # ignore joints the model is less than 50% sure about

# Colours are (Blue, Green, Red) in OpenCV, not (Red, Green, Blue)!
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
RED = (0, 0, 255)

# MediaPipe gives every joint a number from 0 to 32. "J" lets us use names
# instead, e.g. J.LEFT_WRIST is 15.
J = vision.PoseLandmark

# The "bones": each pair is two joints we connect with a line.
BONES = [
    (J.LEFT_SHOULDER, J.RIGHT_SHOULDER),
    (J.LEFT_SHOULDER, J.LEFT_ELBOW),
    (J.LEFT_ELBOW, J.LEFT_WRIST),
    (J.RIGHT_SHOULDER, J.RIGHT_ELBOW),
    (J.RIGHT_ELBOW, J.RIGHT_WRIST),
    (J.LEFT_SHOULDER, J.LEFT_HIP),
    (J.RIGHT_SHOULDER, J.RIGHT_HIP),
    (J.LEFT_HIP, J.RIGHT_HIP),
    (J.LEFT_HIP, J.LEFT_KNEE),
    (J.LEFT_KNEE, J.LEFT_ANKLE),
    (J.RIGHT_HIP, J.RIGHT_KNEE),
    (J.RIGHT_KNEE, J.RIGHT_ANKLE),
]


def create_detector():
    """Load the model file and return the object that finds body joints."""
    options = vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_FILE),
        # VIDEO mode: the detector remembers the previous frame, which makes
        # tracking smoother and faster than treating every frame as a new photo.
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,  # track one person
    )
    return vision.PoseLandmarker.create_from_options(options)


def find_joints(detector, frame, timestamp_ms):
    """
    Return the list of 33 joints found in the frame, or None if nobody is seen.

    Each joint has:
        .x, .y       position as a fraction of the picture (0.0 to 1.0),
                     x=0 is the left edge, y=0 is the TOP edge
        .visibility  how sure the model is that the joint is visible (0.0 to 1.0)
    """
    # OpenCV stores colours as BGR, MediaPipe expects RGB, so we convert.
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect_for_video(mp_image, timestamp_ms)

    if not result.pose_landmarks:   # empty list = no person found
        return None
    return result.pose_landmarks[0]  # [0] = the first (and only) person


def to_pixels(joint, width, height):
    """Turn a joint's 0.0-1.0 position into a pixel position on the picture."""
    return int(joint.x * width), int(joint.y * height)


def draw_skeleton(frame, joints):
    """Draw the bones as lines and the joints as dots, directly onto the frame."""
    height, width = frame.shape[:2]

    for start, end in BONES:
        a, b = joints[start], joints[end]
        if a.visibility > MIN_VISIBILITY and b.visibility > MIN_VISIBILITY:
            cv2.line(frame, to_pixels(a, width, height), to_pixels(b, width, height), WHITE, 3)

    for joint in joints:
        if joint.visibility > MIN_VISIBILITY:
            cv2.circle(frame, to_pixels(joint, width, height), 6, GREEN, -1)  # -1 = filled


def main():
    camera = cv2.VideoCapture(CAMERA_INDEX)
    if not camera.isOpened():
        print("Could not open the webcam. Try changing CAMERA_INDEX.")
        return

    detector = create_detector()
    start_time = time.time()
    previous_time = start_time

    while True:
        # 1. Grab a frame. "ok" is False if the camera gave us nothing.
        ok, frame = camera.read()
        if not ok:
            print("The webcam stopped sending pictures.")
            break

        # 2. Find the joints. The detector needs to know when the frame was
        #    taken, in milliseconds since we started.
        now = time.time()
        timestamp_ms = int((now - start_time) * 1000)
        joints = find_joints(detector, frame, timestamp_ms)

        # 3. Draw.
        if joints is not None:
            draw_skeleton(frame, joints)

        # Flip left-right so the window behaves like a mirror. We do this AFTER
        # detection, otherwise the model would mix up your left and right side.
        frame = cv2.flip(frame, 1)

        # Text goes on after the flip, otherwise it would be mirrored too.
        fps = 1 / max(now - previous_time, 0.001)  # frames per second; max() avoids dividing by zero
        previous_time = now
        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 2)
        if joints is None:
            cv2.putText(frame, "No person found", (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, RED, 2)

        # 4. Show the frame, then wait 1 ms for a key press.
        cv2.imshow("Body tracker", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # 27 = Esc
            break
        # Also stop when the window's X button is clicked. Without this check,
        # imshow would simply open the window again on the next frame.
        if cv2.getWindowProperty("Body tracker", cv2.WND_PROP_VISIBLE) < 1:
            break

    # Give the webcam back to the system and close the window.
    camera.release()
    detector.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
