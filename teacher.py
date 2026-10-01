"""
The teacher: where they are and what they are doing.

The teacher is a "state machine": they are always in one state, and after a
random time they switch to the next one:

    BUSY  ->  TURNING  ->  WATCHING  ->  BUSY  -> ...
    safe      safe, but    copying now
              a warning    = caught
              sound plays

There are two places, the BOARD (erasing it) and the DESK (on the phone).
After WATCHING the teacher sometimes moves to the other place. Place + state
decide which classroom picture is shown (see image_name()).

TURNING is the fair warning: the player is often looking away from the
screen, so its sound tells them to stop copying before the teacher looks.
But while the player looks down at the paper they hear nothing from the
teacher (see sounds()), so they have to look up to find out what is going on.

This file only does the logic; it draws and plays nothing, so it can be
tested without a window (see tests/test_teacher.py).
"""

import random

from settings import TEACHER_DURATIONS, MOVE_CHANCE, CAUGHT_GRACE

BUSY, TURNING, WATCHING = "BUSY", "TURNING", "WATCHING"
BOARD, DESK = "BOARD", "DESK"


class Teacher:
    def __init__(self, rng=None):
        # Tests pass a random.Random with a fixed seed, so the "random"
        # durations are the same every run.
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        self.place = BOARD
        self.start(BUSY)

    def start(self, state):
        """Switch to `state` and pick how long it will last."""
        self.state = state
        self.time_in_state = 0.0
        self.turning_heard = False   # has the player heard this TURNING yet?
        shortest, longest = TEACHER_DURATIONS[state]
        self.duration = self.rng.uniform(shortest, longest)

    def update(self, dt):
        """
        Move the teacher forward by dt seconds. Returns ["state:<NEW STATE>"]
        when the state changes (main.py plays a sound for it), otherwise [].
        """
        self.time_in_state += dt
        if self.time_in_state < self.duration:
            return []

        if self.state == BUSY:
            self.start(TURNING)
        elif self.state == TURNING:
            self.start(WATCHING)
        else:
            # Back to work, sometimes at the other place.
            if self.rng.random() < MOVE_CHANCE:
                self.place = DESK if self.place == BOARD else BOARD
            self.start(BUSY)
        return ["state:" + self.state]

    def sounds(self, events, can_hear):
        """
        Which of this frame's events (from update()) the player hears.
        can_hear=False (looking down at the paper): nothing at all.
        The turning sound is also played when the player looks up while the
        teacher is still turning, so it is never missed by looking up late.
        It plays once per turn.
        """
        if not can_hear:
            return []
        heard = [event for event in events if event != "state:" + TURNING]
        if self.state == TURNING and not self.turning_heard:
            self.turning_heard = True
            heard.append("state:" + TURNING)
        return heard

    def is_facing_class(self):
        """True while the teacher looks at the class (the picture shows it)."""
        return self.state == WATCHING

    def is_watching(self):
        """
        True = looking sideways now fills the suspicion bar fast (and gets you
        caught when it is full). The first CAUGHT_GRACE seconds of WATCHING
        don't count: that covers the head tracker's delay.
        """
        return self.state == WATCHING and self.time_in_state >= CAUGHT_GRACE

    def image_name(self):
        """
        Which classroom picture to show, e.g. "classroom_board_busy".
        While TURNING the teacher has not looked up yet, so it is the busy picture.
        """
        looking = "watching" if self.state == WATCHING else "busy"
        return f"classroom_{self.place.lower()}_{looking}"
