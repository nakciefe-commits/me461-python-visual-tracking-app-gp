"""Tests for the "How to play" guide in guide.py (no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.guide import Guide, GUIDE_STEPS, GEMINI, CLAUDE, LETTERS
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (PAPER_FOCUS_TIME, GUIDE_TYPE_SPEED, GUIDE_LINE_PAUSE, GUIDE_STEP_PAUSE,
                      GUIDE_HOLD_TIME)

DT = 0.01
# A small made-up guide, so the tests do not depend on the real lines.
STEPS = [
    {"lines": [(GEMINI, "Hello there."), (CLAUDE, "Look down.")], "task": ("look", DOWN)},
    {"lines": [(CLAUDE, "Write B.")], "task": ("write", "B")},
    {"lines": [(GEMINI, "Read the left one.")], "task": ("read", LEFT), "sound": "state:TURNING"},
    {"lines": [(CLAUDE, "Bye!")]},
]


def run(guide, seconds, direction=SCREEN):
    """Move the guide on for `seconds`. Returns all the events, in order."""
    events = []
    for _ in range(round(seconds / DT)):
        events += guide.update(DT, direction)
    return events


def line_time(text):
    """Seconds to type a line and read it."""
    return len(text) / GUIDE_TYPE_SPEED + GUIDE_LINE_PAUSE


class TestGuide(unittest.TestCase):
    def test_lines_are_typed_then_the_next_one_starts(self):
        guide = Guide(STEPS)
        self.assertEqual(guide.letters(), 0)
        run(guide, 0.1)
        self.assertGreater(guide.letters(), 0)
        run(guide, line_time("Hello there."))
        self.assertEqual(guide.current_line(), (CLAUDE, "Look down."))
        self.assertEqual(len(guide.said), 2)

    def test_typing_makes_talking_blips_in_the_speakers_voice(self):
        guide = Guide(STEPS)
        events = run(guide, 0.3)
        self.assertIn("talk:GEMINI", events)
        self.assertNotIn("talk:CLAUDE", events)

    def test_a_look_task_waits_for_the_head(self):
        guide = Guide(STEPS)
        run(guide, 10, SCREEN)   # looking the wrong way: stuck on the task
        self.assertTrue(guide.waiting())
        self.assertEqual(guide.step, 0)
        events = run(guide, GUIDE_HOLD_TIME + 0.05, DOWN)
        self.assertIn("read", events)   # the "ding"
        run(guide, GUIDE_STEP_PAUSE + 0.05, DOWN)
        self.assertEqual(guide.step, 1)

    def test_a_short_look_does_not_count(self):
        guide = Guide(STEPS)
        run(guide, 10)
        run(guide, GUIDE_HOLD_TIME / 2, DOWN)
        run(guide, 0.1, SCREEN)   # looked away: starts again
        run(guide, GUIDE_HOLD_TIME / 2, DOWN)
        self.assertTrue(guide.waiting())

    def test_the_task_only_counts_after_the_lines(self):
        guide = Guide(STEPS)
        run(guide, 0.5, DOWN)   # looking down while the first line is typed
        self.assertEqual(guide.step, 0)
        self.assertFalse(guide.task_done)

    def test_writing_needs_the_paper_and_the_right_letter(self):
        guide = Guide(STEPS)
        guide.skip(), guide.skip(), guide.skip(), guide.skip()   # through step 1
        run(guide, 10)
        self.assertTrue(guide.waiting())
        self.assertEqual(guide.press("B", SCREEN), ["menu_back"])   # not looking down
        self.assertEqual(guide.press("A", DOWN), ["menu_back"])     # wrong letter
        self.assertEqual(guide.written, [])
        self.assertEqual(guide.press("B", DOWN), ["read"])
        self.assertEqual(guide.written, ["B"])

    def test_any_letter_and_blank(self):
        guide = Guide([{"lines": [(GEMINI, "Write.")], "task": ("write", None)},
                       {"lines": [(GEMINI, "Again.")], "task": ("write", None)}])
        run(guide, 5)
        guide.press("S", DOWN)
        run(guide, GUIDE_STEP_PAUSE + 5)
        guide.press("D", DOWN)
        self.assertEqual(guide.written, ["-", "D"])

    def test_reading_takes_the_papers_focus_time(self):
        guide = Guide(STEPS[2:])
        run(guide, 5)
        run(guide, PAPER_FOCUS_TIME - 0.2, LEFT)
        self.assertTrue(guide.waiting())
        self.assertLess(guide.clarity(LEFT), 1)
        self.assertEqual(guide.clarity(RIGHT), 0)
        run(guide, 0.3, LEFT)
        self.assertTrue(guide.task_done)

    def test_a_steps_sound_plays_when_it_starts(self):
        guide = Guide(STEPS[1:])
        run(guide, 5)
        guide.press("B", DOWN)
        events = run(guide, GUIDE_STEP_PAUSE + 0.05, DOWN)
        self.assertIn("state:TURNING", events)

    def test_skip_finishes_typing_then_does_the_task(self):
        guide = Guide(STEPS)
        guide.skip()
        self.assertTrue(guide.typed())
        guide.skip()                      # next line
        guide.skip()                      # typed
        self.assertTrue(guide.waiting())
        guide.skip()                      # the task is done for the player
        self.assertEqual(guide.step, 1)

    def test_it_finishes(self):
        guide = Guide(STEPS)
        for _ in range(50):
            guide.skip()
        self.assertTrue(guide.finished())
        self.assertEqual(run(guide, 1), [])
        self.assertEqual(guide.skip(), [])
        # Asking about the step after the end must not crash (main.py did once).
        self.assertIsNone(guide.task())
        self.assertFalse(guide.waiting())
        self.assertEqual(guide.teacher(), "busy")
        self.assertEqual(guide.press("A", DOWN), [])

    def test_the_real_guide_can_be_played_through(self):
        guide = Guide()
        for _ in range(500):
            if guide.finished():
                break
            kind, what = guide.task() or (None, None)
            if guide.waiting() and kind == "write":
                guide.press(what or "A", DOWN)
            run(guide, 0.5, what if kind in ("look", "read") else SCREEN)
        self.assertTrue(guide.finished())
        self.assertEqual(guide.written, ["A", "B"])

    def test_real_lines_fit_in_the_bubble(self):
        for step in GUIDE_STEPS:
            for who, text in step["lines"]:
                self.assertIn(who, (GEMINI, CLAUDE))
                self.assertLessEqual(len(text), 75, text)
            task = step.get("task")
            if task and task[0] == "write" and task[1] is not None:
                self.assertIn(task[1], LETTERS)


if __name__ == "__main__":
    unittest.main()
