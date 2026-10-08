"""
Menus: which item is selected, and how head movements choose one. Also the
loading bar's fake progress (loading_steps(), loading_progress()).

Every menu (main menu, settings, how to play, the end screen) is a list of
items with one of them selected. The player moves the selection with the head:
    tilt UP / DOWN     move the selection up / down
    turn RIGHT         select the item (hold it until the bar is full)
    turn LEFT          go back (hold it until the bar is full)
The keyboard (arrows, Enter, Esc) and the mouse do the same things; main.py
turns them into the same four actions.

A menu laid out sideways (the character row) uses the head the other way
round (horizontal=True): turn LEFT / RIGHT to move, tilt DOWN (hold) to
choose, tilt UP (hold) to go back.

Like game.py, this file draws nothing and does not import pygame, so it can be
tested without a camera or a window (see tests/test_menu.py).
"""

from settings import (MENU_PITCH_THRESHOLD, MENU_YAW_THRESHOLD, MENU_MOVE_HOLD,
                      MENU_REPEAT_TIME, MENU_SELECT_TIME, LOADING_JUMPS, LOADING_STALL,
                      HEAD_PAUSE_AFTER_KEYS)

# The four things a player can do in a menu.
UP, DOWN, SELECT, BACK = "up", "down", "select", "back"
# A sideways menu: what each head pose (named as in a normal menu) means there.
# Turning moves (left = the one before, right = the next), tilting chooses.
HORIZONTAL = {BACK: UP, SELECT: DOWN, DOWN: SELECT, UP: BACK}


class Menu:
    """A list of item names with one selected. The selection wraps around."""

    def __init__(self, items):
        self.items = list(items)
        self.selected = 0

    def move(self, step):
        """step = -1 moves up, +1 moves down; past the end it wraps to the other end."""
        self.selected = (self.selected + step) % len(self.items)

    def current(self):
        """The name of the selected item."""
        return self.items[self.selected]


class HeadMenuInput:
    """
    Turns the head angles of each frame into menu actions.

    Moving up/down happens after the tilt has lasted MENU_MOVE_HOLD, and then
    again every MENU_REPEAT_TIME while the head stays tilted, so the player can
    scroll by holding the tilt. Selecting and going back need the turn to be
    held for MENU_SELECT_TIME (a bar fills on the screen), so a quick glance
    does not choose anything by accident.

    After entering a menu, nothing happens until the head has been straight
    once: the player may still be turned from the last screen.

    Using the keyboard or the mouse turns head control off for a moment
    (pause()), so the head does not fight the keys; after it, the head must
    be straight once again.
    """

    def __init__(self):
        self.paused_time = 0.0   # seconds head control stays off after a key press
        # Degrees to turn left / right; main.py sets them to the player's
        # own (calibrated) turns, but never more than MENU_YAW_THRESHOLD.
        self.left_turn = MENU_YAW_THRESHOLD
        self.right_turn = MENU_YAW_THRESHOLD
        self.horizontal = False  # True on a sideways menu (see HORIZONTAL)
        self.reset()

    def reset(self):
        """Call when a new menu opens."""
        self.armed = False     # True once the head has been straight since reset()
        self.held = None       # the pose being held right now: UP, DOWN, SELECT, BACK or None
        self.held_time = 0.0   # seconds it has been held

    def set_turns(self, left, right):
        """The player's calibrated turns (degrees); the menus never ask for more than MENU_YAW_THRESHOLD."""
        self.left_turn = min(MENU_YAW_THRESHOLD, left)
        self.right_turn = min(MENU_YAW_THRESHOLD, right)

    @staticmethod
    def pose(yaw, pitch, left_turn=MENU_YAW_THRESHOLD, right_turn=MENU_YAW_THRESHOLD):
        """
        Which action the head points at, or None for straight. yaw and pitch
        are measured from the calibrated screen angles (positive yaw = the
        player's left, positive pitch = up). Turning wins over tilting.
        """
        if yaw < -right_turn:
            return SELECT          # turned right
        if yaw > left_turn:
            return BACK            # turned left
        if pitch > MENU_PITCH_THRESHOLD:
            return UP
        if pitch < -MENU_PITCH_THRESHOLD:
            return DOWN
        return None

    def pause(self):
        """A key was pressed or the mouse clicked: head control off for HEAD_PAUSE_AFTER_KEYS."""
        self.paused_time = HEAD_PAUSE_AFTER_KEYS
        self.reset()   # forget any half-done turn, and wait for a straight head after

    def paused_part(self):
        """How much of the pause is left: 1 = just paused, 0 = head control is on."""
        return self.paused_time / HEAD_PAUSE_AFTER_KEYS

    def update(self, yaw, pitch, dt, face_found):
        """Call once per frame. Returns UP, DOWN, SELECT, BACK or None."""
        if self.paused_time > 0:
            self.paused_time = max(0.0, self.paused_time - dt)
            return None
        if not face_found:
            # The angles are old: forget the pose, but stay armed.
            self.held = None
            self.held_time = 0.0
            return None

        pose = self.pose(yaw, pitch, self.left_turn, self.right_turn)
        if pose is not None and self.horizontal:
            pose = HORIZONTAL[pose]   # the same head, read sideways
        if pose is None:
            self.armed = True
            self.held = None
            self.held_time = 0.0
            return None
        if not self.armed:
            return None

        if pose != self.held:
            self.held = pose       # a new pose: start timing it
            self.held_time = 0.0
        self.held_time += dt

        if pose in (UP, DOWN):
            if self.held_time >= MENU_MOVE_HOLD:
                # The next step comes MENU_REPEAT_TIME later, if still tilted.
                self.held_time -= MENU_REPEAT_TIME
                return pose
            return None

        if self.held_time >= MENU_SELECT_TIME:
            # Chosen. The head must come back straight before the next choice,
            # otherwise one long turn would select again on the next screen.
            self.armed = False
            self.held = None
            self.held_time = 0.0
            return pose
        return None

    def progress(self, pose):
        """How far turning towards SELECT or BACK has got, 0..1 (for the bar)."""
        if self.held != pose:
            return 0.0
        return min(1.0, self.held_time / MENU_SELECT_TIME)


def loading_steps(rng):
    """
    A random plan for the loading bar, so it fills like a real one: stuck,
    then a jump, stuck again... Returns a list of (time, progress) points,
    both 0..1, from (0, 0) to (1, 1). `rng` is a random.Random (tests pass
    one with a fixed seed).
    """
    times = sorted(rng.uniform(0.05, 0.9) for _ in range(LOADING_JUMPS))
    amounts = sorted(rng.uniform(0.05, 0.97) for _ in range(LOADING_JUMPS))
    return [(0.0, 0.0)] + list(zip(times, amounts)) + [(1.0, 1.0)]


def loading_progress(time, steps):
    """
    How full the loading bar is (0..1) at `time` (0..1 of the loading
    screen). Between two points of `steps` the bar is stuck for the first
    LOADING_STALL part, then quickly fills up to the next point. The last
    jump, to 100 %, comes right at the end: "stuck at 97 %", like real ones.
    """
    for (start_time, start), (end_time, end) in zip(steps, steps[1:]):
        if time <= end_time:
            if end_time == start_time:
                return end
            part = (time - start_time) / (end_time - start_time)   # 0..1 of this gap
            jump = max(0.0, (part - LOADING_STALL) / (1 - LOADING_STALL))
            return start + (end - start) * jump
    return 1.0
