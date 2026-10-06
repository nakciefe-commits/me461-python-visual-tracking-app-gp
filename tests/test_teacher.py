"""Tests for the teacher in teacher.py (no window needed)."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from teacher import Teacher, BUSY, TURNING, WATCHING, BOARD, DESK
from settings import TEACHER_DURATIONS, CAUGHT_GRACE

DT = 0.05


def ten_minutes(teacher):
    """
    Run the teacher for 10 minutes of game time. Returns a list of
    (state, place, how long it lasted) for every state that finished.
    """
    finished = []
    for _ in range(round(600 / DT)):
        state, place, time_in_state = teacher.state, teacher.place, teacher.time_in_state
        if teacher.update(DT):
            finished.append((state, place, time_in_state + DT))
    return finished


class TeacherTests(unittest.TestCase):
    def setUp(self):
        self.teacher = Teacher(random.Random(1))

    def test_starts_busy_at_the_board(self):
        self.assertEqual((self.teacher.state, self.teacher.place), (BUSY, BOARD))

    def test_every_state_and_place_appears(self):
        finished = ten_minutes(self.teacher)
        self.assertEqual({state for state, _, _ in finished}, {BUSY, TURNING, WATCHING})
        self.assertEqual({place for _, place, _ in finished}, {BOARD, DESK})

    def test_order_is_busy_turning_watching(self):
        states = [state for state, _, _ in ten_minutes(self.teacher)]
        following = {BUSY: TURNING, TURNING: WATCHING, WATCHING: BUSY}
        for state, next_state in zip(states, states[1:]):
            self.assertEqual(next_state, following[state])

    def test_durations_stay_in_range(self):
        for state, _, lasted in ten_minutes(self.teacher):
            shortest, longest = TEACHER_DURATIONS[state]
            # Plus one step: the switch happens on the first frame past the time.
            self.assertGreaterEqual(lasted, shortest)
            self.assertLessEqual(lasted, longest + DT)

    def test_place_only_changes_after_watching(self):
        finished = ten_minutes(self.teacher)
        for (state, place, _), (_, next_place, _) in zip(finished, finished[1:]):
            if state != WATCHING:
                self.assertEqual(place, next_place)

    def test_update_returns_the_new_state(self):
        events = []
        while not events:
            events = self.teacher.update(DT)
        self.assertEqual(events, ["state:" + TURNING])

    def test_not_watching_while_turning(self):
        self.teacher.start(TURNING)
        self.assertFalse(self.teacher.is_watching())

    def test_watching_only_after_grace(self):
        self.teacher.start(WATCHING)
        self.teacher.time_in_state = CAUGHT_GRACE - 0.01
        self.assertFalse(self.teacher.is_watching())
        self.teacher.time_in_state = CAUGHT_GRACE
        self.assertTrue(self.teacher.is_watching())

    def test_image_names(self):
        self.assertEqual(self.teacher.image_name(), "classroom_board_busy")
        self.teacher.start(TURNING)   # not looking up yet
        self.assertEqual(self.teacher.image_name(), "classroom_board_busy")
        self.teacher.place = DESK
        self.teacher.start(WATCHING)
        self.assertEqual(self.teacher.image_name(), "classroom_desk_watching")

    def test_silent_while_looking_down(self):
        self.assertEqual(self.teacher.sounds(["state:" + BUSY], can_hear=False), [])
        self.teacher.start(TURNING)
        self.assertEqual(self.teacher.sounds(["state:" + TURNING], can_hear=False), [])

    def test_hears_turning_when_looking_up(self):
        self.teacher.start(TURNING)
        self.assertEqual(self.teacher.sounds(["state:" + TURNING], can_hear=True),
                         ["state:" + TURNING])

    def test_hears_turning_late_but_only_once(self):
        self.teacher.start(TURNING)
        self.assertEqual(self.teacher.sounds(["state:" + TURNING], can_hear=False), [])
        self.assertEqual(self.teacher.sounds([], can_hear=True), ["state:" + TURNING])
        self.assertEqual(self.teacher.sounds([], can_hear=True), [])

    def test_no_turning_sound_after_turning_ends(self):
        self.teacher.start(TURNING)
        self.teacher.sounds([], can_hear=False)   # missed it
        self.teacher.start(WATCHING)
        self.assertEqual(self.teacher.sounds([], can_hear=True), [])

    def test_images_exist(self):
        root = os.path.join(os.path.dirname(__file__), "..", "assets", "images")
        for place in ("board", "desk"):
            for looking in ("busy", "watching"):
                path = os.path.join(root, f"classroom_{place}_{looking}.jpeg")
                self.assertTrue(os.path.exists(path), path)
        # The pictures for looking down, left and right (no teacher in them).
        for looking in ("down", "left", "right"):
            path = os.path.join(root, f"classroom_desk_looking_{looking}.jpeg")
            self.assertTrue(os.path.exists(path), path)
        # Each neighbour's paper with the letter (or "?") they wrote.
        for side in ("left", "right"):
            for shown in ("A", "B", "C", "D", "unknown"):
                path = os.path.join(root, f"{side}_{shown}.jpeg")
                self.assertTrue(os.path.exists(path), path)


if __name__ == "__main__":
    unittest.main()
