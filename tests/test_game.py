"""Tests for the game rules in game.py (no camera or window needed)."""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import Game, PLAYING, WON, LOST, WARNING_TIME
from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import EXAM_TIME, ANSWERS_NEEDED, CAUGHT_TIME, COPY_TIME, SUSPICION_DRAIN_TIME

# 1/8 s per step: adds up exactly in floating point, so 20 steps are exactly 2.5 s.
# Times come from settings.py, so tuning them does not break the tests.
DT = 0.125


def run(game, direction, seconds):
    """Call update() for `seconds` of game time; return all events."""
    events = []
    for _ in range(math.ceil(seconds / DT - 1e-9)):   # at least `seconds`
        events += game.update(direction, DT)
    return events


class CopyingTests(unittest.TestCase):
    def test_copy_time_fills_one_answer(self):
        game = Game()
        events = run(game, LEFT, COPY_TIME)
        self.assertEqual(game.answers, 1)
        self.assertEqual(events.count("answer"), 1)

    def test_copy_time_counts_up(self):
        game = Game()
        run(game, RIGHT, 1.25)
        self.assertAlmostEqual(game.copy_time, 1.25)

    def test_looking_away_keeps_progress(self):
        game = Game()
        run(game, LEFT, 1.0)
        run(game, DOWN, 2.0)
        self.assertAlmostEqual(game.copy_time, 1.0)

    def test_copy_in_pieces(self):
        game = Game()
        run(game, LEFT, COPY_TIME / 2)
        run(game, DOWN, 1.0)
        events = run(game, RIGHT, COPY_TIME / 2)
        self.assertEqual(game.answers, 1)
        self.assertEqual(events[0], "tick")   # ticking starts again right away

    def test_must_look_away_between_answers(self):
        game = Game()
        run(game, LEFT, 5.0)
        self.assertEqual(game.answers, 1)

    def test_five_answers_wins(self):
        game = Game()
        events = []
        for _ in range(5):
            events += run(game, LEFT, COPY_TIME)
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
    def test_no_warning_before_warning_time(self):
        game = Game()
        run(game, SCREEN, WARNING_TIME - DT)
        self.assertEqual(game.warnings, 0)
        self.assertAlmostEqual(game.suspicion(), (WARNING_TIME - DT) / WARNING_TIME)

    def test_warning_after_grace_plus_fill(self):
        game = Game()
        events = run(game, SCREEN, WARNING_TIME)
        self.assertEqual(game.warnings, 1)
        self.assertIn("warning", events)
        self.assertIsNotNone(game.popup_text)
        self.assertEqual(game.suspicion(), 0)   # a warning starts the bar over

    def test_popup_disappears(self):
        game = Game()
        run(game, SCREEN, 5.0)
        run(game, DOWN, 2.0)
        self.assertIsNone(game.popup_text)

    def test_three_warnings_lose(self):
        game = Game()
        events = run(game, SCREEN, 15.0)
        self.assertEqual(game.state, LOST)
        self.assertIn("lost", events)

    def test_looking_down_drains_slowly(self):
        # Not reset at once: the bar jumping to empty would give away the teacher.
        game = Game()
        run(game, SCREEN, 4.0)
        run(game, DOWN, 1.0)
        self.assertAlmostEqual(game.suspicion(),
                               4.0 / WARNING_TIME - 1.0 / SUSPICION_DRAIN_TIME)
        run(game, DOWN, SUSPICION_DRAIN_TIME)
        self.assertEqual(game.suspicion(), 0)


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
        self.assertEqual(game.time_left, EXAM_TIME)
        self.assertIsNone(game.lose_reason)

    def test_three_warnings_reason(self):
        game = Game()
        events = run(game, SCREEN, 15.0)
        self.assertEqual(game.lose_reason, "warnings")
        self.assertIn("lost_warnings", events)


class FakeTeacher:
    """Stands in for Teacher: the test decides what it is doing."""

    def __init__(self, watching=False, facing=False):
        self.watching = watching
        self.facing = facing

    def is_watching(self):
        return self.watching

    def is_facing_class(self):
        return self.facing


def run_with(game, direction, seconds, teacher):
    events = []
    for _ in range(math.ceil(seconds / DT - 1e-9)):   # at least `seconds`
        events += game.update(direction, DT, teacher)
    return events


class TeacherRuleTests(unittest.TestCase):
    def test_copying_while_watched_is_caught(self):
        game = Game()
        events = run_with(game, LEFT, CAUGHT_TIME, FakeTeacher(watching=True, facing=True))
        self.assertEqual(game.state, LOST)
        self.assertEqual(game.lose_reason, "caught")
        self.assertIn("caught", events)
        self.assertIn("lost", events)
        self.assertIn("lost_caught", events)

    def test_seen_copying_fills_suspicion_fast(self):
        game = Game()
        events = run_with(game, LEFT, 2 * DT, FakeTeacher(watching=True, facing=True))
        self.assertEqual(game.state, PLAYING)
        self.assertEqual(events.count("spotted"), 1)   # the alarm plays once
        self.assertAlmostEqual(game.suspicion(), 2 * DT / CAUGHT_TIME)

    def test_looking_away_in_time_escapes(self):
        game = Game()
        teacher = FakeTeacher(watching=True, facing=True)
        almost_caught = (math.ceil(CAUGHT_TIME / DT) - 1) * DT   # last step before full
        run_with(game, LEFT, almost_caught, teacher)
        run_with(game, DOWN, 1.0, teacher)
        self.assertEqual(game.state, PLAYING)

    def test_bar_drains_slowly_after_being_seen(self):
        game = Game()
        run_with(game, LEFT, 2 * DT, FakeTeacher(watching=True, facing=True))
        self.assertTrue(game.seen_copying)   # drawn red
        run_with(game, LEFT, 1.0, FakeTeacher(watching=False))   # teacher busy again
        self.assertAlmostEqual(game.suspicion(),
                               2 * DT / CAUGHT_TIME - 1.0 / SUSPICION_DRAIN_TIME)
        run_with(game, DOWN, SUSPICION_DRAIN_TIME, FakeTeacher())
        self.assertEqual(game.suspicion(), 0)
        self.assertFalse(game.seen_copying)

    def test_glances_add_up(self):
        # The bar only drains slowly, so quick risky glances in a row can
        # still get you caught.
        game = Game()
        teacher = FakeTeacher(watching=True, facing=True)
        run_with(game, LEFT, 2 * DT, teacher)
        run_with(game, DOWN, 1.0, teacher)
        self.assertGreater(game.suspicion(), 0)
        events = run_with(game, RIGHT, CAUGHT_TIME, teacher)
        self.assertIn("spotted", events)   # the alarm plays again on each glance
        self.assertEqual(game.lose_reason, "caught")

    def test_staring_after_being_seen_keeps_rising(self):
        game = Game()
        teacher = FakeTeacher(watching=True, facing=True)
        run_with(game, LEFT, 2 * DT, teacher)
        before = game.suspicion()
        run_with(game, SCREEN, 1.0, teacher)
        self.assertAlmostEqual(game.suspicion(), before + 1.0 / WARNING_TIME)

    def test_staring_fills_the_bar_to_a_warning_not_caught(self):
        game = Game()
        teacher = FakeTeacher(watching=True, facing=True)
        run_with(game, LEFT, 2 * DT, teacher)
        run_with(game, SCREEN, WARNING_TIME, teacher)
        self.assertEqual(game.warnings, 1)
        self.assertEqual(game.state, PLAYING)

    def test_no_copying_while_seen(self):
        game = Game()
        events = run_with(game, LEFT, CAUGHT_TIME / 2, FakeTeacher(watching=True, facing=True))
        self.assertEqual(game.copy_time, 0)
        self.assertNotIn("tick", events)

    def test_copying_while_busy_is_safe(self):
        game = Game()
        run_with(game, RIGHT, COPY_TIME, FakeTeacher(watching=False))
        self.assertEqual(game.state, PLAYING)
        self.assertEqual(game.answers, 1)

    def test_looking_down_while_watched_is_safe(self):
        game = Game()
        run_with(game, DOWN, 1.0, FakeTeacher(watching=True, facing=True))
        self.assertEqual(game.state, PLAYING)

    def test_staring_while_busy_does_not_fill(self):
        game = Game()
        run_with(game, SCREEN, 1.0, FakeTeacher(facing=True))
        run_with(game, SCREEN, 10.0, FakeTeacher(facing=False))
        self.assertEqual(game.suspicion(), 0)   # drained, never filled
        self.assertEqual(game.warnings, 0)

    def test_staring_while_facing_gives_warning(self):
        game = Game()
        run_with(game, SCREEN, 5.0, FakeTeacher(facing=True))
        self.assertEqual(game.warnings, 1)

    def test_time_runs_out(self):
        game = Game()
        events = run_with(game, DOWN, EXAM_TIME, FakeTeacher())
        self.assertEqual(game.time_left, 0)
        self.assertEqual(game.state, LOST)
        self.assertEqual(game.lose_reason, "time")
        self.assertIn("lost", events)
        self.assertIn("lost_time", events)

    def test_clock_counts_down(self):
        game = Game()
        run_with(game, DOWN, 10.0, FakeTeacher())
        self.assertAlmostEqual(game.time_left, EXAM_TIME - 10.0)

    def test_pause_freezes_clock(self):
        # Paused = main.py does not call update(), so nothing may change.
        game = Game()
        run_with(game, DOWN, 1.0, FakeTeacher())
        before = game.time_left
        self.assertEqual(game.time_left, before)
        run_with(game, DOWN, 1.0, FakeTeacher())
        self.assertAlmostEqual(game.time_left, before - 1.0)

    def test_win_on_last_second_is_a_win(self):
        game = Game()
        game.time_left = COPY_TIME   # exactly the time one answer takes
        game.answers = ANSWERS_NEEDED - 1
        run_with(game, LEFT, COPY_TIME, FakeTeacher())
        self.assertEqual(game.state, WON)


if __name__ == "__main__":
    unittest.main()
