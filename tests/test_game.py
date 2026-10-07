"""Tests for the game rules in game.py (no camera or window needed)."""

import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from game import Game, PLAYING, WON, LOST, WARNING_TIME
from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (EXAM_TIME, ANSWERS_NEEDED, ANSWER_CHOICES, CAUGHT_TIME,
                      SUSPICION_DRAIN_TIME, PAPER_FOCUS_TIME)

# 1/8 s per step: adds up exactly in floating point, so 20 steps are exactly 2.5 s.
# Times come from settings.py, so tuning them does not break the tests.
DT = 0.125


def run(game, direction, seconds):
    """Call update() for `seconds` of game time; return all events."""
    events = []
    for _ in range(math.ceil(seconds / DT - 1e-9)):   # at least `seconds`
        events += game.update(direction, DT)
    return events


class ExamPaperTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(random.Random(1))

    def test_own_paper_starts_blank_and_neighbours_are_marked(self):
        self.assertEqual(self.game.player_answers, [None] * ANSWERS_NEEDED)
        for direction in (LEFT, RIGHT):
            marks = self.game.neighbour_answers[direction]
            self.assertEqual(len(marks), ANSWERS_NEEDED)
            self.assertTrue(all(choice in ANSWER_CHOICES for choice in marks))
            self.assertEqual(marks, self.game.answer_key)

    def test_neighbour_marks_stay_fixed_when_looking_around(self):
        before = self.game.neighbour_answers.copy()
        for direction in (LEFT, DOWN, RIGHT, SCREEN):
            run(self.game, direction, DT)
        self.assertEqual(self.game.neighbour_answers, before)

    def test_looking_sideways_does_not_write_or_win(self):
        for direction in (LEFT, RIGHT):
            self.assertNotIn("answer", run(self.game, direction, EXAM_TIME / 4))
        self.assertEqual(self.game.answers, 0)
        self.assertEqual(self.game.state, PLAYING)

    def test_keyboard_writes_then_advances_to_next_blank_question(self):
        self.assertEqual(self.game.answer("a", SCREEN), ["answer"])
        self.assertEqual(self.game.player_answers[0], "a")
        self.assertEqual(self.game.active_question, 1)
        self.assertEqual(self.game.answers, 1)

    def test_all_five_keys_and_uppercase_are_accepted(self):
        for choice in ANSWER_CHOICES:
            with self.subTest(choice=choice):
                game = Game(random.Random(1))
                game.answer(choice.upper(), DOWN)
                self.assertEqual(game.player_answers[0], choice)

    def test_cannot_answer_sideways_or_while_paused(self):
        for direction in (LEFT, RIGHT, None):
            self.assertEqual(self.game.answer("c", direction), [])
        self.assertEqual(self.game.answers, 0)

    def test_invalid_choices_are_ignored(self):
        for choice in ("x", "", "ab", None, 0):
            self.assertEqual(self.game.answer(choice, SCREEN), [])
        self.assertEqual(self.game.answers, 0)

    def test_revising_an_answer_does_not_double_count_it(self):
        self.game.answer("a", SCREEN)
        self.game.select_question(0, DOWN)
        self.game.answer("b", DOWN)
        self.assertEqual(self.game.player_answers[0], "b")
        self.assertEqual(self.game.answers, 1)
        self.assertEqual(self.game.active_question, 1)

    def test_navigation_wraps_and_rejects_invalid_indices(self):
        self.game.move_question(-1, SCREEN)
        self.assertEqual(self.game.active_question, ANSWERS_NEEDED - 1)
        self.game.move_question(1, DOWN)
        self.assertEqual(self.game.active_question, 0)
        for index in (-1, ANSWERS_NEEDED):
            self.assertFalse(self.game.select_question(index, SCREEN))
        self.assertEqual(self.game.active_question, 0)

    def test_navigation_is_frozen_sideways_and_paused(self):
        for direction in (LEFT, RIGHT, None):
            self.assertFalse(self.game.move_question(1, direction))
        self.assertEqual(self.game.active_question, 0)

    def test_correct_manual_answers_win(self):
        events = []
        for choice in self.game.neighbour_answers[LEFT]:
            events += self.game.answer(choice, DOWN)
        self.assertEqual(self.game.state, WON)
        self.assertEqual(self.game.correct_answers, ANSWERS_NEEDED)
        self.assertEqual(events.count("answer"), ANSWERS_NEEDED)
        self.assertEqual(events.count("won"), 1)

    def test_wrong_answer_can_be_revisited_after_paper_is_full(self):
        expected = self.game.answer_key[0]
        wrong = next(choice for choice in ANSWER_CHOICES if choice != expected)
        self.game.answer(wrong, SCREEN)
        for choice in self.game.answer_key[1:]:
            self.game.answer(choice, SCREEN)
        self.assertEqual(self.game.answers, ANSWERS_NEEDED)
        self.assertEqual(self.game.state, PLAYING)
        self.assertIsNotNone(self.game.popup_text)
        self.game.select_question(0, SCREEN)
        self.assertIn("won", self.game.answer(expected, SCREEN))

    def test_reset_clears_marks_selection_and_score(self):
        self.game.answer("a", SCREEN)
        self.game.reset()
        self.assertEqual(self.game.player_answers, [None] * ANSWERS_NEEDED)
        self.assertEqual(self.game.active_question, 0)
        self.assertEqual((self.game.answers, self.game.correct_answers), (0, 0))
        self.assertEqual(self.game.state, PLAYING)

    def test_seeded_exams_can_be_repeated_but_reset_generates_a_new_exam(self):
        other = Game(random.Random(1))
        self.assertEqual(self.game.answer_key, other.answer_key)
        # Check RNG state as well, so repeated letters cannot make this flaky.
        state = self.game.rng.getstate()
        self.game.reset()
        other.reset()
        self.assertNotEqual(self.game.rng.getstate(), state)
        self.assertEqual(self.game.answer_key, other.answer_key)

    def test_answers_after_win_or_loss_are_ignored(self):
        for state in (WON, LOST):
            with self.subTest(state=state):
                game = Game()
                game.state = state
                self.assertEqual(game.answer("e", DOWN), [])
                self.assertFalse(game.move_question(1, DOWN))
                self.assertEqual(game.answers, 0)


class PaperFocusTests(unittest.TestCase):
    def test_a_new_exam_starts_blurry(self):
        game = Game()
        self.assertEqual(game.paper_clarity, 0)
        self.assertIsNone(game.paper_direction)

    def test_continuous_look_slowly_clears_the_paper(self):
        game = Game()
        for expected in (0.25, 0.5, 0.75, 1.0):
            game.update(LEFT, PAPER_FOCUS_TIME / 4)
            self.assertAlmostEqual(game.paper_clarity, expected)
        self.assertEqual(game.answers, 0)  # focusing only reads, never writes

    def test_focus_is_capped_after_the_paper_is_clear(self):
        game = Game()
        game.update(RIGHT, PAPER_FOCUS_TIME * 2)
        self.assertEqual(game.paper_clarity, 1)
        self.assertEqual(game.paper_focus_time, PAPER_FOCUS_TIME)

    def test_looking_away_restarts_blur(self):
        for direction in (SCREEN, DOWN):
            with self.subTest(direction=direction):
                game = Game()
                game.update(LEFT, PAPER_FOCUS_TIME)
                game.update(direction, DT)
                self.assertEqual(game.paper_clarity, 0)
                game.update(LEFT, PAPER_FOCUS_TIME / 4)
                self.assertAlmostEqual(game.paper_clarity, 0.25)

    def test_switching_neighbours_starts_blurry_again(self):
        game = Game()
        game.update(LEFT, PAPER_FOCUS_TIME)
        game.update(RIGHT, PAPER_FOCUS_TIME / 4)
        self.assertAlmostEqual(game.paper_clarity, 0.25)
        self.assertEqual(game.paper_direction, RIGHT)

    def test_answering_starts_the_next_question_blurry(self):
        game = Game()
        game.update(LEFT, PAPER_FOCUS_TIME)
        game.answer(game.answer_key[0], DOWN)
        self.assertEqual(game.active_question, 1)
        self.assertEqual(game.paper_clarity, 0)

    def test_revisiting_a_question_resets_focus(self):
        game = Game()
        game.update(LEFT, PAPER_FOCUS_TIME)
        game.select_question(1, DOWN)
        self.assertEqual(game.paper_clarity, 0)
        self.assertEqual(game.active_question, 1)

    def test_tracking_pause_and_restart_clear_focus(self):
        game = Game()
        game.update(LEFT, PAPER_FOCUS_TIME)
        game.reset_paper_focus()
        self.assertEqual(game.paper_clarity, 0)
        game.update(RIGHT, PAPER_FOCUS_TIME)
        game.reset()
        self.assertEqual(game.paper_clarity, 0)


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
        run(game, SCREEN, WARNING_TIME / 2)   # half full, no warning yet
        run(game, DOWN, 1.0)
        self.assertAlmostEqual(game.suspicion(), 0.5 - 1.0 / SUSPICION_DRAIN_TIME)
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

    def test_being_seen_does_not_write_answers(self):
        game = Game()
        events = run_with(game, LEFT, CAUGHT_TIME / 2, FakeTeacher(watching=True, facing=True))
        self.assertEqual(game.answers, 0)
        self.assertNotIn("answer", events)

    def test_copying_while_busy_is_safe(self):
        game = Game()
        run_with(game, RIGHT, DT, FakeTeacher(watching=False))
        self.assertEqual(game.state, PLAYING)
        self.assertEqual(game.answers, 0)

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
        for choice in game.answer_key[:-1]:
            game.answer(choice, DOWN)
        game.time_left = DT
        game.answer(game.answer_key[-1], DOWN)
        run_with(game, DOWN, DT, FakeTeacher())
        self.assertEqual(game.state, WON)


if __name__ == "__main__":
    unittest.main()
