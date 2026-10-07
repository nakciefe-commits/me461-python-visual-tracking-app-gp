"""
Game rules for one exam: the clock, warnings, getting caught, the scenes,
handing the exam in, losing and the score.

The parts have their own files; this one puts them together:
    exam_paper.py   the answer key, what you wrote, the grade
    neighbours.py   reading a neighbour's paper (it gets sharper as you look)
    suspicion.py    the suspicion bar (staring and being seen copying)

How an answer gets onto your paper:
    1. Look at a neighbour long enough to read their paper (or don't).
    2. Look down at your own paper and press A-D to write a letter, or S to
       leave the question blank. A letter you never read is a guess: right
       +1, wrong -0.5, blank 0 (see exam_paper.py).
    3. All questions answered = handed in (WON, graded). When the clock runs
       out the teacher collects the paper: the rest are blank, also graded.
    Losing (0 points) is only getting caught or too many warnings.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "read" or "warning") so main.py knows which sounds to play.
That keeps the rules testable without a camera or a window (tests/test_game.py).
"""

import random

from logic.exam_paper import ExamPaper, BLANK, POINTS, CORRECT
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from logic.neighbours import NeighbourPapers
from logic.suspicion import SuspicionBar, close_call_points
from settings import (MAX_WARNINGS, POPUP_TIME, EXAM_TIME, ANSWERS_NEEDED, WARNING_SCENE_TIME,
                      CAUGHT_SCENE_TIME, CAUGHT_EXCLAIM_TIME, GAME_OVER_TIME,
                      STARE_ONLY_WHEN_FACING, SCORE_PER_POINT, SCORE_TIME_BONUS,
                      CLOSE_CALL_EDGE, SCORE_PER_WARNING, SUSPICIOUS_AT, SCORE_NINJA,
                      SCORE_ALMOST_NINJA, SCORE_SHARP_EYE)

# WON = the exam was handed in (or collected when time ran out) and is graded.
PLAYING, WON, LOST = "PLAYING", "WON", "LOST"
# The scenes: short moments where the game is frozen and something is shown.
#   WARNING_SCENE  the teacher comes over and points at you (after a warning)
#   CAUGHT_SCENE   a Metal Gear "!", then the teacher tears up your exam
#   GAME_OVER_SCENE  after losing, before the end menu (render: two logos talk)
WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE = "WARNING_SCENE", "CAUGHT_SCENE", "GAME_OVER_SCENE"


class Game:
    def __init__(self, rng=None, exam_time=EXAM_TIME, questions=ANSWERS_NEEDED,
                 suspicious_at=SUSPICIOUS_AT):
        # Tests pass a random.Random with a fixed seed, so the "random"
        # answers are the same every run.
        self.rng = rng or random.Random()
        self.exam_time = exam_time   # seconds (each quiz of the run has its own, see run.py)
        self.questions = questions   # how many questions this exam has
        self.suspicious_at = suspicious_at   # the hidden point on the suspicion bar, see under_suspicion()
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings" or "caught" once lost
        self.time_ran_out = False # handed in because the clock ran out (not by you)
        self.time_left = self.exam_time
        self.warnings = 0
        self.sharp_eyes = 0       # questions where the first paper you read was the one that knows
        self.paper = ExamPaper(self.rng, self.questions)
        self.neighbours = NeighbourPapers()
        self.suspicion = SuspicionBar()
        self.popup_text = None    # message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears
        # The scene playing (WARNING_SCENE etc.), or None, and its seconds
        # left. While one plays, nothing else moves: not the bar, not the
        # clock. main.py also stops the teacher.
        self.scene = None
        self.scene_time = 0.0

    # ------------------------------------------------------------------
    # Your paper
    # ------------------------------------------------------------------
    def paper_shows(self, side):
        """
        What you have read on that neighbour's paper for the current
        question: the letter, "?", or None if you have not read it yet.
        """
        if not self.neighbours.has_read(side):
            return None
        return self.paper.says(side)

    def knows_answer(self):
        """True once the neighbour who knows the current answer has been read."""
        if self.paper.is_full():
            return False
        return self.neighbours.has_read(self.paper.knowing_side[self.paper.question()])

    def under_suspicion(self):
        """
        True while the suspicion bar is above this exam's hidden point: the
        teacher keeps watching you (main.py tells teacher.update()) until it
        drains back under it, so you have to look at your paper.
        """
        return self.suspicion.level >= self.suspicious_at

    def can_write(self):
        return self.state == PLAYING and not self.in_scene()

    def write(self, answer, direction):
        """
        The player pressed A-D (or S: answer = BLANK). It is written only
        while looking down at your paper; read or not, any letter goes.
        Returns a list of events, like update().
        """
        if direction != DOWN or not self.can_write():
            return []
        self.paper.write(answer)
        self.neighbours.new_question()   # on to the next question: nothing read yet
        events = ["write"]
        if self.paper.is_full():
            self.state = WON
            events.append("won")
        return events

    def leave_blank(self, direction):
        """The player pressed S: leave the current question empty (0 points)."""
        return self.write(BLANK, direction)

    # ------------------------------------------------------------------
    # Score
    # ------------------------------------------------------------------
    def score_parts(self):
        """
        The score of a handed-in exam, as (name, points) pairs: one per
        question (the end screen counts them up one by one, see tally.py),
        then the bonuses. A lost exam has none (it was torn up).
        """
        if self.state != WON:
            return []
        questions = [(f"Q{i + 1}", int(POINTS[result] * SCORE_PER_POINT))
                     for i, result in enumerate(self.paper.results())]
        # Handing in early pays: the bonus is the share of the time left
        # (0 when the clock ran out and the paper was collected).
        time_share = self.time_left / self.exam_time
        bonuses = [
            ("EARLY BONUS", int(SCORE_TIME_BONUS * time_share)),
            ("SHARP EYES", self.sharp_eyes * SCORE_SHARP_EYE),
            ("CLOSE CALLS", self.suspicion.close_call_score),
            ("WARNINGS", -self.warnings * SCORE_PER_WARNING),
            ("NINJA!" if self.warnings == 0 else "ALMOST NINJA", self.ninja_bonus()),
        ]
        # Only the bonuses you got: the count does not show a row of zeros.
        return questions + [(name, points) for name, points in bonuses if points]

    def ninja_bonus(self):
        """Every answer right: a big bonus with no warning, a smaller one with one."""
        if self.paper.count(CORRECT) != self.paper.size():
            return 0
        return {0: SCORE_NINJA, 1: SCORE_ALMOST_NINJA}.get(self.warnings, 0)

    def score(self):
        """The total score: 0 if lost, never below 0."""
        return max(0, sum(points for _, points in self.score_parts()))

    # ------------------------------------------------------------------
    # Scenes, warnings, losing
    # ------------------------------------------------------------------
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

    def update_scene(self, dt):
        """Only the scene's own clock runs. Returns events, like update()."""
        events = []
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

    def start_game_over(self, events):
        self.start_scene(GAME_OVER_SCENE, GAME_OVER_TIME)
        events.append("nooo")

    def show_popup(self, text):
        self.popup_text = text
        self.popup_timer = POPUP_TIME

    def warn(self, events):
        """
        Staring filled the bar: one more warning, and the bar starts over.
        The teacher comes over to your desk (the warning scene); the last
        warning also ends the game, but the scene still plays first.
        """
        self.warnings += 1
        events.append("warning")
        self.show_popup(f"The teacher noticed you staring! Warning {self.warnings}/{MAX_WARNINGS}")
        self.start_scene(WARNING_SCENE, WARNING_SCENE_TIME)
        self.suspicion.start_over()
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
        # scene follows it (see update_scene()).
        if reason == "caught":
            self.start_scene(CAUGHT_SCENE, CAUGHT_SCENE_TIME)
        elif not self.in_scene():
            self.start_game_over(events)

    # ------------------------------------------------------------------
    # Every frame
    # ------------------------------------------------------------------
    def update(self, direction, dt, teacher=None):
        """
        Move the game forward by dt seconds. `direction` is DOWN, SCREEN, LEFT
        or RIGHT. `teacher` is a Teacher, or None for the demo without one.
        Returns a list of events, e.g. ["read", "warning"].
        """
        # A scene is checked before game over, so the scenes after losing
        # still play out.
        if self.in_scene():
            return self.update_scene(dt)
        if self.state != PLAYING:
            return []
        events = []

        self.popup_timer -= dt
        if self.popup_timer <= 0:
            self.popup_text = None

        # The suspicion bar. Seen = looking sideways while the teacher
        # watches; staring = looking at the teacher while they look at the class.
        seen = direction in (LEFT, RIGHT) and teacher is not None and teacher.is_watching()
        teacher_sees = (teacher is None or not STARE_ONLY_WHEN_FACING
                        or teacher.is_facing_class())
        staring = direction == SCREEN and teacher_sees
        events += self.suspicion.update(seen, staring, dt)
        if "close_call" in events:
            points = self.suspicion.last_close_call
            name = "RAZOR CLOSE!" if points >= close_call_points(CLOSE_CALL_EDGE) else "CLOSE CALL!"
            self.show_popup(f"{name} +{points}")
        if self.suspicion.is_full():
            if seen:
                events.append("caught")
                self.lose("caught", events)
                return events
            self.warn(events)

        # Reading a neighbour's paper. While the teacher sees you it does not
        # get sharper: glancing sideways then is all risk and no gain.
        read = self.neighbours.update(direction, dt, can_focus=not seen)
        if read and self.neighbours.read_sides == {self.paper.knowing_side[self.paper.question()]}:
            # The first paper you read for this question was the right one.
            self.sharp_eyes += 1
            self.show_popup(f"SHARP EYE! +{SCORE_SHARP_EYE}")
            read.append("sharp_eye")
        events += read

        # The exam clock.
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left == 0 and self.state == PLAYING:   # not after the last warning
            self.collect_paper(events)
        return events

    def collect_paper(self, events):
        """Time is up: the teacher takes your paper. Unanswered questions count as blank."""
        while not self.paper.is_full():
            self.paper.write(BLANK)
        self.state = WON
        self.time_ran_out = True
        events.append("time_up")
