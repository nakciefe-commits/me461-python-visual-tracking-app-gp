"""Tests for exam_paper.py: the answer key and the grade (right +1, wrong -0.5, blank 0)."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.exam_paper import ExamPaper, LETTERS, UNKNOWN, BLANK, CORRECT, WRONG, EMPTY
from tracking.head_tracker import LEFT, RIGHT
from settings import (ANSWERS_NEEDED, POINTS_CORRECT, POINTS_WRONG, POINTS_BLANK, MAX_SAME_LETTER,
                      MAX_SIDE_STREAK)


def paper_with_key(letter="B", side=LEFT):
    paper = ExamPaper(random.Random(1))
    paper.right_letters = [letter] * ANSWERS_NEEDED
    paper.knowing_side = [side] * ANSWERS_NEEDED
    return paper


class ExamPaperTests(unittest.TestCase):
    def test_answer_key_is_random_but_valid(self):
        paper = ExamPaper(random.Random(1))
        self.assertEqual(len(paper.right_letters), ANSWERS_NEEDED)
        self.assertTrue(set(paper.right_letters) <= set(LETTERS))
        self.assertTrue(set(paper.knowing_side) <= {LEFT, RIGHT})

    def test_only_the_knowing_side_says_the_letter(self):
        paper = paper_with_key("D", LEFT)
        self.assertEqual(paper.says(LEFT), "D")
        self.assertEqual(paper.says(RIGHT), UNKNOWN)

    def test_writing_moves_to_the_next_question(self):
        paper = paper_with_key()
        paper.write("A")
        paper.write(BLANK)
        self.assertEqual(paper.question(), 2)
        self.assertFalse(paper.is_full())

    def test_full_paper_says_nothing_more(self):
        paper = paper_with_key()
        for _ in range(ANSWERS_NEEDED):
            paper.write("B")
        self.assertTrue(paper.is_full())
        self.assertIsNone(paper.says(LEFT))

    def test_results(self):
        paper = paper_with_key("B")
        for answer in ["B", "C", BLANK]:
            paper.write(answer)
        self.assertEqual(paper.results(), [CORRECT, WRONG, EMPTY])
        self.assertEqual((paper.count(CORRECT), paper.count(WRONG), paper.count(EMPTY)), (1, 1, 1))

    def test_points(self):
        paper = paper_with_key("B")
        for answer in ["B", "B", "A", BLANK, "C"]:   # 2 right, 2 wrong, 1 blank
            paper.write(answer)
        self.assertEqual(paper.points(), 2 * POINTS_CORRECT + 2 * POINTS_WRONG + POINTS_BLANK)

    def test_all_wrong_goes_below_zero(self):
        paper = paper_with_key("B")
        for _ in range(ANSWERS_NEEDED):
            paper.write("A")
        self.assertLess(paper.points(), 0)


class NoStreakTests(unittest.TestCase):
    """The answer key is random, but never "A A A B" (checked on many seeds)."""

    def test_no_letter_twice_in_a_row(self):
        for seed in range(500):
            letters = ExamPaper(random.Random(seed)).right_letters
            for before, after in zip(letters, letters[1:]):
                self.assertNotEqual(before, after, f"seed {seed}: {letters}")

    def test_no_letter_too_often(self):
        for seed in range(500):
            letters = ExamPaper(random.Random(seed)).right_letters
            for letter in LETTERS:
                self.assertLessEqual(letters.count(letter), MAX_SAME_LETTER)

    def test_side_streaks_are_short(self):
        for seed in range(500):
            sides = ExamPaper(random.Random(seed)).knowing_side
            for i in range(len(sides) - MAX_SIDE_STREAK):
                self.assertGreater(len(set(sides[i:i + MAX_SIDE_STREAK + 1])), 1, f"seed {seed}: {sides}")

    def test_still_random(self):
        # Every letter still comes first sometimes, and both sides know answers.
        firsts = {ExamPaper(random.Random(seed)).right_letters[0] for seed in range(200)}
        self.assertEqual(firsts, set(LETTERS))
        sides = {ExamPaper(random.Random(seed)).knowing_side[0] for seed in range(200)}
        self.assertEqual(sides, {LEFT, RIGHT})


if __name__ == "__main__":
    unittest.main()
