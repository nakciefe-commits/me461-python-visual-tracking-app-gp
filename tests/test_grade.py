"""Tests for the semester's letter grade in grade.py (no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.grade import (curve, class_average, z_score, letter_for_z, letter_for_share,
                         semester_grade, LETTERS, FAIL)
from settings import GRADES, GRADE_CURVE_MIN

# A class of earlier runs, as many as the curve needs: average 10000, spread 2000.
CLASS = [8000, 12000] * GRADE_CURVE_MIN


class GradeTests(unittest.TestCase):
    def test_no_curve_without_enough_runs(self):
        self.assertIsNone(curve([5000] * (GRADE_CURVE_MIN - 1)))
        self.assertEqual(curve(CLASS), (10000, 2000))

    def test_average_run_is_the_pass_letter_for_z_zero(self):
        self.assertEqual(semester_grade(10000, 0.0, CLASS), letter_for_z(0))

    def test_better_total_is_never_a_worse_grade(self):
        ranks = [LETTERS.index(semester_grade(total, 0.0, CLASS))
                 for total in range(1000, 20001, 500)]
        self.assertEqual(ranks, sorted(ranks, reverse=True))

    def test_far_above_the_class_is_the_best_grade(self):
        self.assertEqual(semester_grade(10**6, 0.0, CLASS), LETTERS[0])

    def test_far_below_the_class_fails(self):
        self.assertEqual(semester_grade(1, 1.0, CLASS), FAIL)

    def test_zero_total_always_fails(self):
        self.assertEqual(semester_grade(0, 1.0, []), FAIL)
        self.assertEqual(semester_grade(0, 1.0, [0] * GRADE_CURVE_MIN), FAIL)

    def test_each_z_threshold(self):
        for letter, least, _ in GRADES[:-1]:
            self.assertEqual(letter_for_z(least), letter)

    def test_without_a_class_the_share_decides(self):
        for letter, _, least in GRADES[:-1]:
            self.assertEqual(semester_grade(5000, least, []), letter)
        self.assertEqual(letter_for_share(-1), FAIL)

    def test_all_equal_class(self):
        same = [7000] * GRADE_CURVE_MIN
        self.assertEqual(z_score(7000, *curve(same)), 0)
        self.assertGreater(z_score(7001, *curve(same)), 0)

    def test_class_average(self):
        self.assertIsNone(class_average([]))
        self.assertEqual(class_average([1000, 2001]), 1500)


if __name__ == "__main__":
    unittest.main()
