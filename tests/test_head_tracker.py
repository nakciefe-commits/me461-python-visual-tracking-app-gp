"""Tests for the direction logic in head_tracker.py (no camera needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tracking.head_tracker import (HeadTracker, Calibration, pose_threshold, DOWN, SCREEN, LEFT,
                                   RIGHT)
from settings import (PITCH_DOWN_THRESHOLD, YAW_THRESHOLD, HOLD_TIME, CALIBRATION_SHARE,
                      CALIBRATION_MIN_ANGLE, CALIBRATION_MAX_ANGLE)

# Clearly past the "down" threshold, whatever it is set to in settings.py.
LOOKING_DOWN = -(PITCH_DOWN_THRESHOLD + 5)


def tracker_at(yaw, pitch):
    tracker = HeadTracker(load_model=False)
    tracker.yaw, tracker.pitch = yaw, pitch
    return tracker


class RawDirectionTests(unittest.TestCase):
    def test_neutral_is_screen(self):
        self.assertEqual(tracker_at(0, 0).raw_direction(), SCREEN)

    def test_left_right_down(self):
        self.assertEqual(tracker_at(30, 0).raw_direction(), LEFT)
        self.assertEqual(tracker_at(-30, 0).raw_direction(), RIGHT)
        self.assertEqual(tracker_at(0, LOOKING_DOWN).raw_direction(), DOWN)

    def test_down_wins_over_turn(self):
        self.assertEqual(tracker_at(30, LOOKING_DOWN).raw_direction(), DOWN)

    def test_looking_up_is_screen(self):
        self.assertEqual(tracker_at(0, 25).raw_direction(), SCREEN)

    def test_uses_calibration(self):
        tracker = tracker_at(30, 0)
        tracker.calibrate(30 - (YAW_THRESHOLD - 5), 0)   # less than YAW_THRESHOLD from neutral
        self.assertEqual(tracker.raw_direction(), SCREEN)


class HoldTimeTests(unittest.TestCase):
    def test_new_direction_needs_hold_time(self):
        tracker = tracker_at(30, 0)
        self.assertEqual(tracker.update_direction(0.0), SCREEN)
        self.assertEqual(tracker.update_direction(HOLD_TIME / 2), SCREEN)
        self.assertEqual(tracker.update_direction(HOLD_TIME + 0.05), LEFT)

    def test_one_frame_flicker_is_ignored(self):
        tracker = tracker_at(30, 0)
        tracker.update_direction(0.0)
        tracker.yaw = 0
        for t in (0.05, 0.1, 0.2, 0.3, 0.5):
            self.assertEqual(tracker.update_direction(t), SCREEN)


class FaceVisibleTests(unittest.TestCase):
    def test_never_seen(self):
        self.assertFalse(tracker_at(0, 0).face_visible(1.0))

    def test_short_gap_still_visible(self):
        tracker = tracker_at(0, 0)
        tracker.last_seen = 1.0
        self.assertTrue(tracker.face_visible(1.5))     # 0.5 s gap
        self.assertFalse(tracker.face_visible(1.7))    # 0.7 s gap


class LostFaceTests(unittest.TestCase):
    """What current_direction() does when the face disappears."""

    def lost_after(self, raw_pitch):
        tracker = tracker_at(0, 0)
        tracker.last_seen = 1.0
        tracker.last_raw_pitch = raw_pitch
        return tracker

    def test_found_face_is_tracked(self):
        tracker = tracker_at(0, 0)
        self.assertEqual(tracker.current_direction(1.0, True), SCREEN)
        self.assertEqual(tracker.status, "")

    def test_lost_while_tilting_down_is_down(self):
        tracker = self.lost_after(-15)
        self.assertEqual(tracker.current_direction(1.1, False), DOWN)
        self.assertEqual(tracker.status, "head down")

    def test_down_lasts_while_face_is_hidden(self):
        # Reading the paper for 10 s must not pause the game.
        tracker = self.lost_after(-15)
        self.assertEqual(tracker.current_direction(11.0, False), DOWN)

    def test_short_gap_keeps_last_direction(self):
        tracker = self.lost_after(0)
        tracker.direction = LEFT
        self.assertEqual(tracker.current_direction(1.3, False), LEFT)
        self.assertEqual(tracker.status, "face lost...")

    def test_long_gap_pauses(self):
        tracker = self.lost_after(0)
        self.assertIsNone(tracker.current_direction(2.0, False))

    def test_uses_calibrated_pitch(self):
        tracker = self.lost_after(-15)
        tracker.calibrate(0, -10)   # only 5 degrees below this player's neutral
        self.assertIsNone(tracker.current_direction(2.0, False))

    def test_camera_gap_clears_old_down_guess_but_preserves_calibration_and_timestamp(self):
        tracker = self.lost_after(-15)
        tracker.calibrate(12, -3)
        tracker.last_timestamp_ms = 1234
        tracker.direction = DOWN
        tracker.reset_tracking()
        self.assertIsNone(tracker.current_direction(2.0, False))
        self.assertEqual(tracker.relative_angles(), (0, 0))
        self.assertEqual((tracker.neutral_yaw, tracker.neutral_pitch), (12, -3))
        self.assertEqual(tracker.last_timestamp_ms, 1234)


class CalibrationTests(unittest.TestCase):
    # 0.125 adds up exactly in floating point (0.1 would not reach 1.0)
    STEP = 0.125

    def measure(self, calibration, yaw, pitch, face_visible=True):
        """Hold a pose (these angles), press Space, and wait until it is measured."""
        calibration.tracker.yaw, calibration.tracker.pitch = yaw, pitch
        calibration.start()
        for _ in range(int(calibration.duration / self.STEP)):
            calibration.add(face_visible, self.STEP)

    def test_screen_pose_averages_angles(self):
        tracker = tracker_at(10, -4)
        tracker.last_seen = 0.0
        calibration = Calibration(tracker, 1.0)
        calibration.start()
        for _ in range(4):
            calibration.add(True, self.STEP)
        tracker.yaw, tracker.pitch = 20, -6
        for _ in range(4):
            calibration.add(True, self.STEP)
        self.assertEqual(calibration.pose(), LEFT)   # on to the next pose
        self.assertAlmostEqual(tracker.neutral_yaw, 15)
        self.assertAlmostEqual(tracker.neutral_pitch, -5)

    def test_nothing_is_measured_before_space(self):
        calibration = Calibration(tracker_at(0, 0), 1.0)
        for _ in range(20):
            calibration.add(True, self.STEP)
        self.assertEqual(calibration.pose(), SCREEN)
        self.assertEqual(calibration.progress(), 0)

    def test_four_poses_set_the_thresholds(self):
        tracker = tracker_at(0, 0)
        tracker.last_seen = 0.0
        calibration = Calibration(tracker, 1.0)
        self.measure(calibration, 5, 2)        # screen
        self.measure(calibration, 35, 2)       # left: 30 degrees from the screen
        self.measure(calibration, -20, 2)      # right: 25 degrees
        self.measure(calibration, 5, -38)      # down: 40 degrees
        self.assertTrue(calibration.done())
        self.assertAlmostEqual(tracker.left_threshold, 30 * CALIBRATION_SHARE)
        self.assertAlmostEqual(tracker.right_threshold, 25 * CALIBRATION_SHARE)
        self.assertAlmostEqual(tracker.down_threshold, min(CALIBRATION_MAX_ANGLE, 40 * CALIBRATION_SHARE))
        # And the game uses them: a turn a bit past the left threshold is LEFT.
        tracker.yaw, tracker.pitch = 5 + 30 * CALIBRATION_SHARE + 1, 2
        self.assertEqual(tracker.raw_direction(), LEFT)

    def test_lost_face_measures_the_pose_again(self):
        tracker = tracker_at(0, 0)
        tracker.last_seen = 0.0
        calibration = Calibration(tracker, 1.0)
        calibration.start()
        for _ in range(6):
            calibration.add(True, self.STEP)
        calibration.add(False, self.STEP)
        self.assertEqual(calibration.pose(), SCREEN)
        self.assertEqual(calibration.progress(), 0)
        self.assertFalse(calibration.measuring)   # Space again

    def test_down_pose_survives_a_hidden_face(self):
        # Looking down often hides the face: the last angles seen are used.
        tracker = tracker_at(0, 0)
        tracker.last_seen = 0.0
        calibration = Calibration(tracker, 1.0)
        self.measure(calibration, 0, 0)
        self.measure(calibration, 25, 0)
        self.measure(calibration, -25, 0)
        self.measure(calibration, 0, -30, face_visible=False)
        self.assertTrue(calibration.done())

    def test_wrong_way_keeps_the_default(self):
        self.assertEqual(pose_threshold(-10, YAW_THRESHOLD), YAW_THRESHOLD)
        tiny = (CALIBRATION_MIN_ANGLE / CALIBRATION_SHARE) - 1   # hardly moved
        self.assertEqual(pose_threshold(tiny, YAW_THRESHOLD), YAW_THRESHOLD)

    def test_threshold_limits(self):
        self.assertEqual(pose_threshold(200, YAW_THRESHOLD), CALIBRATION_MAX_ANGLE)
        self.assertGreaterEqual(pose_threshold(CALIBRATION_MIN_ANGLE / CALIBRATION_SHARE, 0),
                                CALIBRATION_MIN_ANGLE)


if __name__ == "__main__":
    unittest.main()
