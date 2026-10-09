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

The player's character (logic/character.py) bends a few of these rules:
the speeds of the suspicion bar and of reading, a joker that writes the
right answer (use_joker()), a deadline for handing in, a sugar rush or a
sleepy crash. Without one, the plain rules apply.

This file only does the rules; it draws nothing and plays nothing. Every frame
main.py calls update() with the head direction, and update() returns a list
of "events" (like "read" or "warning") so main.py knows which sounds to play.
That keeps the rules testable without a camera or a window (tests/test_game.py).
"""

import random

from logic.exam_paper import ExamPaper, BLANK, POINTS, CORRECT, UNKNOWN
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from logic.neighbours import NeighbourPapers
from logic.suspicion import SuspicionBar, close_call_points
from logic.character import rules as character_rules, Energy, RUSH
from settings import (MAX_WARNINGS, POPUP_TIME, EXAM_TIME, ANSWERS_NEEDED, WARNING_SCENE_TIME,
                      CAUGHT_SCENE_TIME, CAUGHT_EXCLAIM_TIME, GAME_OVER_TIME,
                      MUGSHOT_SCENE_TIME, MUGSHOT_WRITE_DELAY,
                      STARE_ONLY_WHEN_FACING, SCORE_PER_POINT, SCORE_TIME_BONUS,
                      CLOSE_CALL_EDGE, SCORE_PER_WARNING, SUSPICIOUS_AT, SCORE_NINJA,
                      SCORE_ALMOST_NINJA, SCORE_SHARP_EYE, DEFAULT_CHARACTER)

# WON = the exam was handed in (or collected when time ran out) and is graded.
PLAYING, WON, LOST = "PLAYING", "WON", "LOST"
# The scenes: short moments where the game is frozen and something is shown.
#   WARNING_SCENE  the teacher comes over and points at you (after a warning)
#   CAUGHT_SCENE   a Metal Gear "!", then the teacher tears up your exam
#   MUGSHOT_SCENE  after losing: your taped-up exam with your webcam photo
#                  clipped on, and the teacher writes "GOT CAUGHT!" on it
#   GAME_OVER_SCENE  after losing, before the end menu (render: two logos talk)
WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE = "WARNING_SCENE", "CAUGHT_SCENE", "GAME_OVER_SCENE"
MUGSHOT_SCENE = "MUGSHOT_SCENE"


class Game:
    def __init__(self, rng=None, exam_time=EXAM_TIME, questions=ANSWERS_NEEDED,
                 suspicious_at=SUSPICIOUS_AT, character=DEFAULT_CHARACTER, rushes_before=0,
                 ease=1.0):
        # Tests pass a random.Random with a fixed seed, so the "random"
        # answers are the same every run.
        self.rng = rng or random.Random()
        self.exam_time = exam_time   # seconds (each quiz of the run has its own, see run.py)
        self.questions = questions   # how many questions this exam has
        self.suspicious_at = suspicious_at   # the hidden point on the suspicion bar, see under_suspicion()
        self.character = character   # who the player is (a key of CHARACTERS)
        self.rules = character_rules(character)
        self.rushes_before = rushes_before   # the energy drink addict's sugar rushes earlier in the run
        # The practice exam is easier: every danger at `ease` of its strength
        # (the bar fills slower, you read faster; main.py shortens his looks).
        self.ease = ease
        self.reset()

    def reset(self):
        """Put everything back to the start of a new game."""
        self.state = PLAYING
        self.lose_reason = None   # "warnings" or "caught" once lost
        self.time_ran_out = False # handed in because the clock ran out (not by you)
        self.time_left = self.exam_time
        self.warnings = 0
        self.sharp_eyes = 0       # questions where the first paper you read was the one that knows
        self.paper = ExamPaper(self.rng, self.questions, both_know=self.rules["both_know"])
        self.neighbours = NeighbourPapers()
        self.suspicion = SuspicionBar(self.rules["seen_speed"] * self.ease, self.rules["stare_speed"] * self.ease,
                                      self.rules["creep_time"])
        self.popup_text = None    # message on screen, or None
        self.popup_timer = 0.0    # seconds until the popup disappears
        self.jokers = self.rules["jokers"]   # the nerd's jokers left in this exam
        self.missed_deadline = False         # the nerd: the time to hand in early has passed
        # The energy drink addict: today's sugar rush or crash, else None.
        self.energy = Energy(self.rng, self.rules, self.rushes_before) if self.rules["energy"] else None
        if self.energy is not None:
            self.show_popup("SUGAR RUSH! The world slows down" if self.energy.day == RUSH
                            else "CRASH... you will get sleepy")
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
        """True once a neighbour who knows the current answer has been read."""
        return any(self.paper_shows(side) not in (None, UNKNOWN) for side in (LEFT, RIGHT))

    def world_speed(self):
        """How fast the world (teacher, clock, suspicion bar) runs: below 1 in a sugar rush."""
        return self.energy.world_speed() if self.energy is not None else 1.0

    def focus_speed(self):
        """How fast you read a neighbour's paper: the character's speed, slower while sleepy."""
        speed = self.rules["focus_speed"] / self.ease
        if self.energy is not None:
            speed *= self.energy.focus_speed()
        return speed

    def is_sleepy(self):
        """True during the energy drink addict's sleepy spell (the eyelids close)."""
        return self.energy is not None and self.energy.is_sleepy()

    def deadline(self):
        """The nerd's deadline: seconds that must be left on the clock at hand-in (0 = none)."""
        return self.rules["hand_in_share"] * self.exam_time

    def use_joker(self, direction):
        """
        The nerd pressed J: if a joker is left, the right answer is written
        (only while looking at your paper, like writing). Returns events.
        """
        if self.jokers <= 0 or direction != DOWN or not self.can_write():
            return []
        self.jokers -= 1
        self.show_popup("JOKER! The nerd knew this one")
        return ["joker"] + self.write(self.paper.right_answer(), direction)

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
        # The nerd's bonus counts from his deadline: 0 with exactly
        # hand_in_share of the time left, the full bonus with all of it left.
        line = self.rules["hand_in_share"]
        time_share = max(0.0, (time_share - line) / (1 - line))
        late = self.deadline() > 0 and self.time_left < self.deadline()
        bonuses = [
            ("EARLY BONUS", int(SCORE_TIME_BONUS * time_share)),
            ("NERD WAS LATE", -self.rules["late_penalty"] if late else 0),
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
        # The moment the teacher starts writing on the mugshot: a pen sound.
        pen_at = MUGSHOT_SCENE_TIME - MUGSHOT_WRITE_DELAY
        if self.scene == MUGSHOT_SCENE and before > pen_at >= self.scene_time:
            events.append("pen")
        if self.scene_time == 0:
            self.popup_text = None   # the scene showed the message already
            # Lost, and the warning or caught scene is over: the mugshot,
            # then game over.
            if self.state == LOST and self.scene in (WARNING_SCENE, CAUGHT_SCENE):
                self.start_mugshot(events)
            elif self.state == LOST and self.scene == MUGSHOT_SCENE:
                self.start_game_over(events)
            else:
                self.scene = None
        return events

    def start_mugshot(self, events):
        # Silent: it fades in on a black screen; only the pen is heard later.
        self.start_scene(MUGSHOT_SCENE, MUGSHOT_SCENE_TIME)

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
        events += ["warning", "footsteps"]   # the buzz, and he walks over to your desk
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
            self.start_mugshot(events)

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

        # In a sugar rush the world (the bar, the clock; main.py slows the
        # teacher too) runs slower, but your eyes do not.
        world_dt = dt * self.world_speed()
        if self.energy is not None:
            for change in self.energy.update(dt):
                events.append(change)
                if change == "sleepy":
                    self.show_popup("ZZZ... SO SLEEPY")

        # The suspicion bar. Seen = looking sideways while the teacher
        # watches; staring = looking at the teacher while they look at the class.
        seen = direction in (LEFT, RIGHT) and teacher is not None and teacher.is_watching()
        teacher_sees = (teacher is None or not STARE_ONLY_WHEN_FACING
                        or teacher.is_facing_class())
        staring = direction == SCREEN and teacher_sees
        events += self.suspicion.update(seen, staring, world_dt, away=direction != DOWN)
        if "close_call" in events:
            points = self.suspicion.last_close_call
            razor = points >= close_call_points(CLOSE_CALL_EDGE)
            self.show_popup(f"{'RAZOR CLOSE!' if razor else 'CLOSE CALL!'} +{points}")
            if razor:
                events.append("heartbeat")   # that was too close: the player's heart pounds
        if self.suspicion.is_full():
            if seen:
                events.append("caught")
                self.lose("caught", events)
                return events
            self.warn(events)

        # Reading a neighbour's paper. While the teacher sees you it does not
        # get sharper: glancing sideways then is all risk and no gain.
        read = self.neighbours.update(direction, dt, can_focus=not seen, speed=self.focus_speed())
        if (read and not self.paper.both_know
                and self.neighbours.read_sides == {self.paper.knowing_side[self.paper.question()]}):
            # The first paper you read for this question was the right one.
            self.sharp_eyes += 1
            self.show_popup(f"SHARP EYE! +{SCORE_SHARP_EYE}")
            read.append("sharp_eye")
        events += read

        # The exam clock.
        self.time_left = max(0.0, self.time_left - world_dt)
        if self.deadline() > 0 and self.time_left < self.deadline() and not self.missed_deadline:
            # The nerd is too slow: say so once, the points go at the end.
            self.missed_deadline = True
            self.show_popup(f"TOO SLOW FOR A NERD! -{self.rules['late_penalty']}")
            events.append("nerd_late")
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
