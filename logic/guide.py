"""
The guide on the "How to play" screen: Gemini and Claude teach the game
step by step, and the player tries each thing with their head.

The guide is a list of steps (GUIDE_STEPS). Each step is a few chat lines,
typed out one after the other, and maybe a task the player must do before
the next step starts:
    ("look", DOWN)    look that way and hold it for GUIDE_HOLD_TIME
    ("read", LEFT)    keep looking at that neighbour until the paper is sharp
                      (PAPER_FOCUS_TIME, like in the game)
    ("write", None)   look down and press any of A-D or S
    ("write", "B")    look down and write that letter
The task only counts once all the lines of its step are typed, so the
player has read what to do first. Space (skip()) hurries everything along.

Like game.py, this file draws nothing and does not import pygame, so it can
be tested without a camera or a window (see tests/test_guide.py).
"""

from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (PAPER_FOCUS_TIME, GUIDE_TYPE_SPEED, GUIDE_LINE_PAUSE, GUIDE_STEP_PAUSE,
                      GUIDE_HOLD_TIME, GUIDE_BLIP_LETTERS)

GEMINI, CLAUDE = "GEMINI", "CLAUDE"   # who talks (the same names as ui/draw_scenes.py)
LETTERS = ("A", "B", "C", "D", "S")   # the keys that write on the paper (S = blank)
BLANK_MARK = "-"                      # what S writes on the paper

# What each neighbour's paper shows in the guide: the right one does not
# know ("?"), the left one does. (The real game picks at random.)
GUIDE_PAPERS = {RIGHT: "unknown", LEFT: "B"}

# The steps. "teacher": what the classroom shows when the player looks at the
# screen ("busy" or "watching"; busy if not given). "sound": played when the
# step starts. Keep a line under ~75 letters (two lines in the bubble).
GUIDE_STEPS = [
    {"lines": [(GEMINI, "Hi, I'm Gemini. I drew this game. Claude coded it. You... play it."),
               (CLAUDE, "Lesson one of cheating: use your head. Literally. Hands off.")]},
    {"lines": [(CLAUDE, "Tilt your head DOWN. Your paper. The only safe place in this room.")],
     "task": ("look", DOWN)},
    {"lines": [(GEMINI, "A-D writes an answer, S leaves it blank. Go on, pretend you studied.")],
     "task": ("write", None)},
    {"lines": [(CLAUDE, "Right +1, wrong -0.5. So guessing loses points. It's called math."),
               (GEMINI, "Copying doesn't. Turn RIGHT and stare at his paper till it's sharp.")],
     "task": ("read", RIGHT)},
    {"lines": [(GEMINI, "A question mark. He knows as much as you. Truly inspiring."),
               (CLAUDE, "One of them always knows. Turn LEFT. Slowly. It takes a second.")],
     "task": ("read", LEFT)},
    {"lines": [(CLAUDE, "B! Look away and it blurs. Quick, before you forget: look DOWN, write B.")],
     "task": ("write", "B")},
    {"lines": [(GEMINI, "Now look at the SCREEN. The only place you can see the teacher.")],
     "task": ("look", SCREEN)},
    {"lines": [(CLAUDE, "At the board = busy = copy freely. Tip: NOW, not \"in a sec\".")]},
    {"teacher": "watching", "sound": "state:TURNING",
     "lines": [(GEMINI, "Hear that \"hmm\"? He's turning around. Eyes on your paper. NOW."),
               (CLAUDE, "Seen copying = exam torn up, zero. Escape just in time = bonus."),
               (GEMINI, "Tip: looking down you hear nothing. Glance up. Paranoia pays.")]},
    {"teacher": "watching",
     "lines": [(CLAUDE, "Staring at him fills the suspicion bar. Full = a yelling. 3 = you're out."),
               (GEMINI, "Looking down drains it. Too high and he watches you. Forever."),
               (CLAUDE, "How high is too high? Random. I forgot where I put it. Have fun.")]},
    {"lines": [(GEMINI, "Hand in early: bigger bonus. No warnings at all: NINJA bonus."),
               (CLAUDE, "The right paper on the first try: SHARP EYE. Grades are curved. Suffer.")]},
    {"lines": [(GEMINI, "A run: Quiz, Midterm, Final. A slot machine picks his mood. Gamble!"),
               (CLAUDE, "Pick a character too. Each bends a rule, for a price. Like tuition."),
               (GEMINI, "Now a practice exam. Counts for nothing. Just like your attendance."),
               (CLAUDE, "DON'T. GET. CAUGHT.")]},
]


class Guide:
    """Where the guide is: the step, the line being typed, the task."""

    def __init__(self, steps=GUIDE_STEPS):
        self.steps = steps
        self.step = 0
        self.line = 0            # the line of this step being typed (or the last one)
        self.line_time = 0.0     # seconds since that line started
        self.hold_time = 0.0     # seconds the task's direction has been held
        self.task_done = False
        self.done_time = 0.0     # seconds since the task was done
        self.said = [self.current_line()]   # every line started so far, in order
        self.written = []        # letters on the player's paper
        # Seconds the player has been looking at each neighbour without a break.
        self.look_times = {LEFT: 0.0, RIGHT: 0.0}

    # --- What the screen shows -------------------------------------------
    def current_line(self):
        return self.steps[self.step]["lines"][self.line]

    def letters(self):
        """How many letters of the current line are typed."""
        return min(len(self.current_line()[1]), int(self.line_time * GUIDE_TYPE_SPEED))

    def typed(self):
        """True when the current line is fully typed."""
        return self.letters() >= len(self.current_line()[1])

    def task(self):
        """The current step's task, or None (also when the guide is finished)."""
        if self.finished():
            return None
        return self.steps[self.step].get("task")

    def waiting(self):
        """True while the player must do the task (all lines typed, task not done)."""
        return self.task() is not None and self.last_line() and self.typed() and not self.task_done

    def last_line(self):
        return self.line == len(self.steps[self.step]["lines"]) - 1

    def teacher(self):
        """What the teacher is doing in this step: "busy" or "watching"."""
        if self.finished():
            return "busy"
        return self.steps[self.step].get("teacher", "busy")

    def clarity(self, side):
        """0 = the neighbour's paper is very blurry, 1 = sharp (read)."""
        return min(1.0, self.look_times[side] / PAPER_FOCUS_TIME)

    def progress(self):
        """0..1, how far the current task is (for a bar on the screen)."""
        kind, what = self.task() or (None, None)
        if kind == "look":
            return min(1.0, self.hold_time / GUIDE_HOLD_TIME)
        if kind == "read":
            return self.clarity(what)
        return 0.0

    def finished(self):
        """True when the last step is over."""
        return self.step >= len(self.steps)

    # --- Moving on -------------------------------------------------------
    def update(self, dt, direction):
        """
        Move on by dt seconds; `direction` is where the player looks.
        Returns events for the sounds: "talk:GEMINI" / "talk:CLAUDE" every
        GUIDE_BLIP_LETTERS letters typed, "read" when a task is done, and a
        step's own "sound" when it starts.
        """
        if self.finished():
            return []
        for side in self.look_times:
            self.look_times[side] = self.look_times[side] + dt if direction == side else 0.0

        before = self.letters()
        self.line_time += dt
        events = self.talk_events(before, self.letters())

        if self.waiting():
            events += self.check_task(dt, direction)
        elif self.typed():
            # A short pause to read the line (or to enjoy the task's "ding").
            if self.task_done:
                self.done_time += dt
                waited, pause = self.done_time, GUIDE_STEP_PAUSE
            else:
                waited, pause = self.line_time - self.typing_time(), GUIDE_LINE_PAUSE
            if waited >= pause:
                events += self.next_line()
        return events

    def typing_time(self):
        """Seconds the current line takes to type."""
        return len(self.current_line()[1]) / GUIDE_TYPE_SPEED

    def talk_events(self, before, now):
        """A talking blip when the typing passes a multiple of GUIDE_BLIP_LETTERS (not on a space)."""
        who, text = self.current_line()
        if now // GUIDE_BLIP_LETTERS > before // GUIDE_BLIP_LETTERS and text[now - 1] != " ":
            return [f"talk:{who}"]
        return []

    def check_task(self, dt, direction):
        """The "look" and "read" tasks are done by holding the head; "write" by press()."""
        kind, what = self.task()
        if kind == "look":
            self.hold_time = self.hold_time + dt if direction == what else 0.0
            if self.hold_time >= GUIDE_HOLD_TIME:
                return self.complete_task()
        elif kind == "read" and self.clarity(what) >= 1:
            return self.complete_task()
        return []

    def complete_task(self):
        self.task_done = True
        self.done_time = 0.0
        return ["read"]   # the "ding" of reading a paper

    def press(self, letter, direction):
        """The player pressed A-D or S. Returns events, like update()."""
        if not self.waiting() or self.task()[0] != "write":
            return []
        if direction != DOWN:
            return ["menu_back"]   # you can only write while looking at your paper
        wanted = self.task()[1]
        if wanted is not None and letter != wanted:
            return ["menu_back"]   # not the letter the neighbour showed
        self.written.append(BLANK_MARK if letter == "S" else letter)
        return self.complete_task()

    def next_line(self):
        """The next line of this step, or the next step. Returns events."""
        if not self.last_line():
            self.line += 1
        else:
            self.step += 1
            self.line = 0
            self.hold_time = 0.0
            self.task_done = False
            if self.finished():
                return []
        self.line_time = 0.0
        self.said.append(self.current_line())
        sound = self.steps[self.step].get("sound")
        return [sound] if sound and self.line == 0 else []

    def skip(self):
        """
        Space: finish typing the line; if it is typed, do the task for the
        player (a letter it would write), or go on to the next line.
        Returns events, like update().
        """
        if self.finished():
            return []
        if not self.typed():
            self.line_time = self.typing_time()
            return []
        if self.waiting():
            kind, what = self.task()
            if kind == "write":
                self.written.append(what or "A")
            return self.complete_task() + self.next_line()
        return self.next_line()
