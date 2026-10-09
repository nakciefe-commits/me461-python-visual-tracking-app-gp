"""Tests for the grade roast after the final (logic/verdict.py; no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.verdict import Verdict, VERDICTS, GEMINI, CLAUDE, HYPE_SOUNDS
from logic.grade import LETTERS
from settings import (VERDICT_TYPE_SPEED, VERDICT_LINE_PAUSE, VERDICT_HOLD, VERDICT_HYPE, VERDICT_REVEAL,
                      VERDICT_FIREWORK_EVERY)

DT = 0.01
LINES = [(GEMINI, "Hello."), (CLAUDE, "Bye now.")]


def run(verdict, seconds):
    """Move the roast on for `seconds`. Returns all the events, in order."""
    events = []
    for _ in range(round(seconds / DT)):
        events += verdict.update(DT)
    return events


class VerdictTextTests(unittest.TestCase):
    def test_every_letter_has_a_roast(self):
        for letter in LETTERS:
            self.assertIn(letter, VERDICTS)
            self.assertGreaterEqual(len(VERDICTS[letter]), 2, letter)

    def test_lines_fit(self):
        for letter, chats in VERDICTS.items():
            for chat in chats:
                self.assertLessEqual(len(chat), 3)
                for who, text in chat:
                    self.assertIn(who, (GEMINI, CLAUDE))
                    self.assertLessEqual(len(text), 75, text)

    def test_hype_only_for_good_grades(self):
        # Nothing below BB, and the better the grade, the bigger the show.
        self.assertEqual(set(VERDICT_HYPE), {"AA", "BA", "BB"})
        self.assertGreater(VERDICT_HYPE["AA"], VERDICT_HYPE["BA"])
        self.assertGreater(VERDICT_HYPE["BA"], VERDICT_HYPE["BB"])


class VerdictTests(unittest.TestCase):
    def test_lines_are_typed_one_after_the_other(self):
        verdict = Verdict("CC", LINES)
        run(verdict, 0.05)
        first, second = verdict.letters()
        self.assertGreater(first, 0)
        self.assertEqual(second, 0)
        run(verdict, len("Hello.") / VERDICT_TYPE_SPEED + VERDICT_LINE_PAUSE)
        self.assertEqual(verdict.letters()[0], len("Hello."))
        self.assertGreater(verdict.letters()[1], 0)

    def test_it_finishes_after_the_hold(self):
        verdict = Verdict("CC", LINES)
        run(verdict, verdict.typed_at + 0.05)
        self.assertTrue(verdict.all_typed())
        self.assertFalse(verdict.finished())
        run(verdict, VERDICT_HOLD)
        self.assertTrue(verdict.finished())

    def test_skip_types_all_then_closes(self):
        verdict = Verdict("CC", LINES)
        run(verdict, 0.1)
        verdict.skip()
        self.assertTrue(verdict.all_typed())
        self.assertEqual(verdict.letters(), [len(text) for _, text in LINES])
        self.assertFalse(verdict.finished())
        verdict.skip()
        self.assertTrue(verdict.finished())

    def test_talking_blips_in_each_voice(self):
        events = run(Verdict("CC", LINES), 5)
        self.assertIn("talk:GEMINI", events)
        self.assertIn("talk:CLAUDE", events)

    def test_they_laugh_at_a_bad_grade_and_smile_at_a_good_one(self):
        for letter, laughs in (("FF", True), ("CC", True), ("AA", False)):
            verdict = Verdict(letter, LINES)
            self.assertFalse(verdict.laughing())   # not before it is all said
            verdict.skip()
            self.assertEqual(verdict.laughing(), laughs, letter)


class HypeTests(unittest.TestCase):
    def test_no_show_below_bb(self):
        verdict = Verdict("CB", LINES)
        self.assertEqual(verdict.hype, 0)
        self.assertEqual(verdict.reveal, 0)
        events = run(verdict, 1)
        self.assertFalse(set(events) & {"boom", "firework", "new_top", "tally_done"})

    def test_the_show_comes_first(self):
        for letter in VERDICT_HYPE:
            verdict = Verdict(letter, LINES)
            self.assertEqual(verdict.reveal, VERDICT_REVEAL[VERDICT_HYPE[letter]])
            events = run(verdict, verdict.reveal - 0.05)
            self.assertEqual(verdict.letters(), [0, 0], letter)   # nobody talks during the show
            self.assertEqual(events[:len(HYPE_SOUNDS[verdict.hype])], HYPE_SOUNDS[verdict.hype])

    def test_aa_has_fireworks_during_the_show(self):
        verdict = Verdict("AA", LINES)
        events = run(verdict, verdict.reveal)
        expected = sum(1 for t in verdict.firework_times() if t < verdict.reveal)
        self.assertGreaterEqual(expected, verdict.reveal / VERDICT_FIREWORK_EVERY - 1)
        self.assertEqual(events.count("firework"), expected)
        # After the show they go on quietly (no sound over the talking).
        self.assertNotIn("firework", run(verdict, 5))
        self.assertGreater(len(verdict.firework_times()), expected)
        self.assertEqual(Verdict("BA", LINES).firework_times(), [])


if __name__ == "__main__":
    unittest.main()
