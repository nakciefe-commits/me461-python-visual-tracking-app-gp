"""
Game rules: copying, staring, warnings, winning and losing.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "tick" or "warning") so main.py knows which sounds to play.

Keeping the rules apart from the drawing means the rules can be tested without
a camera or a window (see tests/test_game.py).
"""

from head_tracker import SCREEN, LEFT, RIGHT
from settings import (ANSWERS_NEEDED, COPY_TIME, STARE_GRACE_TIME, STARE_FILL_TIME,
                      MAX_WARNINGS, POPUP_TIME, TICK_INTERVAL)

PLAYING, WON, LOST = "PLAYING", "WON", "LOST"

# Staring this long in one go gives a warning.
WARNING_TIME = STARE_GRACE_TIME + STARE_FILL_TIME


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.answers = 0
        self.warnings = 0

        self.copy_time = 0.0      # seconds of looking sideways in one go
        self.copy_locked = False  # True after an answer, until you look away
        self.next_tick = 0.0      # copy_time at which the next tick sound plays

        self.stare_time = 0.0     # seconds of looking at the screen in one go

        self.popup_text = None    # warning message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears

    def update(self, direction, dt):
        """
        Move the game forward by dt seconds. `direction` is DOWN, SCREEN, LEFT
        or RIGHT. Returns a list of events, e.g. ["tick", "answer"].
        """
        events = []
        if self.state != PLAYING:
            return events

        # The popup disappears after POPUP_TIME seconds.
        self.popup_timer -= dt
        if self.popup_timer <= 0:
            self.popup_text = None

        # --- Option 3: copying from a neighbour ---
        if direction in (LEFT, RIGHT):
            if not self.copy_locked:
                if self.copy_time >= self.next_tick:   # first tick right at the start
                    events.append("tick")
                    self.next_tick += TICK_INTERVAL
                self.copy_time += dt

                if self.copy_time >= COPY_TIME:
                    self.answers += 1
                    events.append("answer")
                    self.copy_time = 0.0
                    self.next_tick = 0.0
                    self.copy_locked = True   # must look away before the next one
                    if self.answers == ANSWERS_NEEDED:
                        self.state = WON
                        events.append("won")
        else:
            # Looked away: copying starts over.
            self.copy_time = 0.0
            self.next_tick = 0.0
            self.copy_locked = False

        # --- Option 2: staring at the teacher ---
        if direction == SCREEN:
            self.stare_time += dt
            if self.stare_time >= WARNING_TIME:
                self.warnings += 1
                events.append("warning")
                self.popup_text = (f"The teacher noticed you staring! "
                                   f"Warning {self.warnings}/{MAX_WARNINGS}")
                self.popup_timer = POPUP_TIME
                self.stare_time = 0.0
                if self.warnings == MAX_WARNINGS:
                    self.state = LOST
                    events.append("lost")
        else:
            self.stare_time = 0.0

        return events
