"""Tests for the sound helpers in ui/sounds.py that only do numbers (no sound device needed)."""

import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ui.sounds import (cut_sound, fade_out, heartbeat, far_away, marker, SAMPLE_RATE, SOUND_LENGTHS,
                       SOUND_DUCKS)
from settings import (EXAM_TITLE_TIME, HEARTBEAT_BPM, HEARTBEAT_TIME, FAR_MUSIC_ECHO, FAR_MUSIC_CUTOFF,
                      MUGSHOT_WRITE_TIME)


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


class HeartbeatTests(unittest.TestCase):
    def test_length_and_loudness(self):
        wave = heartbeat(HEARTBEAT_BPM, HEARTBEAT_TIME)
        self.assertEqual(len(wave), int(SAMPLE_RATE * HEARTBEAT_TIME))
        self.assertLessEqual(np.abs(wave).max(), 1.0)
        self.assertGreater(np.abs(wave).max(), 0.5)   # hard, not a whisper

    def test_beats_at_the_tempo(self):
        # Count the beats: the moments the wave jumps up after a quiet stretch.
        wave = np.abs(heartbeat(120, 2.0))
        gap = SAMPLE_RATE // 2   # 120 bpm = a beat every half second
        for beat in range(3):
            self.assertGreater(wave[beat * gap:beat * gap + 2000].max(), 0.5)
            self.assertLess(wave[beat * gap + int(gap * 0.6):beat * gap + int(gap * 0.95)].max(), 0.05)

    def test_music_ducks_for_as_long_as_it_lasts(self):
        self.assertEqual(SOUND_DUCKS["heartbeat"], HEARTBEAT_TIME)
        self.assertEqual(SOUND_LENGTHS["heartbeat"], HEARTBEAT_TIME)


class FarAwayTests(unittest.TestCase):
    def setUp(self):
        t = np.arange(SAMPLE_RATE) / SAMPLE_RATE
        self.low = np.sin(2 * np.pi * FAR_MUSIC_CUTOFF / 4 * t)    # a low note
        self.high = np.sin(2 * np.pi * FAR_MUSIC_CUTOFF * 8 * t)   # a high note

    def test_echo_makes_it_longer_and_stays_as_loud(self):
        far = far_away(self.low, SAMPLE_RATE)
        self.assertEqual(len(far), SAMPLE_RATE + int(SAMPLE_RATE * FAR_MUSIC_ECHO))
        self.assertAlmostEqual(np.abs(far).max(), np.abs(self.low).max())
        self.assertGreater(np.abs(far[SAMPLE_RATE + 1000:SAMPLE_RATE + 3000]).max(), 0.01)   # echo after the end

    def test_high_notes_are_muffled(self):
        mixed = far_away(self.low + self.high, SAMPLE_RATE)
        low_only = far_away(self.low, SAMPLE_RATE)
        # Adding the high note barely changes anything: it was cut.
        self.assertLess(np.abs(mixed / np.abs(mixed).max() - low_only).max(), 0.1)

    def test_stereo(self):
        far = far_away(np.column_stack([self.low, self.low]), SAMPLE_RATE)
        self.assertEqual(far.shape[1], 2)



class MarkerTests(unittest.TestCase):
    def test_lasts_as_long_as_the_writing(self):
        wave = marker(MUGSHOT_WRITE_TIME, 12)
        self.assertAlmostEqual(len(wave) / SAMPLE_RATE, MUGSHOT_WRITE_TIME, delta=0.02)
        self.assertLessEqual(np.abs(wave).max(), 1.0)
        self.assertEqual(SOUND_LENGTHS["pen"], MUGSHOT_WRITE_TIME)

    def test_strokes_have_gaps(self):
        # Silent stretches between the strokes: the marker is lifted.
        wave = marker(MUGSHOT_WRITE_TIME, 12)
        silent = np.abs(wave) < 1e-9
        self.assertGreater(silent.mean(), 0.15)
        self.assertLess(silent.mean(), 0.4)

if __name__ == "__main__":
    unittest.main()
