"""Tests for the menu logic in menu.py (no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random

from logic.menu import (Menu, HeadMenuInput, loading_steps, loading_progress,
                  UP, DOWN, SELECT, BACK)
from settings import (MENU_PITCH_THRESHOLD, MENU_YAW_THRESHOLD, MENU_MOVE_HOLD,
                      MENU_REPEAT_TIME, MENU_SELECT_TIME,
                      HEAD_PAUSE_AFTER_KEYS)

DT = 0.01
# Clearly past each threshold, whatever they are set to in settings.py.
TILT_UP = (0, MENU_PITCH_THRESHOLD + 5)
TILT_DOWN = (0, -(MENU_PITCH_THRESHOLD + 5))
TURN_RIGHT = (-(MENU_YAW_THRESHOLD + 5), 0)   # negative yaw = the player's right
TURN_LEFT = (MENU_YAW_THRESHOLD + 5, 0)
STRAIGHT = (0, 0)


def hold(head_input, angles, seconds, face_found=True):
    """Hold the head at `angles` for `seconds`. Returns the actions, in order."""
    actions = []
    for _ in range(round(seconds / DT)):
        action = head_input.update(*angles, DT, face_found)
        if action is not None:
            actions.append(action)
    return actions


def armed_input():
    """A HeadMenuInput that has already seen the head straight."""
    head_input = HeadMenuInput()
    hold(head_input, STRAIGHT, 0.1)
    return head_input


class MenuTests(unittest.TestCase):
    def test_move_and_wrap(self):
        menu = Menu(["PLAY", "HELP", "QUIT"])
        self.assertEqual(menu.current(), "PLAY")
        menu.move(1)
        self.assertEqual(menu.current(), "HELP")
        menu.move(-1)
        menu.move(-1)
        self.assertEqual(menu.current(), "QUIT")   # up from the top = the bottom
        menu.move(1)
        self.assertEqual(menu.current(), "PLAY")   # down from the bottom = the top


class PoseTests(unittest.TestCase):
    def test_poses(self):
        self.assertIsNone(HeadMenuInput.pose(*STRAIGHT))
        self.assertEqual(HeadMenuInput.pose(*TILT_UP), UP)
        self.assertEqual(HeadMenuInput.pose(*TILT_DOWN), DOWN)
        self.assertEqual(HeadMenuInput.pose(*TURN_RIGHT), SELECT)
        self.assertEqual(HeadMenuInput.pose(*TURN_LEFT), BACK)

    def test_small_movements_do_nothing(self):
        self.assertIsNone(HeadMenuInput.pose(MENU_YAW_THRESHOLD - 3, MENU_PITCH_THRESHOLD - 3))

    def test_sideways_menu(self):
        # The character row: turning moves, tilting down chooses, tilting up goes back.
        head = HeadMenuInput()
        head.horizontal = True
        head.update(*STRAIGHT, 0.1, True)          # straight once: armed
        actions = [head.update(*TURN_RIGHT, MENU_MOVE_HOLD, True)]
        self.assertEqual(actions, [DOWN])          # the next one
        head.update(*STRAIGHT, 0.1, True)
        self.assertEqual(head.update(*TURN_LEFT, MENU_MOVE_HOLD, True), UP)
        head.update(*STRAIGHT, 0.1, True)
        self.assertIsNone(head.update(*TILT_DOWN, MENU_SELECT_TIME / 2, True))
        self.assertEqual(head.update(*TILT_DOWN, MENU_SELECT_TIME / 2, True), SELECT)
        head.update(*STRAIGHT, 0.1, True)
        head.update(*TILT_UP, MENU_SELECT_TIME / 2, True)
        self.assertEqual(head.update(*TILT_UP, MENU_SELECT_TIME / 2, True), BACK)

    def test_calibrated_turns(self):
        # A player who turns only a little: the menu asks for their own turn.
        head = HeadMenuInput()
        head.set_turns(10, 12)
        self.assertEqual(head.left_turn, 10)
        self.assertEqual(head.right_turn, 12)
        self.assertEqual(HeadMenuInput.pose(-13, 0, head.left_turn, head.right_turn), SELECT)
        self.assertEqual(HeadMenuInput.pose(11, 0, head.left_turn, head.right_turn), BACK)
        # Never more than the fixed menu turn.
        head.set_turns(40, 40)
        self.assertEqual(head.left_turn, MENU_YAW_THRESHOLD)

    def test_turn_wins_over_tilt(self):
        self.assertEqual(HeadMenuInput.pose(TURN_RIGHT[0], TILT_DOWN[1]), SELECT)


class HeadMenuInputTests(unittest.TestCase):
    def test_nothing_until_head_was_straight(self):
        # Entering a menu with the head already turned must not select anything.
        head_input = HeadMenuInput()
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME * 3), [])
        hold(head_input, STRAIGHT, 0.1)
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME + 0.05), [SELECT])

    def test_tilt_moves_after_hold_time(self):
        head_input = armed_input()
        self.assertEqual(hold(head_input, TILT_DOWN, MENU_MOVE_HOLD - 0.05), [])
        self.assertEqual(hold(head_input, TILT_DOWN, 0.1), [DOWN])

    def test_holding_a_tilt_repeats(self):
        head_input = armed_input()
        actions = hold(head_input, TILT_UP, MENU_MOVE_HOLD + 2 * MENU_REPEAT_TIME + 0.05)
        self.assertEqual(actions, [UP, UP, UP])

    def test_select_needs_hold_time(self):
        head_input = armed_input()
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME - 0.1), [])
        self.assertGreater(head_input.progress(SELECT), 0.5)
        self.assertEqual(head_input.progress(BACK), 0.0)
        self.assertEqual(hold(head_input, TURN_RIGHT, 0.15), [SELECT])

    def test_glance_does_not_select(self):
        head_input = armed_input()
        hold(head_input, TURN_RIGHT, MENU_SELECT_TIME / 2)
        hold(head_input, STRAIGHT, 0.05)
        self.assertEqual(head_input.progress(SELECT), 0.0)   # starts over
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME / 2), [])

    def test_one_long_turn_selects_once(self):
        head_input = armed_input()
        self.assertEqual(hold(head_input, TURN_LEFT, MENU_SELECT_TIME * 4), [BACK])

    def test_keys_pause_head_control(self):
        head_input = armed_input()
        hold(head_input, TURN_RIGHT, MENU_SELECT_TIME / 2)
        head_input.pause()                       # a key was pressed
        self.assertEqual(head_input.progress(SELECT), 0.0)   # the half-done turn is forgotten
        self.assertEqual(hold(head_input, TURN_RIGHT, HEAD_PAUSE_AFTER_KEYS), [])
        self.assertEqual(head_input.paused_part(), 0.0)
        # Still turned after the pause: needs a straight head first.
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME * 2), [])
        hold(head_input, STRAIGHT, 0.1)
        self.assertEqual(hold(head_input, TILT_DOWN, MENU_MOVE_HOLD + 0.05), [DOWN])

    def test_face_lost_does_nothing(self):
        head_input = armed_input()
        self.assertEqual(hold(head_input, TURN_RIGHT, MENU_SELECT_TIME * 2, face_found=False), [])


class LoadingTests(unittest.TestCase):
    def setUp(self):
        self.steps = loading_steps(random.Random(4))
        self.values = [loading_progress(i / 100, self.steps) for i in range(101)]

    def test_starts_empty_ends_full(self):
        self.assertEqual(self.values[0], 0.0)
        self.assertEqual(self.values[-1], 1.0)

    def test_never_goes_back(self):
        for before, after in zip(self.values, self.values[1:]):
            self.assertLessEqual(before, after)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in self.values))

    def test_gets_stuck_and_jumps(self):
        # Not an even fill: some moments it does not move, some it jumps.
        moves = [after - before for before, after in zip(self.values, self.values[1:])]
        self.assertGreater(moves.count(0.0), 20)
        self.assertGreater(max(moves), 0.03)   # an even fill would move 0.01 each time

    def test_not_full_before_the_end(self):
        self.assertLess(loading_progress(0.97, self.steps), 1.0)


if __name__ == "__main__":
    unittest.main()
