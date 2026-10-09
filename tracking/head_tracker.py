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
angles, which are measured at the start (calibration). Calibration also
measures how far this player turns left, right and down, and sets the
thresholds from that (see Calibration at the bottom).
"""

import math
from collections import deque

import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision

from settings import (FACE_MODEL_FILE, MIN_FACE_CONFIDENCE, FACE_LOST_GRACE,
                      LOST_DOWN_PITCH, LOST_DOWN_SPEED, PITCH_TREND_TIME, YAW_THRESHOLD, PITCH_DOWN_THRESHOLD,
                      YAW_SIGN, PITCH_SIGN, SMOOTHING, HOLD_TIME, CALIBRATION_SAMPLE_TIME,
                      CALIBRATION_SHARE, CALIBRATION_MIN_ANGLE, CALIBRATION_MAX_ANGLE)

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
            # We read the model file ourselves and hand MediaPipe the bytes.
            # Giving it the file name instead fails on Windows when the folder
            # path has letters like ç, ş or ı in it.
            with open(FACE_MODEL_FILE, "rb") as model_file:
                model = model_file.read()
            options = vision.FaceLandmarkerOptions(
                base_options=mp.tasks.BaseOptions(model_asset_buffer=model),
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
        # Degrees from the neutral angles at which a direction starts. The
        # fixed ones from settings.py until calibration measures this player.
        self.left_threshold = YAW_THRESHOLD
        self.right_threshold = YAW_THRESHOLD
        self.down_threshold = PITCH_DOWN_THRESHOLD

        self.last_seen = None     # time (seconds) of the last frame with a face
        self.last_raw_pitch = 0.0 # unsmoothed pitch of the last frame with a face
        self.pitch_history = deque()   # (time, raw pitch) of the last PITCH_TREND_TIME seconds with a face
        self.landmarks = None     # the 478 face points of the last frame (for drawing)
        self.nose_vector = None   # where the nose points, camera space (for drawing)
        self.raw_yaw = 0.0        # unsmoothed angles of the last frame with a face (debug panel)
        self.raw_pitch = 0.0
        self.rotation = None      # the head's 3x3 rotation matrix from MediaPipe (debug panel)

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
        self.rotation = [[m[row][col] for col in range(3)] for row in range(3)]
        nose_x, nose_y, nose_z = m[0][2], m[1][2], m[2][2]
        self.nose_vector = (nose_x, nose_y)

        # Positive yaw = the player turns to their own left.
        # Positive pitch = the player looks up.
        raw_yaw = YAW_SIGN * math.degrees(math.atan2(nose_x, nose_z))
        raw_pitch = PITCH_SIGN * math.degrees(math.asin(max(-1.0, min(1.0, nose_y))))
        self.last_raw_pitch = raw_pitch
        self.raw_yaw, self.raw_pitch = raw_yaw, raw_pitch
        self.remember_pitch(now, raw_pitch)

        # Smoothing: move only part of the way towards the new value, so one
        # noisy frame cannot make the angle jump.
        self.yaw += SMOOTHING * (raw_yaw - self.yaw)
        self.pitch += SMOOTHING * (raw_pitch - self.pitch)
        return True

    def remember_pitch(self, now, raw_pitch):
        """Keep the last PITCH_TREND_TIME seconds of pitch, to see which way the head is moving."""
        self.pitch_history.append((now, raw_pitch))
        while now - self.pitch_history[0][0] > PITCH_TREND_TIME:
            self.pitch_history.popleft()

    def pitch_speed(self):
        """
        How fast the head was nodding in the last frames with a face, in
        degrees per second (negative = going down); 0 if not enough frames.
        """
        if len(self.pitch_history) < 2:
            return 0.0
        (first_time, first_pitch), (last_time, last_pitch) = self.pitch_history[0], self.pitch_history[-1]
        if last_time <= first_time:
            return 0.0
        return (last_pitch - first_pitch) / (last_time - first_time)

    def went_down(self):
        """
        True if the face vanished on its way down to the paper: it was
        already tilted down (LOST_DOWN_PITCH), or it was moving down fast
        (LOST_DOWN_SPEED) - a quick nod loses the face before it is far down.
        """
        if self.last_seen is None:
            return False
        pitch_when_lost = self.last_raw_pitch - self.neutral_pitch
        return pitch_when_lost < -LOST_DOWN_PITCH or self.pitch_speed() < -LOST_DOWN_SPEED

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
        self.pitch_history.clear()   # an old nod must not count after the gap
        self.direction = self.candidate = SCREEN
        self.candidate_since = 0.0
        self.status = "waiting for camera"
        # Keep calibration and the increasing MediaPipe timestamp across reconnects.

    def calibrate(self, yaw, pitch):
        """Remember these angles as 'looking straight at the screen'."""
        self.neutral_yaw = yaw
        self.neutral_pitch = pitch
        self.direction = self.candidate = SCREEN

    def set_thresholds(self, left, right, down):
        """The degrees (from neutral) at which LEFT, RIGHT and DOWN start."""
        self.left_threshold = left
        self.right_threshold = right
        self.down_threshold = down

    def relative_angles(self):
        """Yaw and pitch measured from the calibrated screen angles."""
        return self.yaw - self.neutral_yaw, self.pitch - self.neutral_pitch

    def raw_direction(self):
        """Classify the current angles, without any hold time."""
        yaw, pitch = self.relative_angles()
        # DOWN is checked first: looking down at the paper wins over a small turn.
        if pitch < -self.down_threshold:
            return DOWN
        if yaw > self.left_threshold:
            return LEFT
        if yaw < -self.right_threshold:
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
        # the top of the head). So if the face vanished while tilting down
        # (or while moving down fast), the player is reading the paper, not gone.
        if self.went_down():
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
    def draw_face(self, frame, colour, box_colour=None):
        """
        Draw what the tracker sees onto a BGR frame (before mirroring it):
        the face outline, eyes and lips, and an arrow showing where the nose
        points. `colour` is (Blue, Green, Red). With box_colour, also the
        box around all the face points (face_box(), the debug panel).
        """
        if self.landmarks is None:
            return
        height, width = frame.shape[:2]
        points = [(int(p.x * width), int(p.y * height)) for p in self.landmarks]
        if box_colour is not None:
            left, top, right, bottom = self.face_box()
            cv2.rectangle(frame, (int(left * width), int(top * height)),
                          (int(right * width), int(bottom * height)), box_colour, 1)

        for line in FACE_LINES:
            cv2.line(frame, points[line.start], points[line.end], colour, 1, cv2.LINE_AA)

        # The arrow goes from the nose tip in the direction the nose points.
        # Camera space has y pointing up, the picture has y pointing down,
        # hence the minus.
        nose_x, nose_y = self.nose_vector
        tip = points[NOSE_TIP]
        end = (int(tip[0] + nose_x * ARROW_LENGTH), int(tip[1] - nose_y * ARROW_LENGTH))
        cv2.arrowedLine(frame, tip, end, colour, 3, cv2.LINE_AA, tipLength=0.25)

    def face_box(self):
        """
        Where the face is in the last frame, as (left, top, right, bottom),
        each 0..1 of the frame's width/height (unmirrored), or None if no
        face was found. For cropping the mugshot photo.
        """
        if self.landmarks is None:
            return None
        xs = [p.x for p in self.landmarks]
        ys = [p.y for p in self.landmarks]
        return min(xs), min(ys), max(xs), max(ys)

    def close(self):
        if self.detector is not None:
            self.detector.close()


# The poses calibration asks for, in order.
CALIBRATION_POSES = (SCREEN, LEFT, RIGHT, DOWN)


def pose_threshold(reached, default):
    """
    The threshold for one direction, from how far (degrees from neutral,
    positive = the right way) the player turned in that pose: a share of
    the way there, within the limits in settings.py. A pose that went the
    wrong way, or hardly moved, cannot be trusted: then `default`.
    """
    if reached * CALIBRATION_SHARE < CALIBRATION_MIN_ANGLE:
        return default
    return min(CALIBRATION_MAX_ANGLE, reached * CALIBRATION_SHARE)


class Calibration:
    """
    Measures the player's four poses, one after the other (CALIBRATION_POSES):
    looking at the screen, then turned left, right and down as far as they
    would in the game while still seeing the screen. For each pose the
    player gets into it and presses Space (start()); the angles are then
    collected for `duration` seconds and averaged.

    - SCREEN becomes the neutral angles (everything is measured from them).
    - LEFT, RIGHT and DOWN set the thresholds (pose_threshold()).

    If the face is lost while measuring, that pose starts over, except DOWN:
    looking down often hides the face, so the last angles seen are used.
    """

    def __init__(self, tracker, duration=CALIBRATION_SAMPLE_TIME):
        self.tracker = tracker
        self.duration = duration
        self.restart()

    def restart(self):
        """From the first pose again."""
        self.step = 0
        self.reached = {}   # pose -> its average (yaw, pitch)
        self.restart_pose()

    def restart_pose(self):
        """Measure the current pose again (Space must be pressed again)."""
        self.measuring = False
        self.yaws = []
        self.pitches = []
        self.elapsed = 0.0

    def pose(self):
        """The pose being asked for (SCREEN, LEFT, RIGHT, DOWN), or None when done."""
        return None if self.done() else CALIBRATION_POSES[self.step]

    def start(self):
        """Space: the player is in the pose, measure it now."""
        if not self.done():
            self.measuring = True

    def done(self):
        return self.step >= len(CALIBRATION_POSES)

    def progress(self):
        """0..1, how far the current pose's measuring is."""
        return min(1.0, self.elapsed / self.duration)

    def add(self, face_visible, dt):
        """Call once per frame while calibrating."""
        if self.done() or not self.measuring:
            return
        if not face_visible and (self.pose() != DOWN or self.tracker.last_seen is None):
            self.restart_pose()
            return
        self.yaws.append(self.tracker.yaw)
        self.pitches.append(self.tracker.pitch)
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finish_pose()

    def finish_pose(self):
        """The pose is measured: keep its average; after the last one, set the tracker."""
        average = (sum(self.yaws) / len(self.yaws), sum(self.pitches) / len(self.pitches))
        self.reached[self.pose()] = average
        if self.pose() == SCREEN:
            # Measured first, because the other poses are measured from it.
            self.tracker.calibrate(*average)
        self.step += 1
        self.restart_pose()
        if self.done():
            self.set_thresholds()

    def set_thresholds(self):
        """All four poses are in: give the tracker this player's thresholds."""
        neutral_yaw, neutral_pitch = self.reached[SCREEN]
        # Positive = the right way: yaw grows to the player's left, pitch grows upwards.
        left = self.reached[LEFT][0] - neutral_yaw
        right = neutral_yaw - self.reached[RIGHT][0]
        down = neutral_pitch - self.reached[DOWN][1]
        self.tracker.set_thresholds(pose_threshold(left, YAW_THRESHOLD),
                                    pose_threshold(right, YAW_THRESHOLD),
                                    pose_threshold(down, PITCH_DOWN_THRESHOLD))
