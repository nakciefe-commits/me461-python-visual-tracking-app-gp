"""Tests for the game rules in game.py (no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import Game, PLAYING, WON, LOST
from head_tracker import DOWN, SCREEN, LEFT, RIGHT

# 1/8 s per step: adds up exactly in floating point, so 20 steps are exactly 2.5 s.
DT = 0.125


def run(game, direction, seconds):
    """Call update() for `seconds` of game time; return all events."""
    events = []
    for _ in range(round(seconds / DT)):
        events += game.update(direction, DT)
    return events


class CopyingTests(unittest.TestCase):
    def test_copy_time_fills_one_answer(self):
        game = Game()
        events = run(game, LEFT, 2.5)
        self.assertEqual(game.answers, 1)
        self.assertEqual(events.count("answer"), 1)

    def test_progress_bar_fills(self):
        game = Game()
        run(game, RIGHT, 1.25)
        self.assertAlmostEqual(game.copy_progress, 0.5)

    def test_looking_away_resets_progress(self):
        game = Game()
        run(game, LEFT, 2.375)
        run(game, DOWN, 0.125)
        run(game, LEFT, 0.25)
        self.assertEqual(game.answers, 0)

    def test_must_look_away_between_answers(self):
        game = Game()
        run(game, LEFT, 5.0)
        self.assertEqual(game.answers, 1)

    def test_five_answers_wins(self):
        game = Game()
        events = []
        for _ in range(5):
            events += run(game, LEFT, 2.5)
            events += run(game, DOWN, 0.125)
        self.assertEqual(game.state, WON)
        self.assertIn("won", events)

    def test_ticks_while_copying(self):
        game = Game()
        events = run(game, RIGHT, 1.0)
        # One tick right at the start, then one every 0.3 s: 3 or 4 in 1 s
        # depending on how the frames line up.
        self.assertIn(events.count("tick"), (3, 4))


class StaringTests(unittest.TestCase):
    def test_grace_time_is_free(self):
        game = Game()
        run(game, SCREEN, 2.875)
        self.assertEqual(game.suspicion, 0)

    def test_suspicion_fills_after_grace(self):
        game = Game()
        run(game, SCREEN, 4.0)
        self.assertGreater(game.suspicion, 0)
        self.assertLess(game.suspicion, 1)

    def test_warning_after_grace_plus_fill(self):
        game = Game()
        events = run(game, SCREEN, 5.0)
        self.assertEqual(game.warnings, 1)
        self.assertIn("warning", events)
        self.assertIsNotNone(game.popup_text)

    def test_popup_disappears(self):
        game = Game()
        run(game, SCREEN, 5.0)
        run(game, DOWN, 2.0)
        self.assertIsNone(game.popup_text)

    def test_three_warnings_lose(self):
        game = Game()
        events = run(game, SCREEN, 15.0)
        self.assertEqual(game.state, LOST)
        self.assertEqual(game.lose_reason, "warnings")
        self.assertIn("lost", events)

    def test_looking_down_resets_staring(self):
        game = Game()
        run(game, SCREEN, 4.0)
        run(game, DOWN, 0.125)
        self.assertEqual(game.stare_time, 0)
        self.assertEqual(game.suspicion, 0)


class GameOverTests(unittest.TestCase):
    def test_nothing_happens_after_game_over(self):
        game = Game()
        run(game, SCREEN, 15.0)
        self.assertEqual(run(game, LEFT, 5.0), [])
        self.assertEqual(game.answers, 0)

    def test_reset(self):
        game = Game()
        run(game, SCREEN, 15.0)
        game.reset()
        self.assertEqual(game.state, PLAYING)
        self.assertEqual((game.answers, game.warnings), (0, 0))


if __name__ == "__main__":
    unittest.main()
