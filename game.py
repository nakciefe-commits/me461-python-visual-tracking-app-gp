"""
Game rules: exam papers, keyboard answers, suspicion and the exam clock.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "spotted" or "warning") so main.py knows which sounds to play.
answer() handles keyboard marks and returns the "answer" and "won" events.

Keeping the rules apart from the drawing means the rules can be tested without
a camera or a window (see tests/test_game.py).
"""

import random

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (ANSWERS_NEEDED, ANSWER_CHOICES, STARE_GRACE_TIME, STARE_FILL_TIME,
                      MAX_WARNINGS, POPUP_TIME, EXAM_TIME,
                      STARE_ONLY_WHEN_FACING, CAUGHT_TIME, SUSPICION_DRAIN_TIME,
                      PAPER_FOCUS_TIME)

PLAYING, WON, LOST = "PLAYING", "WON", "LOST"

# Staring this long (from an empty bar) gives a warning.
WARNING_TIME = STARE_GRACE_TIME + STARE_FILL_TIME
# The free part of the suspicion bar: staring only gets dangerous past it.
GRACE_PART = STARE_GRACE_TIME / WARNING_TIME
# The bar counts as full from here. Adding up many small dt / time steps can
# end just below 1 because of rounding (e.g. 24 steps of 0.125 / 3.0).
FULL = 1 - 1e-9


class Game:
    def __init__(self, rng=None):
        # A seeded Random lets tests repeat exactly the same exam.
        self.rng = rng or random.Random()
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings", "caught" or "time" once lost
        self.time_left = EXAM_TIME
        self.answer_key = tuple(self.rng.choice(ANSWER_CHOICES) for _ in range(ANSWERS_NEEDED))
        # Both neighbours take the same exam. Their marks stay fixed until reset.
        self.neighbour_answers = {LEFT: self.answer_key, RIGHT: self.answer_key}
        self.player_answers = [None] * ANSWERS_NEEDED
        self.active_question = 0  # zero-based index of the question the keyboard answers
        self.reset_paper_focus()
        self.warnings = 0

        # The suspicion bar, 0 (empty) to 1 (full). Staring at the teacher
        # fills it slowly, being seen copying fills it fast. It never jumps
        # back to empty (that would tell the player the teacher looked away):
        # it drains slowly whenever you are not doing anything suspicious.
        self.suspicion_level = 0.0
        self.seen_copying = False # the bar was raised by being seen copying (drawn red)
        self.was_seen = False     # seen copying last frame? (the alarm plays when it starts)

        self.popup_text = None    # warning message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears

    @property
    def answers(self):
        """Number of questions marked on the player's paper."""
        return sum(choice is not None for choice in self.player_answers)

    @property
    def correct_answers(self):
        """Used for winning and the final score, never to mark the player's paper."""
        return sum(choice == expected for choice, expected
                   in zip(self.player_answers, self.answer_key))

    def can_write(self, direction):
        """Return to your own paper first; paused and finished games reject input."""
        return self.state == PLAYING and direction in (DOWN, SCREEN)

    def reset_paper_focus(self):
        """Every new sideways look starts blurry, including after tracking pauses."""
        self.paper_focus_time = 0.0
        self.paper_direction = None

    @property
    def paper_clarity(self):
        """0 = fully blurred, 1 = sharp; drawing does not change this timer."""
        return min(1.0, max(0.0, self.paper_focus_time / PAPER_FOCUS_TIME))

    def select_question(self, index, direction):
        """Select a question to revisit without changing any answers."""
        if not self.can_write(direction) or not 0 <= index < ANSWERS_NEEDED:
            return False
        if index != self.active_question:
            self.reset_paper_focus()
        self.active_question = index
        return True

    def move_question(self, step, direction):
        """Arrow keys wrap around the paper, including already answered questions."""
        return self.select_question((self.active_question + step) % ANSWERS_NEEDED, direction)

    def answer(self, choice, direction):
        """Mark A..E by hand; looking at a neighbour never writes an answer."""
        if not self.can_write(direction) or not isinstance(choice, str):
            return []
        choice = choice.lower()
        if choice not in ANSWER_CHOICES:
            return []
        self.player_answers[self.active_question] = choice
        self.reset_paper_focus()
        events = ["answer"]
        if self.correct_answers == ANSWERS_NEEDED:
            self.state = WON
            events.append("won")
        elif self.answers == ANSWERS_NEEDED:
            # Give one overall hint instead of revealing which marks are wrong.
            self.popup_text = "Some answers differ. Check the papers; use Up / Down to revise."
            self.popup_timer = POPUP_TIME
        else:
            # Move to the next blank question so normal play only needs A..E.
            for step in range(1, ANSWERS_NEEDED + 1):
                index = (self.active_question + step) % ANSWERS_NEEDED
                if self.player_answers[index] is None:
                    self.active_question = index
                    break
        return events

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
        Returns sound events. Answer keys are handled separately by answer().
        """
        events = []
        if self.state != PLAYING:
            return events

        # Focus belongs to one continuous look at one neighbour. Switching
        # sides or looking at your own paper/the teacher starts it over.
        if direction in (LEFT, RIGHT):
            if self.paper_direction != direction:
                self.reset_paper_focus()
                self.paper_direction = direction
            self.paper_focus_time = min(PAPER_FOCUS_TIME, self.paper_focus_time + dt)
        else:
            self.reset_paper_focus()

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
                events.append("spotted")   # the paper hides the teacher, so the player must hear it
            self.seen_copying = True
            self.suspicion_level += dt / CAUGHT_TIME
            if self.suspicion_level >= FULL:
                events.append("caught")
                self.lose("caught", events)
                return events
        elif staring:
            self.suspicion_level += dt / WARNING_TIME
            if self.suspicion_level >= FULL:
                self.warn(events)
        else:
            self.suspicion_level = max(0.0, self.suspicion_level - dt / SUSPICION_DRAIN_TIME)
            if self.suspicion_level == 0:
                self.seen_copying = False
        self.was_seen = seen

        # --- The exam clock ---
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left == 0 and self.state == PLAYING:
            self.lose("time", events)

        return events
