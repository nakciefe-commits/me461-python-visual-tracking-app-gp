"""
Game rules: copying, staring, warnings, getting caught, the exam clock,
winning and losing.

How an answer gets onto your paper:
    1. Each question has a right letter (A-D), and only ONE neighbour (left or
       right, chosen at random) knows it. The other one's paper shows "?".
    2. Look at a neighbour: their paper is blurry and gets sharper the
       longer you look, without looking away (each look starts blurry again).
       Once it is sharp you have read it (the letter, or "?" = "try the
       other side"). Idea and first version: Emre (gradual focus).
    3. Look down at your own paper and press the letter (write()). You must
       remember it: the letter is only shown on the neighbour's paper.
       Any letter can be written, but only after the answer has been read;
       wrong letters only show up in the grade at the end.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "read" or "warning") so main.py knows which sounds to play.

Keeping the rules apart from the drawing means the rules can be tested without
a camera or a window (see tests/test_game.py).
"""

import random

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (ANSWERS_NEEDED, PAPER_FOCUS_TIME, STARE_GRACE_TIME, STARE_FILL_TIME,
                      MAX_WARNINGS, POPUP_TIME, EXAM_TIME, WARNING_SCENE_TIME,
                      CAUGHT_SCENE_TIME, CAUGHT_EXCLAIM_TIME, GAME_OVER_TIME,
                      STARE_ONLY_WHEN_FACING, CAUGHT_TIME, SUSPICION_DRAIN_TIME,
                      SCORE_PER_CORRECT, SCORE_TIME_BONUS, SCORE_PER_CLOSE_CALL, SCORE_PER_WARNING)

PLAYING, WON, LOST = "PLAYING", "WON", "LOST"
# The scenes: short moments where the game is frozen and something is shown.
#   WARNING_SCENE  the teacher comes over and points at you (after a warning)
#   CAUGHT_SCENE   a Metal Gear "!", then the teacher tears up your exam
#   GAME_OVER_SCENE  after losing, before the end menu (render.py: two logos talk)
WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE = "WARNING_SCENE", "CAUGHT_SCENE", "GAME_OVER_SCENE"
LETTERS = "ABCD"   # the choices of every question
UNKNOWN = "?"      # what the neighbour who does not know the answer shows

# Staring this long (from an empty bar) gives a warning.
WARNING_TIME = STARE_GRACE_TIME + STARE_FILL_TIME
# The free part of the suspicion bar: staring only gets dangerous past it.
GRACE_PART = STARE_GRACE_TIME / WARNING_TIME
# The bar counts as full from here. Adding up many small dt / time steps can
# end just below 1 because of rounding (e.g. 24 steps of 0.125 / 3.0).
FULL = 1 - 1e-9


class Game:
    def __init__(self, rng=None, exam_time=EXAM_TIME):
        # Tests pass a random.Random with a fixed seed, so the "random"
        # answers are the same every run.
        self.rng = rng or random.Random()
        self.exam_time = exam_time   # seconds; the settings menu can change it
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings", "caught" or "time" once lost
        self.time_left = self.exam_time
        self.warnings = 0

        # The answer key: the right letter of each question, and which
        # neighbour knows it.
        self.right_letters = [self.rng.choice(LETTERS) for _ in range(ANSWERS_NEEDED)]
        self.knowing_side = [self.rng.choice((LEFT, RIGHT)) for _ in range(ANSWERS_NEEDED)]
        self.written = []         # letters written on your paper so far, in order
        self.read_sides = set()   # neighbours whose paper you have read for the current question

        # Seconds you have been looking at each neighbour in this look. It
        # starts at 0 again every time you look somewhere else.
        self.focus_time = {LEFT: 0.0, RIGHT: 0.0}
        self.last_direction = None

        # The suspicion bar, 0 (empty) to 1 (full). Staring at the teacher
        # fills it slowly, being seen copying fills it fast. It never jumps
        # back to empty (that would tell the player the teacher looked away):
        # it drains slowly whenever you are not doing anything suspicious.
        self.suspicion_level = 0.0
        self.seen_copying = False # the bar was raised by being seen copying (drawn red)
        self.was_seen = False     # seen copying last frame? (the alarm plays when it starts)
        self.close_calls = 0      # times you were seen copying and got away (they score points)

        self.popup_text = None    # warning message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears
        # The scene playing (see WARNING_SCENE etc. above), or None, and its
        # seconds left. While one plays, nothing else moves: not the bars,
        # not the clock. main.py also stops the teacher.
        self.scene = None
        self.scene_time = 0.0

    @property
    def answers(self):
        """How many answers are written on your paper."""
        return len(self.written)

    def question(self):
        """Index (0 = question 1) of the question you are working on."""
        return self.answers

    def paper_says(self, side):
        """
        What is written on that neighbour's paper for the current question:
        the letter, or "?" if they do not know it. (Whether you can read it
        yet is paper_clarity(); render.py blurs the picture.) None after the
        last question.
        """
        if self.answers == ANSWERS_NEEDED:
            return None
        q = self.question()
        return self.right_letters[q] if side == self.knowing_side[q] else UNKNOWN

    def paper_shows(self, side):
        """
        What you have read on that neighbour's paper for the current
        question: the letter, "?", or None if you have not read it yet.
        """
        if side not in self.read_sides:
            return None
        return self.paper_says(side)

    def paper_clarity(self, side):
        """How sharp that neighbour's paper is right now: 0 = blurry, 1 = sharp."""
        return min(1.0, self.focus_time[side] / PAPER_FOCUS_TIME)

    def reset_paper_focus(self):
        """Both papers blurry again (a new look, or the camera was lost)."""
        self.focus_time = {LEFT: 0.0, RIGHT: 0.0}

    def can_write(self):
        """True once the current question's answer has been read."""
        return (self.state == PLAYING and not self.in_scene()
                and self.knowing_side[self.question()] in self.read_sides)

    def correct_count(self):
        """How many written answers are right (the grade at the end)."""
        return sum(w == r for w, r in zip(self.written, self.right_letters))

    def write(self, letter, direction):
        """
        The player pressed a letter key. It is written only while looking
        down at your paper, and only after the answer has been read.
        Returns a list of events, like update().
        """
        events = []
        if direction != DOWN or not self.can_write():
            return events
        self.written.append(letter)
        events.append("write")
        # On to the next question: nothing read yet.
        self.read_sides = set()
        self.reset_paper_focus()
        if self.answers == ANSWERS_NEEDED:
            self.state = WON
            events.append("won")
        return events

    def score_parts(self):
        """
        The score of a handed-in exam, as (name, points) pairs for the end
        screen. A lost exam has none (it was torn up, or not finished).
        """
        if self.state != WON:
            return []
        time_share = self.time_left / self.exam_time   # 1 = no time used
        return [
            ("CORRECT", self.correct_count() * SCORE_PER_CORRECT),
            ("TIME", int(SCORE_TIME_BONUS * time_share)),
            ("CLOSE CALLS", self.close_calls * SCORE_PER_CLOSE_CALL),
            ("WARNINGS", -self.warnings * SCORE_PER_WARNING),
        ]

    def score(self):
        """The total score: 0 if lost, never below 0."""
        return max(0, sum(points for _, points in self.score_parts()))

    def suspicion(self):
        """How full the suspicion bar is, 0..1."""
        return self.suspicion_level

    def in_scene(self):
        """True while a scene plays and the game is frozen."""
        return self.scene_time > 0

    def start_scene(self, name, seconds):
        self.scene = name
        self.scene_time = seconds

    def skip_scene(self):
        """
        The player pressed Space: end the scene on the next update(). Only
        after losing; a warning scene in the middle of the game can't be skipped.
        """
        if self.state == LOST and self.in_scene():
            self.scene_time = 1e-9   # update() finishes it and starts the next one

    def start_game_over(self, events):
        self.start_scene(GAME_OVER_SCENE, GAME_OVER_TIME)
        events.append("nooo")

    def warn(self, events):
        """
        Staring filled the bar: one more warning, and the bar starts over.
        The teacher comes over to your desk (the warning scene); the last
        warning also ends the game, but the scene still plays first.
        """
        self.warnings += 1
        events.append("warning")
        self.popup_text = (f"The teacher noticed you staring! "
                           f"Warning {self.warnings}/{MAX_WARNINGS}")
        self.popup_timer = POPUP_TIME
        self.start_scene(WARNING_SCENE, WARNING_SCENE_TIME)
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
        # Then a scene: the caught scene, or straight to game over. After
        # the last warning the warning scene is already playing; the game over
        # scene follows it (see update()).
        if reason == "caught":
            self.start_scene(CAUGHT_SCENE, CAUGHT_SCENE_TIME)
        elif not self.in_scene():
            self.start_game_over(events)

    def update(self, direction, dt, teacher=None):
        """
        Move the game forward by dt seconds. `direction` is DOWN, SCREEN, LEFT
        or RIGHT. `teacher` is a Teacher, or None for the demo without one.
        Returns a list of events, e.g. ["read", "warning"].
        """
        events = []
        # A scene: only its own clock runs. It is checked before game over,
        # so the scenes after losing still play out.
        if self.scene_time > 0:
            before = self.scene_time
            self.scene_time = max(0.0, self.scene_time - dt)
            # The moment the teacher tears up your exam: a ripping sound.
            rip_at = CAUGHT_SCENE_TIME - CAUGHT_EXCLAIM_TIME   # seconds left at that moment
            if self.scene == CAUGHT_SCENE and before > rip_at >= self.scene_time:
                events.append("rip")
            if self.scene_time == 0:
                self.popup_text = None   # the scene showed the message already
                # Lost, and the warning or caught scene is over: game over.
                if self.state == LOST and self.scene != GAME_OVER_SCENE:
                    self.start_game_over(events)
                else:
                    self.scene = None
            return events
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
        if self.was_seen and not seen:
            # The teacher saw you copying, and you got away: a close call.
            self.close_calls += 1
            events.append("close_call")
            self.popup_text = f"CLOSE CALL! +{SCORE_PER_CLOSE_CALL}"
            self.popup_timer = POPUP_TIME
        self.was_seen = seen

        # --- Option 3: copying from a neighbour ---
        # Every look is new: turning anywhere else makes both papers blurry
        # again. While the teacher sees you, the paper does not get sharper:
        # glancing sideways then is all risk and no gain.
        if direction != self.last_direction:
            self.reset_paper_focus()
        self.last_direction = direction
        if direction in (LEFT, RIGHT) and not seen:
            self.focus_time[direction] = min(PAPER_FOCUS_TIME, self.focus_time[direction] + dt)
            # Sharp: you have read it (only counted once per question).
            if self.focus_time[direction] >= PAPER_FOCUS_TIME and direction not in self.read_sides:
                self.read_sides.add(direction)
                events.append("read")

        # --- The exam clock ---
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left == 0 and self.state == PLAYING:
            self.lose("time", events)

        return events
