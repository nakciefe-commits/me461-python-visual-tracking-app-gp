"""
Head tracker: finds the player's face and says which way the head is pointing.

It answers one question per webcam frame: is the player looking
    DOWN    at the exam paper           (option 1)
    SCREEN  at the monitor              (option 2)
    LEFT    or RIGHT at a neighbour     (option 3)
or is the player gone?

How: MediaPipe's Face Landmarker gives a "transformation matrix" for the face,
which says how the head is rotated. From that we compute two angles:
    yaw    turning left/right   (0 = straight at the camera)
    pitch  nodding up/down      (0 = straight at the camera)
The angles are compared with the player's own "straight at the screen"
angles, which are measured at the start (calibration).
"""

import math

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision

from settings import (FACE_MODEL_FILE, MIN_FACE_CONFIDENCE, FACE_LOST_GRACE,
                      LOST_DOWN_PITCH, YAW_THRESHOLD, PITCH_DOWN_THRESHOLD,
                      YAW_SIGN, PITCH_SIGN, SMOOTHING, HOLD_TIME)

DOWN, SCREEN, LEFT, RIGHT = "DOWN", "SCREEN", "LEFT", "RIGHT"

# Lines drawn on the face by draw_face(): outline, eyes, eyebrows, irises, lips.
_C = vision.FaceLandmarksConnections
FACE_LINES = (_C.FACE_LANDMARKS_FACE_OVAL + _C.FACE_LANDMARKS_LEFT_EYE
              + _C.FACE_LANDMARKS_RIGHT_EYE + _C.FACE_LANDMARKS_LEFT_EYEBROW
              + _C.FACE_LANDMARKS_RIGHT_EYEBROW + _C.FACE_LANDMARKS_LEFT_IRIS
              + _C.FACE_LANDMARKS_RIGHT_IRIS + _C.FACE_LANDMARKS_LIPS)
NOSE_TIP = 1            # landmark number of the tip of the nose
ARROW_LENGTH = 150      # pixels, length of the "where the nose points" arrow


class HeadTracker:
    def __init__(self, load_model=True):
        # load_model=False skips MediaPipe, so the tests can check the
        # direction logic without a camera or model file.
        self.detector = None
        if load_model:
            options = vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_path=FACE_MODEL_FILE),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                output_facial_transformation_matrixes=True,  # we need the head rotation
                # Lower than the default 0.5: a face turned to the side looks
                # less like a face, and we want to keep it while it turns.
                min_face_detection_confidence=MIN_FACE_CONFIDENCE,
                min_face_presence_confidence=MIN_FACE_CONFIDENCE,
                min_tracking_confidence=MIN_FACE_CONFIDENCE,
            )
            self.detector = vision.FaceLandmarker.create_from_options(options)
        self.last_timestamp_ms = 0

        self.yaw = 0.0            # smoothed angles, in degrees
        self.pitch = 0.0
        self.neutral_yaw = 0.0    # the player's "looking at the screen" angles,
        self.neutral_pitch = 0.0  # set by calibrate()

        self.last_seen = None     # time (seconds) of the last frame with a face
        self.last_raw_pitch = 0.0 # unsmoothed pitch of the last frame with a face
        self.landmarks = None     # the 478 face points of the last frame (for drawing)
        self.nose_vector = None   # where the nose points, camera space (for drawing)

        self.direction = SCREEN   # the direction we currently believe
        self.candidate = SCREEN   # a new direction waiting for HOLD_TIME to pass
        self.candidate_since = 0.0
        self.status = ""          # why the face is not tracked right now, for the screen

    # ------------------------------------------------------------------
    # Reading the face
    # ------------------------------------------------------------------
    def read(self, frame, now):
        """
        Find the face in a BGR webcam frame and update yaw and pitch.
        `now` is the current time in seconds. Returns True if a face was found.
        """
        # MediaPipe (VIDEO mode) needs a time in milliseconds that grows
        # with every frame.
        timestamp_ms = max(int(now * 1000), self.last_timestamp_ms + 1)
        self.last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # OpenCV is BGR, MediaPipe wants RGB
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.detector.detect_for_video(mp_image, timestamp_ms)

        if not result.facial_transformation_matrixes:
            self.landmarks = None
            return False

        self.last_seen = now
        self.landmarks = result.face_landmarks[0]

        # The top-left 3x3 of the matrix is the rotation. Its third column is
        # the direction the nose points, in camera space (x right, y up,
        # z towards the camera).
        m = result.facial_transformation_matrixes[0]
        nose_x, nose_y, nose_z = m[0][2], m[1][2], m[2][2]
        self.nose_vector = (nose_x, nose_y)

        # Positive yaw = the player turns to their own left.
        # Positive pitch = the player looks up.
        raw_yaw = YAW_SIGN * math.degrees(math.atan2(nose_x, nose_z))
        raw_pitch = PITCH_SIGN * math.degrees(math.asin(max(-1.0, min(1.0, nose_y))))
        self.last_raw_pitch = raw_pitch

        # Smoothing: move only part of the way towards the new value, so one
        # noisy frame cannot make the angle jump.
        self.yaw += SMOOTHING * (raw_yaw - self.yaw)
        self.pitch += SMOOTHING * (raw_pitch - self.pitch)
        return True

    def face_visible(self, now):
        """
        True if a face was seen in the last FACE_LOST_GRACE seconds.
        The face often vanishes for a few frames in the middle of a head turn;
        this stops those short gaps from counting.
        """
        return self.last_seen is not None and now - self.last_seen <= FACE_LOST_GRACE

    # ------------------------------------------------------------------
    # Angles -> direction
    # ------------------------------------------------------------------
    def reset_tracking(self):
        """A camera gap must not reuse an old 'head down' guess when it returns."""
        self.last_seen = None
        self.landmarks = None
        self.nose_vector = None
        self.yaw = self.neutral_yaw
        self.pitch = self.last_raw_pitch = self.neutral_pitch
        self.direction = self.candidate = SCREEN
        self.candidate_since = 0.0
        self.status = "waiting for camera"
        # Keep calibration and the increasing MediaPipe timestamp across reconnects.

    def calibrate(self, yaw, pitch):
        """Remember these angles as 'looking straight at the screen'."""
        self.neutral_yaw = yaw
        self.neutral_pitch = pitch
        self.direction = self.candidate = SCREEN

    def relative_angles(self):
        """Yaw and pitch measured from the calibrated screen angles."""
        return self.yaw - self.neutral_yaw, self.pitch - self.neutral_pitch

    def raw_direction(self):
        """Classify the current angles, without any hold time."""
        yaw, pitch = self.relative_angles()
        # DOWN is checked first: looking down at the paper wins over a small turn.
        if pitch < -PITCH_DOWN_THRESHOLD:
            return DOWN
        if yaw > YAW_THRESHOLD:
            return LEFT
        if yaw < -YAW_THRESHOLD:
            return RIGHT
        return SCREEN

    def update_direction(self, now):
        """
        Return the direction, changing it only after the new direction has
        lasted HOLD_TIME seconds, so one shaky frame is not a glance.
        """
        new = self.raw_direction()
        if new != self.candidate:
            # Something new: start timing it.
            self.candidate = new
            self.candidate_since = now
        elif new != self.direction and now - self.candidate_since >= HOLD_TIME:
            # It has lasted long enough: believe it.
            self.direction = new
        return self.direction

    def current_direction(self, now, face_found):
        """
        The direction to use this frame, or None if the player is gone and the
        game should pause. `face_found` is what read() returned.
        Also sets self.status, a short note for the screen.
        """
        if face_found:
            self.status = ""
            return self.update_direction(now)

        # Looking down at the paper hides the face (the camera mostly sees
        # the top of the head). So if the face vanished while tilting down,
        # the player is reading the paper, not gone.
        pitch_when_lost = self.last_raw_pitch - self.neutral_pitch
        if self.last_seen is not None and pitch_when_lost < -LOST_DOWN_PITCH:
            self.status = "head down"
            self.direction = self.candidate = DOWN
            return DOWN

        # Lost for a moment (mid-turn): keep the last direction.
        if self.face_visible(now):
            self.status = "face lost..."
            return self.direction

        self.status = "face not found"
        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw_face(self, frame, colour):
        """
        Draw what the tracker sees onto a BGR frame (before mirroring it):
        the face outline, eyes and lips, and an arrow showing where the nose
        points. `colour` is (Blue, Green, Red).
        """
        if self.landmarks is None:
            return
        height, width = frame.shape[:2]
        points = [(int(p.x * width), int(p.y * height)) for p in self.landmarks]

        for line in FACE_LINES:
            cv2.line(frame, points[line.start], points[line.end], colour, 1, cv2.LINE_AA)

        # The arrow goes from the nose tip in the direction the nose points.
        # Camera space has y pointing up, the picture has y pointing down,
        # hence the minus.
        nose_x, nose_y = self.nose_vector
        tip = points[NOSE_TIP]
        end = (int(tip[0] + nose_x * ARROW_LENGTH), int(tip[1] - nose_y * ARROW_LENGTH))
        cv2.arrowedLine(frame, tip, end, colour, 3, cv2.LINE_AA, tipLength=0.25)

    def close(self):
        if self.detector is not None:
            self.detector.close()


class Calibration:
    """
    Measures the player's "looking at the screen" angles: collects the angles
    for `duration` seconds and gives their average to the tracker. If the face
    is lost on the way, it starts over.
    """

    def __init__(self, tracker, duration):
        self.tracker = tracker
        self.duration = duration
        self.restart()

    def restart(self):
        self.yaws = []
        self.pitches = []
        self.elapsed = 0.0

    def done(self):
        return self.elapsed >= self.duration

    def seconds_left(self):
        return max(0.0, self.duration - self.elapsed)

    def add(self, face_visible, dt):
        """Call once per frame while calibrating."""
        if self.done():
            return
        if not face_visible:
            self.restart()
            return
        self.yaws.append(self.tracker.yaw)
        self.pitches.append(self.tracker.pitch)
        self.elapsed += dt
        if self.done():
            self.tracker.calibrate(sum(self.yaws) / len(self.yaws),
                                   sum(self.pitches) / len(self.pitches))
