"""Tests for the teacher in teacher.py (no window needed)."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.teacher import Teacher, BUSY, TURNING, WATCHING, BOARD, DESK
from settings import TEACHER_DURATIONS, CAUGHT_GRACE, MOODS

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


class SoundEventTests(unittest.TestCase):
    def test_footsteps_only_when_he_moves(self):
        teacher = Teacher(random.Random(1))
        for _ in range(round(300 / DT)):
            place = teacher.place
            events = teacher.update(DT)
            self.assertEqual("footsteps" in events, teacher.place != place)

    def test_erasing_only_busy_at_the_board(self):
        teacher = Teacher(random.Random(2))
        for _ in range(round(120 / DT)):
            teacher.update(DT)
            self.assertEqual(teacher.erasing(), teacher.state == BUSY and teacher.place == BOARD)


class MoodTextTests(unittest.TestCase):
    def test_mood_texts_fit_the_gossip_box(self):
        # The gossip screen has room for 3 story lines and 3 +/- lines.
        for name, mood in MOODS.items():
            self.assertLessEqual(len(mood["story"]), 3, name)
            self.assertLessEqual(len(mood["good"]) + len(mood["bad"]), 3, name)


class PlaceTests(unittest.TestCase):
    def test_a_mood_can_keep_him_at_one_place(self):
        for mood, numbers in MOODS.items():
            if "place" not in numbers or numbers["move"] > 0:
                continue
            teacher = Teacher(random.Random(3), mood)
            for _ in range(round(300 / DT)):
                teacher.update(DT)
                self.assertEqual(teacher.place, numbers["place"])
                self.assertFalse(teacher.erasing() and numbers["place"] == DESK)

    def test_places_in_moods_are_real(self):
        for numbers in MOODS.values():
            self.assertIn(numbers.get("place", BOARD), (BOARD, DESK))


class KeepWatchingTests(unittest.TestCase):
    def watching_teacher(self):
        teacher = Teacher(random.Random(4))
        while teacher.state != WATCHING:
            teacher.update(DT)
        return teacher

    def test_keeps_watching_while_suspicious(self):
        teacher = self.watching_teacher()
        for _ in range(round(30 / DT)):   # far longer than any watching time
            self.assertEqual(teacher.update(DT, keep_watching=True), [])
        self.assertEqual(teacher.state, WATCHING)

    def test_goes_back_to_work_when_not(self):
        teacher = self.watching_teacher()
        for _ in range(round(30 / DT)):
            teacher.update(DT, keep_watching=True)
        self.assertIn("state:" + BUSY, teacher.update(DT))

    def test_busy_teacher_is_not_affected(self):
        teacher = Teacher(random.Random(5))
        for _ in range(round(10 / DT)):
            teacher.update(DT, keep_watching=True)
            if teacher.state == WATCHING:
                break
        self.assertEqual(teacher.state, WATCHING)   # he still turns as usual


class MoodTests(unittest.TestCase):
    def test_every_mood_keeps_its_durations(self):
        # A mood only changes the numbers: each state lasts inside its range.
        for mood, numbers in MOODS.items():
            teacher = Teacher(random.Random(1), mood)
            limits = {BUSY: numbers["busy"], WATCHING: numbers["watching"],
                      TURNING: TEACHER_DURATIONS[TURNING]}
            for state, _, lasted in ten_minutes(teacher):
                shortest, longest = limits[state]
                self.assertGreaterEqual(lasted, shortest - 1e-6, (mood, state))
                self.assertLessEqual(lasted, longest + DT + 1e-6, (mood, state))

    def test_moods_move_as_often_as_they_say(self):
        # A restless mood changes place more often than a calm one.
        def moves(mood):
            places = [place for _, place, _ in ten_minutes(Teacher(random.Random(2), mood))]
            return sum(a != b for a, b in zip(places, places[1:]))
        calm = min(MOODS, key=lambda mood: MOODS[mood]["move"])
        restless = max(MOODS, key=lambda mood: MOODS[mood]["move"])
        self.assertGreater(moves(restless), moves(calm))

    def test_no_mood_is_the_plain_teacher(self):
        teacher = Teacher(random.Random(3))
        self.assertEqual(teacher.durations, TEACHER_DURATIONS)


if __name__ == "__main__":
    unittest.main()
