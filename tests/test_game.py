"""Tests for the game rules in game.py (no camera or window needed)."""

import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import (Game, PLAYING, WON, LOST, WARNING_TIME, LETTERS, UNKNOWN,
                  WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE)
from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (EXAM_TIME, ANSWERS_NEEDED, CAUGHT_TIME, PAPER_FOCUS_TIME, SUSPICION_DRAIN_TIME,
                      MAX_WARNINGS, WARNING_SCENE_TIME, CAUGHT_SCENE_TIME, CAUGHT_EXCLAIM_TIME,
                      GAME_OVER_TIME, SCORE_PER_CORRECT, SCORE_TIME_BONUS, SCORE_PER_CLOSE_CALL,
                      SCORE_PER_WARNING)

# 1/8 s per step: adds up exactly in floating point, so 20 steps are exactly 2.5 s.
# Times come from settings.py, so tuning them does not break the tests.
DT = 0.125
# Staring this long is enough for every warning, with the warning scene
# (frozen time) after each one.
ALL_WARNINGS_TIME = MAX_WARNINGS * (WARNING_TIME + WARNING_SCENE_TIME) + 1


def run(game, direction, seconds):
    """Call update() for `seconds` of game time; return all events."""
    events = []
    for _ in range(math.ceil(seconds / DT - 1e-9)):   # at least `seconds`
        events += game.update(direction, DT)
    return events


def known_game(side=LEFT, letter="B"):
    """A game where the given neighbour knows every answer, and it is `letter`."""
    game = Game()
    game.knowing_side = [side] * ANSWERS_NEEDED
    game.right_letters = [letter] * ANSWERS_NEEDED
    return game


def copy_and_write(game, side, letter):
    """Read the current answer from `side`, then look down and write `letter`."""
    events = run(game, side, PAPER_FOCUS_TIME)
    events += run(game, DOWN, DT)
    return events + game.write(letter, DOWN)


class CopyingTests(unittest.TestCase):
    def test_looking_long_enough_reads_the_paper(self):
        game = known_game(LEFT, "C")
        events = run(game, LEFT, PAPER_FOCUS_TIME)
        self.assertEqual(events.count("read"), 1)
        self.assertEqual(game.paper_shows(LEFT), "C")
        self.assertEqual(game.answers, 0)   # read, but not written yet

    def test_other_side_shows_question_mark(self):
        game = known_game(LEFT)
        run(game, RIGHT, PAPER_FOCUS_TIME)
        self.assertEqual(game.paper_shows(RIGHT), UNKNOWN)
        self.assertFalse(game.can_write())

    def test_nothing_shown_before_reading(self):
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME / 2)
        self.assertIsNone(game.paper_shows(LEFT))

    def test_nothing_shown_until_the_bar_is_full(self):
        # One frame before the bar is full the answer must still be hidden.
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME - DT)
        self.assertIsNone(game.paper_shows(LEFT))
        run(game, LEFT, DT)
        self.assertEqual(game.paper_shows(LEFT), "B")

    def test_paper_gets_sharper(self):
        game = Game()
        self.assertEqual(game.paper_clarity(RIGHT), 0.0)
        run(game, RIGHT, PAPER_FOCUS_TIME / 2)
        self.assertAlmostEqual(game.paper_clarity(RIGHT), 0.5)
        self.assertEqual(game.paper_clarity(LEFT), 0.0)
        run(game, RIGHT, PAPER_FOCUS_TIME)
        self.assertEqual(game.paper_clarity(RIGHT), 1.0)   # no sharper than sharp

    def test_looking_away_blurs_it_again(self):
        # Each look starts blurry: the focus is not kept (Emre's rule).
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME - DT)
        run(game, DOWN, DT)
        self.assertEqual(game.paper_clarity(LEFT), 0.0)
        run(game, LEFT, DT)
        self.assertIsNone(game.paper_shows(LEFT))   # not read: it started over

    def test_short_glances_do_not_add_up(self):
        game = known_game(LEFT)
        for _ in range(4):
            run(game, LEFT, PAPER_FOCUS_TIME / 2)
            run(game, SCREEN, DT)
        self.assertNotIn(LEFT, game.read_sides)

    def test_what_the_paper_says_before_reading(self):
        # render.py draws the real paper, only blurred: it is there, not yet readable.
        game = known_game(LEFT, "D")
        self.assertEqual(game.paper_says(LEFT), "D")
        self.assertEqual(game.paper_says(RIGHT), UNKNOWN)
        self.assertIsNone(game.paper_shows(LEFT))

    def test_read_paper_gives_nothing_more(self):
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME)
        events = run(game, LEFT, 1.0)
        self.assertEqual(events, [])
        self.assertEqual(game.paper_clarity(LEFT), 1.0)   # but it stays sharp

    def test_read_paper_gets_sharp_again_when_looking_back(self):
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME)
        run(game, DOWN, DT)
        run(game, LEFT, PAPER_FOCUS_TIME)
        self.assertEqual(game.paper_clarity(LEFT), 1.0)
        self.assertEqual(game.paper_shows(LEFT), "B")

    def test_write_needs_the_answer_read(self):
        game = known_game(LEFT)
        self.assertEqual(game.write("A", DOWN), [])   # nothing read yet
        run(game, RIGHT, PAPER_FOCUS_TIME)                   # only the "?" side
        self.assertEqual(game.write("A", DOWN), [])
        self.assertEqual(game.answers, 0)

    def test_write_only_while_looking_down(self):
        game = known_game(LEFT)
        run(game, LEFT, PAPER_FOCUS_TIME)
        self.assertEqual(game.write("B", LEFT), [])
        self.assertEqual(game.write("B", SCREEN), [])
        self.assertEqual(game.write("B", DOWN), ["write"])
        self.assertEqual(game.written, ["B"])

    def test_writing_starts_the_next_question(self):
        game = known_game(LEFT)
        copy_and_write(game, LEFT, "B")
        self.assertEqual(game.question(), 1)
        self.assertIsNone(game.paper_shows(LEFT))
        self.assertEqual(game.focus_time, {LEFT: 0.0, RIGHT: 0.0})

    def test_wrong_letter_is_written_and_graded(self):
        game = known_game(LEFT, "B")
        copy_and_write(game, LEFT, "D")
        self.assertEqual(game.written, ["D"])
        self.assertEqual(game.correct_count(), 0)

    def test_all_answers_written_wins(self):
        game = known_game(RIGHT, "A")
        events = []
        for letter in "AABCA":
            events += copy_and_write(game, RIGHT, letter)
        self.assertEqual(game.state, WON)
        self.assertIn("won", events)
        self.assertEqual(game.correct_count(), 3)

    def test_answer_key_is_random(self):
        game = Game(random.Random(1))
        self.assertEqual(len(game.right_letters), ANSWERS_NEEDED)
        self.assertTrue(set(game.right_letters) <= set(LETTERS))
        self.assertTrue(set(game.knowing_side) <= {LEFT, RIGHT})


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
        run(game, SCREEN, WARNING_TIME)
        run(game, DOWN, WARNING_SCENE_TIME + DT)
        self.assertIsNone(game.popup_text)

    def test_warning_scene_freezes_the_game(self):
        # While the teacher comes over, nothing moves: the clock, the bars.
        game = Game()
        run(game, SCREEN, WARNING_TIME)
        self.assertTrue(game.in_scene())
        time_left = game.time_left
        self.assertEqual(run(game, LEFT, WARNING_SCENE_TIME - DT), [])
        self.assertEqual(game.time_left, time_left)
        self.assertEqual(game.focus_time[LEFT], 0)
        self.assertEqual(game.suspicion(), 0)
        run(game, LEFT, DT)
        self.assertFalse(game.in_scene())
        run(game, LEFT, DT)
        self.assertGreater(game.focus_time[LEFT], 0)   # moving again

    def test_last_warning_scene_plays_before_game_over(self):
        game = Game()
        for _ in range(MAX_WARNINGS - 1):
            run(game, SCREEN, WARNING_TIME + WARNING_SCENE_TIME)
        run(game, SCREEN, WARNING_TIME)
        self.assertEqual(game.state, LOST)
        self.assertEqual(game.scene, WARNING_SCENE)   # main.py waits for it before the end screen
        events = run(game, SCREEN, WARNING_SCENE_TIME)
        self.assertEqual(game.scene, GAME_OVER_SCENE)  # then the game over scene
        self.assertIn("nooo", events)

    def test_three_warnings_lose(self):
        game = Game()
        events = run(game, SCREEN, ALL_WARNINGS_TIME)
        self.assertEqual(game.state, LOST)
        self.assertIn("lost", events)

    def test_looking_down_drains_slowly(self):
        # Not reset at once: the bar jumping to empty would give away the teacher.
        game = Game()
        run(game, SCREEN, WARNING_TIME / 2)   # half full, no warning yet
        run(game, DOWN, 1.0)
        self.assertAlmostEqual(game.suspicion(), 0.5 - 1.0 / SUSPICION_DRAIN_TIME)
        run(game, DOWN, SUSPICION_DRAIN_TIME)
        self.assertEqual(game.suspicion(), 0)


class GameOverTests(unittest.TestCase):
    def test_nothing_happens_after_game_over(self):
        game = Game()
        run(game, SCREEN, ALL_WARNINGS_TIME)
        self.assertEqual(run(game, LEFT, 5.0), [])
        self.assertEqual(game.answers, 0)

    def test_reset(self):
        game = Game()
        run(game, SCREEN, ALL_WARNINGS_TIME)
        game.reset()
        self.assertEqual(game.state, PLAYING)
        self.assertEqual((game.answers, game.warnings), (0, 0))
        self.assertEqual(game.time_left, EXAM_TIME)
        self.assertIsNone(game.lose_reason)

    def test_exam_time_from_the_settings_menu(self):
        # The settings menu changes exam_time; the next reset() uses it.
        game = Game(exam_time=EXAM_TIME + 30)
        self.assertEqual(game.time_left, EXAM_TIME + 30)
        game.exam_time = EXAM_TIME + 60
        game.reset()
        self.assertEqual(game.time_left, EXAM_TIME + 60)

    def test_three_warnings_reason(self):
        game = Game()
        events = run(game, SCREEN, ALL_WARNINGS_TIME)
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

    def test_caught_scene_then_game_over(self):
        # Caught: the "!" and the torn exam, a rip sound, then game over.
        game = Game()
        teacher = FakeTeacher(watching=True, facing=True)
        run_with(game, LEFT, CAUGHT_TIME, teacher)
        self.assertEqual(game.scene, CAUGHT_SCENE)
        self.assertNotIn("rip", run_with(game, LEFT, CAUGHT_EXCLAIM_TIME - DT, teacher))
        events = run_with(game, LEFT, CAUGHT_SCENE_TIME - CAUGHT_EXCLAIM_TIME + DT, teacher)
        self.assertEqual(events.count("rip"), 1)
        self.assertEqual(game.scene, GAME_OVER_SCENE)
        self.assertIn("nooo", events)
        run_with(game, LEFT, GAME_OVER_TIME, teacher)
        self.assertFalse(game.in_scene())   # now main.py shows the end menu

    def test_time_up_goes_straight_to_game_over(self):
        game = Game()
        events = run(game, DOWN, EXAM_TIME)
        self.assertEqual(game.lose_reason, "time")
        self.assertEqual(game.scene, GAME_OVER_SCENE)
        self.assertIn("nooo", events)

    def test_skip_only_after_losing(self):
        game = Game()
        run(game, SCREEN, WARNING_TIME)        # a warning scene, game still on
        game.skip_scene()
        self.assertEqual(game.scene, WARNING_SCENE)
        self.assertGreater(game.scene_time, DT)  # not skipped
        game = Game()
        run(game, DOWN, EXAM_TIME)             # lost: game over scene
        game.skip_scene()
        run(game, DOWN, DT)
        self.assertFalse(game.in_scene())

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
        self.assertEqual(game.focus_time[LEFT], 0)
        self.assertNotIn("read", events)

    def test_copying_while_busy_is_safe(self):
        game = known_game(RIGHT)
        run_with(game, RIGHT, PAPER_FOCUS_TIME, FakeTeacher(watching=False))
        self.assertEqual(game.state, PLAYING)
        self.assertEqual(game.paper_shows(RIGHT), "B")

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
        game = known_game(LEFT)
        game.written = ["B"] * (ANSWERS_NEEDED - 1)
        run_with(game, LEFT, PAPER_FOCUS_TIME, FakeTeacher())
        game.time_left = DT          # the last frame of the exam
        game.write("B", DOWN)
        run_with(game, DOWN, DT, FakeTeacher())
        self.assertEqual(game.state, WON)


class ScoreTests(unittest.TestCase):
    def won_game(self, letters="BBBBB"):
        game = known_game(LEFT, "B")
        for letter in letters:
            copy_and_write(game, LEFT, letter)
        return game

    def test_score_parts(self):
        game = self.won_game("BBBBA")   # 4 right
        time_share = game.time_left / game.exam_time
        parts = dict(game.score_parts())
        self.assertEqual(parts["CORRECT"], 4 * SCORE_PER_CORRECT)
        self.assertEqual(parts["TIME"], int(SCORE_TIME_BONUS * time_share))
        self.assertEqual(game.score(), sum(parts.values()))

    def test_lost_scores_nothing(self):
        game = Game()
        run(game, DOWN, EXAM_TIME)
        self.assertEqual(game.score(), 0)
        self.assertEqual(game.score_parts(), [])

    def test_warnings_cost_points_but_never_below_zero(self):
        game = self.won_game("AAAAA")   # all wrong
        game.warnings = 2
        self.assertEqual(dict(game.score_parts())["WARNINGS"], -2 * SCORE_PER_WARNING)
        self.assertGreaterEqual(game.score(), 0)

    def test_getting_away_is_a_close_call(self):
        game = Game()
        teacher = FakeTeacher(watching=True)
        run_with(game, LEFT, CAUGHT_TIME / 2, teacher)     # seen, but not caught yet
        events = run_with(game, DOWN, DT, teacher)         # looked away in time
        self.assertIn("close_call", events)
        self.assertEqual(game.close_calls, 1)
        self.assertIn(str(SCORE_PER_CLOSE_CALL), game.popup_text)


if __name__ == "__main__":
    unittest.main()
