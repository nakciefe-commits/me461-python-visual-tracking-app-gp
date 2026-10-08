"""Tests for run_intro.py: the intro's lines and beats, timed to the character music."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.run_intro import (INTRO_LINES, BEAT, BAR, line_time, current_line, since_line, is_over,
                             since_beat, beat_number, since_bar)
from settings import CHARACTER_MUSIC_BPM, INTRO_FIRST_HIT, INTRO_DROP


class RunIntroTests(unittest.TestCase):
    def test_bar_is_four_beats(self):
        self.assertAlmostEqual(BEAT, 60 / CHARACTER_MUSIC_BPM)
        self.assertAlmostEqual(BAR, 4 * BEAT)

    def test_lines_come_one_per_bar(self):
        self.assertIsNone(current_line(INTRO_FIRST_HIT - 0.01))
        self.assertEqual(current_line(INTRO_FIRST_HIT), 0)
        self.assertEqual(current_line(INTRO_FIRST_HIT + BAR + 0.01), 1)
        self.assertAlmostEqual(since_line(INTRO_FIRST_HIT + BAR + 0.25), 0.25)

    def test_every_line_comes_before_the_drop(self):
        self.assertLess(line_time(len(INTRO_LINES) - 1), INTRO_DROP)
        self.assertFalse(is_over(INTRO_DROP - 0.01))
        self.assertTrue(is_over(INTRO_DROP))

    def test_drop_is_on_a_beat(self):
        # The measured drop must sit on the beat grid, or the thumps would be off.
        off = since_beat(INTRO_DROP)
        self.assertLess(min(off, BEAT - off), 0.05)

    def test_beats_and_bars(self):
        self.assertAlmostEqual(since_beat(INTRO_FIRST_HIT + 2 * BEAT + 0.1), 0.1)
        self.assertEqual(beat_number(INTRO_FIRST_HIT + 2 * BEAT + 0.1), 2)
        self.assertAlmostEqual(since_bar(INTRO_FIRST_HIT + BAR + 0.2), 0.2)


if __name__ == "__main__":
    unittest.main()
