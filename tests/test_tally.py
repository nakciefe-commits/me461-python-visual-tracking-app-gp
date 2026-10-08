"""Tests for tally.py: the end screen's score count, one part at a time."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from settings import (TALLY_START, TALLY_STEP_TIME, TALLY_COUNT_TIME, TALLY_FX_FULL_SCORE,
                      TALLY_JACKPOT_SHARE)
from logic.tally import (appear_time, parts_shown, is_done, running_score, running_value, is_counting,
                         strength, jackpot)

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


class SlotScoreTests(unittest.TestCase):
    """The numbers behind the slot-machine score."""

    def test_value_rolls_smoothly(self):
        # A third of the way through counting the first part: a third of it.
        third = TALLY_START + TALLY_COUNT_TIME / 3
        self.assertAlmostEqual(running_value(PARTS, third), 1000 / 3)
        self.assertEqual(running_score(PARTS, third), 333)

    def test_counting_only_while_a_part_counts_up(self):
        self.assertFalse(is_counting(PARTS, 0.0))
        self.assertTrue(is_counting(PARTS, TALLY_START + TALLY_COUNT_TIME / 2))
        self.assertFalse(is_counting(PARTS, 100.0))

    def test_strength_grows_with_the_score(self):
        self.assertEqual(strength(0), 0.0)
        self.assertEqual(strength(-500), 0.0)
        self.assertAlmostEqual(strength(TALLY_FX_FULL_SCORE / 2), 0.5)
        self.assertEqual(strength(TALLY_FX_FULL_SCORE * 10), 1.0)
        # A run's total is the sum of its exams, so it needs more.
        self.assertAlmostEqual(strength(TALLY_FX_FULL_SCORE, exams=3), 1 / 3)

    def test_jackpot_only_for_big_scores(self):
        self.assertFalse(jackpot(TALLY_FX_FULL_SCORE * TALLY_JACKPOT_SHARE - 1))
        self.assertTrue(jackpot(TALLY_FX_FULL_SCORE * TALLY_JACKPOT_SHARE))


if __name__ == "__main__":
    unittest.main()
