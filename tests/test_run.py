"""Tests for run.py: three exams in a row, their moods and the total score."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.game import WON, LOST
from logic.run import Run
from settings import QUIZZES, MOODS, ANSWERS_NEEDED
from tracking.head_tracker import DOWN


def hand_in(game, letter="A"):
    """Write `letter` for every question, looking down: the exam is handed in."""
    while game.state != WON:
        game.write(letter, DOWN)


class RunTests(unittest.TestCase):
    def test_exams_come_in_order_with_their_own_time_and_questions(self):
        run = Run(random.Random(1))
        for quiz in QUIZZES:
            game = run.new_game()
            self.assertEqual(game.exam_time, quiz["time"])
            self.assertEqual(game.paper.size(), quiz["questions"])
            self.assertEqual(run.quiz()["title"], quiz["title"])
            hand_in(game)
            run.finish_quiz(game)
        self.assertTrue(run.is_over())

    def test_each_exam_picks_one_of_its_two_moods(self):
        for seed in range(10):
            run = Run(random.Random(seed))
            for quiz, mood in zip(QUIZZES, run.moods):
                self.assertIn(mood, quiz["moods"])
                self.assertIn(mood, MOODS)

    def test_gossip_matches_the_mood(self):
        run = Run(random.Random(2))
        self.assertEqual(run.gossip(), MOODS[run.mood()])

    def test_every_mood_tells_a_story(self):
        # The hallway gossip screen needs a gossip, a story and at most 3
        # +/- lines, all short enough to fit.
        for name, mood in MOODS.items():
            self.assertTrue(mood["gossip"], name)
            self.assertTrue(1 <= len(mood["story"]) <= 3, name)
            self.assertLessEqual(len(mood["good"]) + len(mood["bad"]), 3, name)
            for line in mood["story"] + mood["good"] + mood["bad"]:
                self.assertLessEqual(len(line), 70, (name, line))

    def test_moods_get_worse_exam_by_exam(self):
        # The Quiz: only good (or plain) days; the Midterm: good and bad;
        # the Final: only bad days.
        quiz, midterm, final = QUIZZES
        for name in quiz["moods"]:
            self.assertEqual(MOODS[name]["bad"], [], name)
        for name in midterm["moods"]:
            self.assertTrue(MOODS[name]["good"] and MOODS[name]["bad"], name)
        for name in final["moods"]:
            self.assertEqual(MOODS[name]["good"], [], name)
            self.assertTrue(MOODS[name]["bad"], name)

    def test_the_chosen_mood_is_in_the_pool(self):
        run = Run(random.Random(7))
        self.assertIs(run.pool()[run.chosen()], run.gossip())

    def test_failed_exam_scores_zero_and_the_run_goes_on(self):
        run = Run(random.Random(3))
        game = run.new_game()
        game.lose("caught", [])
        run.finish_quiz(game)
        self.assertEqual(run.results[0]["score"], 0)
        self.assertFalse(run.results[0]["handed_in"])
        self.assertEqual(run.results[0]["lose_reason"], "caught")
        self.assertFalse(run.is_over())
        self.assertEqual(run.number(), 1)

    def test_total_is_the_sum(self):
        run = Run(random.Random(4))
        scores = []
        for _ in QUIZZES:
            game = run.new_game()
            hand_in(game, "B")
            scores.append(game.score())
            run.finish_quiz(game)
        self.assertEqual(run.total(), sum(scores))
        self.assertEqual([points for _, points in run.score_parts()], scores)

    def test_every_new_exam_starts_clean(self):
        run = Run(random.Random(5))
        game = run.new_game()
        game.warnings = 2
        run.finish_quiz(game)
        self.assertEqual(run.new_game().warnings, 0)

    def test_each_exam_gets_more_suspicious(self):
        points = [quiz["suspicious"] for quiz in QUIZZES]
        self.assertEqual(points, sorted(points, reverse=True))
        self.assertEqual(len(set(points)), len(points))
        run = Run(random.Random(6))
        self.assertEqual(run.new_game().suspicious_at, QUIZZES[0]["suspicious"])

    def test_quizzes_fit_the_paper(self):
        # The paper picture has ANSWERS_NEEDED lines.
        for quiz in QUIZZES:
            self.assertLessEqual(quiz["questions"], ANSWERS_NEEDED)


if __name__ == "__main__":
    unittest.main()
