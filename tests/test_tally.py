"""Tests for tally.py: the end screen's score count, one part at a time."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from settings import TALLY_START, TALLY_STEP_TIME, TALLY_COUNT_TIME
from logic.tally import appear_time, parts_shown, is_done, running_score

PARTS = [("Q1", 1000), ("Q2", -500), ("TIME", 300)]
LAST = appear_time(len(PARTS) - 1)


class TallyTests(unittest.TestCase):
    def test_parts_appear_one_by_one(self):
        self.assertEqual(parts_shown(PARTS, 0.0), 0)
        self.assertEqual(parts_shown(PARTS, TALLY_START), 1)
        self.assertEqual(parts_shown(PARTS, TALLY_START + TALLY_STEP_TIME), 2)
        self.assertEqual(parts_shown(PARTS, 100.0), len(PARTS))

    def test_score_counts_up(self):
        self.assertEqual(running_score(PARTS, 0.0), 0)
        halfway = TALLY_START + TALLY_COUNT_TIME / 2
        self.assertEqual(running_score(PARTS, halfway), 500)
        self.assertEqual(running_score(PARTS, TALLY_START + TALLY_COUNT_TIME), 1000)

    def test_done_shows_the_real_score(self):
        self.assertFalse(is_done(PARTS, LAST))
        self.assertTrue(is_done(PARTS, LAST + TALLY_COUNT_TIME))
        self.assertEqual(running_score(PARTS, LAST + TALLY_COUNT_TIME), 800)

    def test_final_score_never_below_zero(self):
        parts = [("Q1", -500), ("Q2", -500)]
        self.assertEqual(running_score(parts, 100.0), 0)

    def test_nothing_to_count_is_done(self):
        self.assertTrue(is_done([], 0.0))
        self.assertEqual(running_score([], 0.0), 0)


if __name__ == "__main__":
    unittest.main()
