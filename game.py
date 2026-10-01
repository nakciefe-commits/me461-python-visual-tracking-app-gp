"""
Game rules: copying, staring, warnings, getting caught, the exam clock,
winning and losing.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "tick" or "warning") so main.py knows which sounds to play.

Keeping the rules apart from the drawing means the rules can be tested without
a camera or a window (see tests/test_game.py).
"""

from head_tracker import SCREEN, LEFT, RIGHT
from settings import (ANSWERS_NEEDED, COPY_TIME, STARE_GRACE_TIME, STARE_FILL_TIME,
                      MAX_WARNINGS, POPUP_TIME, TICK_INTERVAL, EXAM_TIME,
                      STARE_ONLY_WHEN_FACING, CAUGHT_TIME, SUSPICION_DRAIN_TIME)

PLAYING, WON, LOST = "PLAYING", "WON", "LOST"

# Staring this long (from an empty bar) gives a warning.
WARNING_TIME = STARE_GRACE_TIME + STARE_FILL_TIME
# The free part of the suspicion bar: staring only gets dangerous past it.
GRACE_PART = STARE_GRACE_TIME / WARNING_TIME


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings", "caught" or "time" once lost
        self.time_left = EXAM_TIME
        self.answers = 0
        self.warnings = 0

        self.copy_time = 0.0      # seconds copied of the current answer (kept when looking away)
        self.copy_locked = False  # True after an answer, until you look away
        self.next_tick = 0.0      # copy_time at which the next tick sound plays

        # The suspicion bar, 0 (empty) to 1 (full). Staring at the teacher
        # fills it slowly, being seen copying fills it fast. It never jumps
        # back to empty (that would tell the player the teacher looked away):
        # it drains slowly whenever you are not doing anything suspicious.
        self.suspicion_level = 0.0
        self.seen_copying = False # the bar was raised by being seen copying (drawn red)
        self.was_seen = False     # seen copying last frame? (the alarm plays when it starts)

        self.popup_text = None    # warning message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears

    def suspicion(self):
        """How full the suspicion bar is, 0..1."""
        return self.suspicion_level

    def warn(self, events):
        """Staring filled the bar: one more warning, and the bar starts over."""
        self.warnings += 1
        events.append("warning")
        self.popup_text = (f"The teacher noticed you staring! "
                           f"Warning {self.warnings}/{MAX_WARNINGS}")
        self.popup_timer = POPUP_TIME
        self.suspicion_level = 0.0
        self.seen_copying = False
        if self.warnings == MAX_WARNINGS:
            self.lose("warnings", events)

    def lose(self, reason, events):
        self.state = LOST
        self.lose_reason = reason
        # "lost" for anything that only cares about game over, and e.g.
        # "lost_caught" so each way of losing can have its own sound.
        events.append("lost")
        events.append("lost_" + reason)

    def update(self, direction, dt, teacher=None):
        """
        Move the game forward by dt seconds. `direction` is DOWN, SCREEN, LEFT
        or RIGHT. `teacher` is a Teacher, or None for the demo without one.
        Returns a list of events, e.g. ["tick", "answer"].
        """
        events = []
        if self.state != PLAYING:
            return events

        # The popup disappears after POPUP_TIME seconds.
        self.popup_timer -= dt
        if self.popup_timer <= 0:
            self.popup_text = None

        # --- The suspicion bar ---
        # Seen copying (looking sideways while the teacher watches): it fills
        # in CAUGHT_TIME; full = caught. Staring at the teacher while they
        # look at the class: it fills in WARNING_TIME; full = a warning. Both
        # add to the same bar, so after being seen, staring carries on from
        # there. Neither: it drains slowly.
        seen = direction in (LEFT, RIGHT) and teacher is not None and teacher.is_watching()
        teacher_sees = (teacher is None or not STARE_ONLY_WHEN_FACING
                        or teacher.is_facing_class())
        staring = direction == SCREEN and teacher_sees
        if seen:
            if not self.was_seen:
                events.append("spotted")   # alarm: the screen is black, so the player must hear it
            self.seen_copying = True
            self.suspicion_level += dt / CAUGHT_TIME
            if self.suspicion_level >= 1:
                events.append("caught")
                self.lose("caught", events)
                return events
        elif staring:
            self.suspicion_level += dt / WARNING_TIME
            if self.suspicion_level >= 1:
                self.warn(events)
        else:
            self.suspicion_level = max(0.0, self.suspicion_level - dt / SUSPICION_DRAIN_TIME)
            if self.suspicion_level == 0:
                self.seen_copying = False
        self.was_seen = seen

        # --- Option 3: copying from a neighbour ---
        # While the teacher sees you, copying does not move forward: glancing
        # sideways then is all risk and no gain.
        if direction in (LEFT, RIGHT):
            if not self.copy_locked and not seen:
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
            # Looked away: the copy bar keeps its progress, so an answer can be
            # copied in pieces. Ticking starts again right away on looking back.
            self.next_tick = self.copy_time
            self.copy_locked = False

        # --- The exam clock ---
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left == 0 and self.state == PLAYING:
            self.lose("time", events)

        return events
