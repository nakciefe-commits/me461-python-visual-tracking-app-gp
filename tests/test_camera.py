"""Dropped-frame, warm-up, reconnect and shutdown tests without a real webcam."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tracking.camera import Camera
from settings import (CAMERA_STALE_TIME, CAMERA_RECONNECT_TIME,
                      CAMERA_STOP_TIMEOUT, CAMERA_WARMUP_TIME)


class CameraTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.image = np.ones((2, 3, 3), dtype=np.uint8)
        self.factory = self.start_patch('tracking.camera.cv2.VideoCapture')
        self.start_patch('tracking.camera.threading.Thread')
        self.start_patch('tracking.camera.time.monotonic', side_effect=lambda: self.now)
        self.start_patch('builtins.print')
        self.start_patch('tracking.camera.CAMERA_FALLBACK_INDICES', (0,))
        self.camera = Camera(1)
        # Run the worker synchronously with a fake clock; no sleeps or races.
        self.start_patch('tracking.camera.threading.Event.wait', side_effect=self.advance_time)

    def start_patch(self, name, *args, **kwargs):
        patcher = patch(name, *args, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def advance_time(self, delay):
        self.now += delay
        return False

    def capture(self, opened=True):
        capture = MagicMock()
        capture.isOpened.return_value = opened
        return capture

    def finish_on_next_read(self, capture, check):
        """Assert state after a successful picture, then let the worker stop."""
        calls = 0

        def read():
            nonlocal calls
            calls += 1
            if calls == 1:
                return True, self.image
            check()
            self.camera.stop.set()
            return False, None

        capture.read.side_effect = read

    def test_startup_read_does_not_wait_for_the_worker(self):
        self.camera.thread.start.assert_called_once()
        self.assertIsNone(self.camera.read())
        self.factory.assert_not_called()  # opening happens on the worker

    def test_frame_copy_prevents_face_overlay_from_changing_saved_picture(self):
        self.camera.frame = self.image
        self.camera.last_frame_time = self.now
        copy = self.camera.read()
        copy[:] = 0
        np.testing.assert_array_equal(self.camera.frame, self.image)
        self.assertTrue(np.all(self.camera.frame == 1))

    def test_stale_and_stopped_cameras_do_not_return_old_pictures(self):
        self.camera.frame = self.image
        self.camera.last_frame_time = self.now
        self.now += CAMERA_STALE_TIME
        self.assertIsNone(self.camera.read())
        self.camera.last_frame_time = self.now
        self.camera.stop.set()
        self.assertIsNone(self.camera.read())

    def test_one_dropped_frame_is_retried_without_closing_capture(self):
        capture = self.capture()
        self.factory.return_value = capture
        results = [(False, None), (True, self.image)]

        def read():
            if results:
                return results.pop(0)
            self.assertTrue(self.camera.running)
            np.testing.assert_array_equal(self.camera.read(), self.image)
            capture.release.assert_not_called()
            self.camera.stop.set()
            return False, None

        capture.read.side_effect = read
        self.camera.keep_reading()
        self.factory.assert_called_once_with(1)
        capture.release.assert_called_once()
        self.assertFalse(self.camera.running)

    def test_empty_frames_and_opencv_read_error_are_retried(self):
        capture = self.capture()
        self.factory.return_value = capture
        results = [(True, None), (True, np.empty((0, 0, 3))),
                   cv2.error('temporary read error'), (True, self.image)]

        def read():
            if results:
                result = results.pop(0)
                if isinstance(result, Exception):
                    raise result
                return result
            np.testing.assert_array_equal(self.camera.read(), self.image)
            self.camera.stop.set()
            return False, None

        capture.read.side_effect = read
        self.camera.keep_reading()
        self.factory.assert_called_once_with(1)

    def test_unopened_preferred_device_falls_back_to_zero(self):
        preferred, fallback = self.capture(False), self.capture()
        self.factory.side_effect = [preferred, fallback]
        self.finish_on_next_read(fallback,
                                 lambda: self.assertEqual(self.camera.selected_index, 0))
        self.camera.keep_reading()
        self.assertEqual([call.args for call in self.factory.call_args_list], [(1,), (0,)])
        preferred.release.assert_called_once()
        fallback.release.assert_called_once()

    def test_opened_camera_without_frames_is_not_treated_as_working(self):
        preferred, fallback = self.capture(), self.capture()
        self.factory.side_effect = [preferred, fallback]

        def no_picture():
            self.now += CAMERA_WARMUP_TIME
            return False, None

        preferred.read.side_effect = no_picture
        self.finish_on_next_read(fallback,
                                 lambda: self.assertEqual(self.camera.index, 0))
        self.camera.keep_reading()
        self.assertEqual([call.args for call in self.factory.call_args_list], [(1,), (0,)])
        preferred.release.assert_called_once()

    def test_initial_failed_reads_allow_the_camera_to_warm_up(self):
        capture = self.capture()
        self.factory.return_value = capture
        reads = 0

        def read():
            nonlocal reads
            reads += 1
            if reads == 1:
                self.now += CAMERA_WARMUP_TIME / 2
                return False, None
            if reads == 2:
                return True, self.image
            np.testing.assert_array_equal(self.camera.read(), self.image)
            self.camera.stop.set()
            return False, None

        capture.read.side_effect = read
        self.camera.keep_reading()
        self.factory.assert_called_once_with(1)

    def test_long_gap_reopens_same_device_and_recovers(self):
        original, reconnected = self.capture(), self.capture()
        self.factory.side_effect = [original, reconnected]
        reads = 0

        def disconnect():
            nonlocal reads
            reads += 1
            if reads == 1:
                return True, self.image
            self.now += CAMERA_RECONNECT_TIME
            self.assertIsNone(self.camera.read())
            return False, None

        original.read.side_effect = disconnect
        self.finish_on_next_read(reconnected,
                                 lambda: np.testing.assert_array_equal(self.camera.read(), self.image))
        self.camera.keep_reading()
        self.assertEqual([call.args for call in self.factory.call_args_list], [(1,), (1,)])
        original.release.assert_called_once()
        reconnected.release.assert_called_once()

    def test_open_exception_can_recover_on_next_attempt(self):
        fallback = self.capture()
        self.factory.side_effect = [cv2.error('temporary open error'), fallback]
        self.finish_on_next_read(fallback,
                                 lambda: self.assertEqual(self.camera.index, 0))
        self.camera.keep_reading()
        self.assertEqual(self.factory.call_count, 2)

    def test_release_requests_worker_shutdown_without_racing_capture_read(self):
        capture = self.capture()
        self.camera.capture = capture
        self.camera.release()
        self.assertTrue(self.camera.stop.is_set())
        self.camera.thread.join.assert_called_once_with(timeout=CAMERA_STOP_TIMEOUT)
        capture.release.assert_not_called()  # only the worker may release it


if __name__ == '__main__':
    unittest.main()
