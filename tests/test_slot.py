"""Tests for slot.py: the reel spins, slows down and stops on today's mood."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.slot import reel_position, reel_speed, mood_in_middle, has_stopped, passed
from settings import SLOT_SPIN_TIME, SLOT_TURNS


class SlotTests(unittest.TestCase):
    def test_starts_at_the_first_and_stops_on_the_target(self):
        for target in range(4):
            self.assertEqual(reel_position(target, 4, 0.0), 0)
            end = reel_position(target, 4, SLOT_SPIN_TIME)
            self.assertEqual(mood_in_middle(end, 4), target)
            self.assertTrue(has_stopped(SLOT_SPIN_TIME))

    def test_goes_round_several_times(self):
        self.assertEqual(reel_position(2, 4, SLOT_SPIN_TIME), SLOT_TURNS * 4 + 2)

    def test_slows_down(self):
        step = SLOT_SPIN_TIME / 10
        early = reel_position(0, 4, step) - reel_position(0, 4, 0)
        late = reel_position(0, 4, SLOT_SPIN_TIME) - reel_position(0, 4, SLOT_SPIN_TIME - step)
        self.assertGreater(early, late)

    def test_overshoots_a_little_then_settles(self):
        end = reel_position(2, 4, SLOT_SPIN_TIME)
        near_end = max(reel_position(2, 4, SLOT_SPIN_TIME * i / 100) for i in range(90, 100))
        self.assertGreater(near_end, end)       # went a bit too far...
        self.assertLess(near_end, end + 0.5)    # ...but never as far as the next mood

    def test_fast_at_first_still_at_the_end(self):
        self.assertGreater(reel_speed(0, 4, 0.0), 5)
        self.assertEqual(reel_speed(0, 4, SLOT_SPIN_TIME), 0)

    def test_stays_put_after_stopping(self):
        self.assertEqual(reel_position(1, 4, SLOT_SPIN_TIME), reel_position(1, 4, 100.0))

    def test_one_tick_per_mood_passing(self):
        total = sum(passed(reel_position(3, 4, i * 0.01), reel_position(3, 4, (i + 1) * 0.01))
                    for i in range(round(SLOT_SPIN_TIME / 0.01)))
        self.assertEqual(total, SLOT_TURNS * 4 + 3)


if __name__ == "__main__":
    unittest.main()
