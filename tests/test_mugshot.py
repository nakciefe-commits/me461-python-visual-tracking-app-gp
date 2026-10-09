"""Tests for mugshot.py: cutting the face out of the webcam picture."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.mugshot import crop_box
from settings import MUGSHOT_FACE_ZOOM

W, H = 640, 480   # a webcam frame
ASPECT = 0.75     # a 3:4 photo


class CropBoxTests(unittest.TestCase):
    def test_face_in_the_middle(self):
        face = (0.4, 0.3, 0.6, 0.6)   # 144 pixels tall, centred at x = 320
        x, y, width, height = crop_box(face, W, H, ASPECT)
        self.assertAlmostEqual(height, 0.3 * H * MUGSHOT_FACE_ZOOM, delta=1)
        self.assertAlmostEqual(width / height, ASPECT, delta=0.01)
        self.assertAlmostEqual(x + width / 2, 320, delta=1)
        # The face is inside the photo.
        self.assertLessEqual(y, 0.3 * H)
        self.assertGreaterEqual(y + height, 0.6 * H)

    def test_face_at_the_edge_stays_inside(self):
        x, y, width, height = crop_box((0.85, 0.0, 1.0, 0.2), W, H, ASPECT)
        self.assertGreaterEqual(x, 0)
        self.assertGreaterEqual(y, 0)
        self.assertLessEqual(x + width, W)
        self.assertLessEqual(y + height, H)

    def test_huge_face_is_shrunk_to_fit(self):
        x, y, width, height = crop_box((0.1, 0.0, 0.9, 1.0), W, H, ASPECT)
        self.assertLessEqual(height, H)
        self.assertLessEqual(width, W)
        self.assertAlmostEqual(width / height, ASPECT, delta=0.01)

    def test_no_face_uses_the_middle(self):
        x, y, width, height = crop_box(None, W, H, ASPECT)
        self.assertEqual(height, H)
        self.assertAlmostEqual(x + width / 2, W / 2, delta=1)


if __name__ == "__main__":
    unittest.main()
