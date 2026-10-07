"""Tests for the disclaimer notice in disclaimer.py (no window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.disclaimer import Disclaimer
from settings import NOTICE_TYPE_DELAY, NOTICE_TYPE_SPEED, NOTICE_SIGN_TIME, NOTICE_STAMP_HOLD

DT = 0.05
LETTERS = 100


def run(notice, seconds):
    """Call update() for `seconds`; return all events."""
    events = []
    for _ in range(round(seconds / DT)):
        events += notice.update(DT)
    return events


TYPING_TIME = NOTICE_TYPE_DELAY + LETTERS / NOTICE_TYPE_SPEED   # until everything is typed


class DisclaimerTests(unittest.TestCase):
    def test_types_out_the_text(self):
        notice = Disclaimer(LETTERS)
        run(notice, NOTICE_TYPE_DELAY)
        self.assertEqual(notice.letters(), 0)      # the paper slides in first
        events = run(notice, LETTERS / NOTICE_TYPE_SPEED / 2)
        self.assertIn("type", events)
        self.assertGreater(notice.letters(), 0)
        self.assertFalse(notice.typed())
        run(notice, LETTERS / NOTICE_TYPE_SPEED)
        self.assertTrue(notice.typed())

    def test_does_not_go_on_without_a_signature(self):
        notice = Disclaimer(LETTERS)
        run(notice, TYPING_TIME + 30)
        self.assertFalse(notice.done())

    def test_space_while_typing_shows_everything(self):
        notice = Disclaimer(LETTERS)
        run(notice, 0.2)
        self.assertEqual(notice.press(), [])       # not signing yet
        self.assertTrue(notice.typed())
        self.assertIsNone(notice.signed_at)

    def test_sign_then_stamp_then_go_on(self):
        notice = Disclaimer(LETTERS)
        run(notice, TYPING_TIME + 0.1)
        self.assertEqual(notice.press(), ["sign"])
        self.assertIsNone(notice.stamp_age())
        events = run(notice, NOTICE_SIGN_TIME + DT)
        self.assertEqual(events.count("stamp"), 1)
        self.assertEqual(notice.sign_progress(), 1.0)
        self.assertFalse(notice.done())
        run(notice, NOTICE_STAMP_HOLD)
        self.assertTrue(notice.done())

    def test_space_after_the_stamp_goes_on_at_once(self):
        notice = Disclaimer(LETTERS)
        run(notice, TYPING_TIME + 0.1)
        notice.press()
        notice.press()                             # while signing: nothing
        self.assertFalse(notice.done())
        run(notice, NOTICE_SIGN_TIME + DT)
        notice.press()
        self.assertTrue(notice.done())


if __name__ == "__main__":
    unittest.main()
