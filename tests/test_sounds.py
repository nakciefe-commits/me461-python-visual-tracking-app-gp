"""Tests for the sound helpers in ui/sounds.py that only do numbers (no sound device needed)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ui.sounds import cut_sound, fade_out, SOUND_LENGTHS
from settings import EXAM_TITLE_TIME


class CutSoundTests(unittest.TestCase):
    def test_cut_to_length_with_a_fade(self):
        cut = cut_sound(np.ones(1000), 600, 100)
        self.assertEqual(len(cut), 600)
        self.assertEqual(cut[0], 1.0)
        self.assertEqual(cut[-1], 0.0)          # faded out to silence
        self.assertEqual(cut[499], 1.0)         # untouched before the fade

    def test_short_sound_is_padded(self):
        cut = cut_sound(np.ones(100), 300, 10)
        self.assertEqual(len(cut), 300)
        self.assertEqual(cut[150], 0.0)

    def test_stereo(self):
        cut = cut_sound(np.ones((1000, 2)), 500, 50)
        self.assertEqual(cut.shape, (500, 2))
        self.assertEqual(cut[-1, 1], 0.0)

    def test_fade_shape(self):
        shape = fade_out(10, 4)
        self.assertEqual(list(shape[:6]), [1.0] * 6)
        self.assertEqual(shape[-1], 0.0)

    def test_bell_lasts_as_long_as_the_title_card(self):
        self.assertEqual(SOUND_LENGTHS["bell"], EXAM_TITLE_TIME)


if __name__ == "__main__":
    unittest.main()
