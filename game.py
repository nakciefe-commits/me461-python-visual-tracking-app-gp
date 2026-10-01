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


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings" (later also "caught", "time")

        self.answers = 0
        self.warnings = 0

        # Copying (option 3)
        self.copy_time = 0.0      # seconds of looking sideways so far
        self.copy_progress = 0.0  # the same, as 0.0-1.0 for the bar
        self.copy_locked = False  # True after an answer, until you look away
        self.next_tick = 0.0      # copy_time at which the next tick plays

        # Staring at the teacher (option 2)
        self.stare_time = 0.0     # seconds of looking at the screen so far
        self.suspicion = 0.0      # the part after the grace time, 0.0-1.0

        self.popup_text = None
        self.popup_timer = 0.0

    def update(self, direction, dt, teacher=None):
        """
        Move the game forward by dt seconds. `direction` is DOWN, SCREEN, LEFT
        or RIGHT. `teacher` is not used yet. Returns a list of events.
        """
        events = []
        if self.state != PLAYING:
            return events

        self._update_popup(dt)
        self._update_copying(direction, dt, events)
        if self.state == PLAYING:
            self._update_staring(direction, dt, events)
        return events

    def _update_popup(self, dt):
        if self.popup_text is not None:
            self.popup_timer -= dt
            if self.popup_timer <= 0:
                self.popup_text = None

    def _update_copying(self, direction, dt, events):
        if direction not in (LEFT, RIGHT):
            # Looked away: progress is lost, and the next answer can start.
            self.copy_time = 0.0
            self.copy_progress = 0.0
            self.copy_locked = False
            self.next_tick = 0.0
            return

        if self.copy_locked:
            return  # just finished an answer; look away before the next one

        # Tick first, so a tick plays the moment copying starts.
        if self.copy_time >= self.next_tick:
            events.append("tick")
            self.next_tick += TICK_INTERVAL

        self.copy_time += dt
        self.copy_progress = min(self.copy_time / COPY_TIME, 1.0)

        if self.copy_time >= COPY_TIME:
            self.answers += 1
            events.append("answer")
            self.copy_time = 0.0
            self.copy_progress = 0.0
            self.next_tick = 0.0
            self.copy_locked = True
            if self.answers >= ANSWERS_NEEDED:
                self.state = WON
                events.append("won")

    def _update_staring(self, direction, dt, events):
        if direction != SCREEN:
            self.stare_time = 0.0
            self.suspicion = 0.0
            return

        self.stare_time += dt
        # The bar only starts filling once the grace time is over.
        filled = (self.stare_time - STARE_GRACE_TIME) / STARE_FILL_TIME
        self.suspicion = max(0.0, min(filled, 1.0))

        if self.suspicion >= 1.0:
            self.warnings += 1
            events.append("warning")
            self.popup_text = (f"The teacher noticed you staring! "
                               f"Warning {self.warnings}/{MAX_WARNINGS}")
            self.popup_timer = POPUP_TIME
            self.stare_time = 0.0
            self.suspicion = 0.0
            if self.warnings >= MAX_WARNINGS:
                self.state = LOST
                self.lose_reason = "warnings"
                events.append("lost")
