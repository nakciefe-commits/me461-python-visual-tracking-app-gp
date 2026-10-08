"""
Tests that every mood in settings.py does what its + and - lines say.

The gossip screen promises things like "Long busy times" or "He never
leaves the desk"; the teacher only follows the numbers ("busy",
"watching", "move", "place"). These tests read each line, find what it
promises (KEYWORDS below) and check the numbers against "normal_day", the
plain teacher. Change a number, and a line that is no longer true fails.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from settings import MOODS

PLAIN = MOODS["normal_day"]
LONGER = 1.1    # "long" = at least 10 % longer on average than the plain teacher
SHORTER = 0.9   # "short" / "quick" = at least 10 % shorter


def average(pair):
    return sum(pair) / 2


def busy_ratio(mood):
    return average(mood["busy"]) / average(PLAIN["busy"])


def watching_ratio(mood):
    return average(mood["watching"]) / average(PLAIN["watching"])


# (words in a line, what must be true of the mood). Lower case.
KEYWORDS = [
    (("long busy", "very long busy", "long calls", "long quiet"), lambda m: busy_ratio(m) >= LONGER),
    (("short busy", "barely works"), lambda m: busy_ratio(m) <= SHORTER),
    (("quick", "short, ", "short looks"), lambda m: watching_ratio(m) <= SHORTER),
    (("long looks", "long, angry", "long stares", "very long stares", "for a while"),
     lambda m: watching_ratio(m) >= LONGER),
    (("never leaves the desk", "stays at his desk", "at the desk"),
     lambda m: m.get("place") == "DESK" and m["move"] <= 0.1),
    (("never leaves the board",), lambda m: m.get("place", "BOARD") == "BOARD" and m["move"] == 0),
    (("stays where he is", "too hungry to walk", "too tired to walk"), lambda m: m["move"] <= 0.15),
    (("keeps moving", "moves a lot"), lambda m: m["move"] >= 0.5),
]


class MoodPromiseTests(unittest.TestCase):
    def test_every_line_is_true(self):
        for name, mood in MOODS.items():
            for line in mood["good"] + mood["bad"]:
                text = line.lower()
                for words, holds in KEYWORDS:
                    if any(word in text for word in words):
                        self.assertTrue(holds(mood), f"{name}: \"{line}\" is not true of its numbers")

    def test_every_line_is_checked(self):
        # A new line with a promise the tests do not know yet: add its words above.
        for name, mood in MOODS.items():
            for line in mood["good"] + mood["bad"]:
                text = line.lower()
                self.assertTrue(any(word in text for words, _ in KEYWORDS for word in words),
                                f"{name}: nothing checks \"{line}\"")

    def test_good_days_are_good_and_bad_days_bad(self):
        # A mood with only + lines must not be harder than the plain teacher, and
        # one with only - lines not easier (busy shorter or looks longer).
        for name, mood in MOODS.items():
            if mood["good"] and not mood["bad"]:
                self.assertGreaterEqual(busy_ratio(mood), 1.0, name)
                self.assertLessEqual(watching_ratio(mood), 1.0, name)
            if mood["bad"] and not mood["good"]:
                self.assertTrue(busy_ratio(mood) < 1.0 or watching_ratio(mood) > 1.0, name)


if __name__ == "__main__":
    unittest.main()
