"""
The grade roast: after the final, Gemini and Claude comment on your
semester grade (the letter on the curve, see grade.py), two or three
sarcastic chat lines typed out over the results screen.

Each letter has a few conversations (VERDICTS); main.py picks one with a
Bag (logic/bag.py), so the same joke does not come back too soon. It can
be turned off in the settings ("GRADE ROAST").

Verdict is where the roast is: which line is being typed, how far. The
lines come one after the other (VERDICT_LINE_PAUSE between them); when all
are typed it stays VERDICT_HOLD seconds, then it is finished. Space (or the
head) calls skip(): first it types everything at once, then it closes.

A good grade gets a show first (VERDICT_HYPE: BB 1, BA 2, AA 3): the
letter alone, big, for VERDICT_REVEAL seconds, with effects that grow with
the hype (ui/draw_scenes.py draws them). For an AA there are fireworks;
firework_times() says when, so the sounds and the pictures agree.

Like game.py, this file draws nothing and does not import pygame, so it can
be tested without a camera or a window (see tests/test_verdict.py).
"""

from settings import (VERDICT_TYPE_SPEED, VERDICT_LINE_PAUSE, VERDICT_HOLD, GUIDE_BLIP_LETTERS,
                      VERDICT_HYPE, VERDICT_REVEAL, VERDICT_FIREWORK_EVERY)

GEMINI, CLAUDE = "GEMINI", "CLAUDE"   # who talks (the same names as ui/draw_scenes.py)
HAPPY_LETTERS = ("AA", "BA")          # for these they smile at the end; for the rest they laugh
# The sounds when the show starts, per hype (the AA's fireworks come on top).
HYPE_SOUNDS = {1: ["tally_done"], 2: ["new_top"], 3: ["boom", "new_top"]}

# Letter -> conversations, each a list of (who, text). Keep a line under
# ~75 letters (two lines in the bubble) and at most three lines.
VERDICTS = {
    "AA": [
        [(GEMINI, "Wait. AA? Like, the actual top grade?"),
         (CLAUDE, "I checked my code twice. No bug. You are... \"the one\" :O"),
         (GEMINI, "Neo copied from his neighbours too. Probably.")],
        [(CLAUDE, "AA. The curve is crying. The class average is crying."),
         (GEMINI, "Your neighbours did all the work, but sure. Take a bow.")],
    ],
    "BA": [
        [(GEMINI, "BA. So close to greatness. Touching distance."),
         (CLAUDE, "Greatness looked at you and said \"nah\".")],
        [(CLAUDE, "BA! Wow, you actually have talent."),
         (GEMINI, "For cheating. Put that on your CV.")],
    ],
    "BB": [
        [(GEMINI, "BB. Solid. Respectable. Like a beige sofa."),
         (CLAUDE, "Your parents will say \"good\" and change the topic.")],
        [(CLAUDE, "BB. Honestly? Decent copying."),
         (GEMINI, "Your neighbour should get half of that grade.")],
    ],
    "CB": [
        [(GEMINI, "CB. Hey, wow, you have some potential!"),
         (CLAUDE, "\"Potential.\" What teachers say when they've got nothing else.")],
        [(CLAUDE, "CB. Above average! Barely. Squint and you'll see it."),
         (GEMINI, "Microscopes were invented for grades like this.")],
    ],
    "CC": [
        [(GEMINI, "CC. Wow, I thought you were special."),
         (CLAUDE, "NAAHHH. Average. Always was.")],
        [(CLAUDE, "CC. Exactly the class average. Statistically, you're nobody."),
         (GEMINI, "The most average human ever measured. Congrats?")],
    ],
    "DC": [
        [(GEMINI, "DC. Like the comics. Except nobody wants a sequel."),
         (CLAUDE, "Passed. Technically. The best kind of passed.")],
        [(CLAUDE, "DC. A pass is a pass, right?"),
         (GEMINI, "Your diploma will have a tiny little asterisk.")],
    ],
    "DD": [
        [(GEMINI, "DD. The lowest pass. You limbo'd under the bar."),
         (CLAUDE, "And the bar was lying on the floor.")],
        [(CLAUDE, "DD. You passed by exactly one pixel."),
         (GEMINI, "I drew that pixel. You're welcome.")],
    ],
    "FD": [
        [(GEMINI, "FD. Not even an FF. You failed... with style?"),
         (CLAUDE, "See you next semester. Same seat, same neighbour.")],
        [(CLAUDE, "FD. So close to passing that it hurts. Mostly us."),
         (GEMINI, "7th-year legend: unlocked. Spiritually.")],
    ],
    "FF": [
        [(GEMINI, "FF. Like in online games: forfeit."),
         (CLAUDE, "Your neighbours studied. You just... looked at them.")],
        [(CLAUDE, "FF. The F stands for \"fantastic\". The other F too."),
         (GEMINI, "Oh no, sorry, I misread. It stands for FAILED.")],
        [(GEMINI, "FF. Zero copying skills. Zero studying skills."),
         (CLAUDE, "But 100% attendance at this exam. Respect.")],
    ],
}


class Verdict:
    """One roast being typed: the lines, and how long it has been going."""

    def __init__(self, letter, lines):
        self.letter = letter
        self.lines = lines
        self.time = 0.0
        self.closed = False   # True once skipped after everything was typed
        self.hype = VERDICT_HYPE.get(letter, 0)   # how big the show is (0 = none)
        self.reveal = VERDICT_REVEAL.get(self.hype, 0.0)   # seconds of the big letter alone
        # When each line starts: after the show, then after the one before is typed, and a pause.
        self.starts = []
        start = self.reveal
        for who, text in lines:
            self.starts.append(start)
            start += len(text) / VERDICT_TYPE_SPEED + VERDICT_LINE_PAUSE
        last_start = self.starts[-1]
        self.typed_at = last_start + len(lines[-1][1]) / VERDICT_TYPE_SPEED   # all typed

    def letters(self):
        """For each line, how many of its letters are typed (0 = not started)."""
        return [max(0, min(len(text), int((self.time - start) * VERDICT_TYPE_SPEED)))
                for (who, text), start in zip(self.lines, self.starts)]

    def all_typed(self):
        return self.time >= self.typed_at

    def laughing(self):
        """True when it is all said: they laugh at you (or smile, for a great grade)."""
        return self.all_typed() and self.letter not in HAPPY_LETTERS

    def firework_times(self):
        """When the AA's fireworks go off (seconds): often during the show, half as often after."""
        if self.hype < 3:
            return []
        times, t = [], VERDICT_FIREWORK_EVERY / 2
        end = self.typed_at + VERDICT_HOLD
        while t < end:
            times.append(t)
            t += VERDICT_FIREWORK_EVERY * (1 if t < self.reveal else 2)
        return times

    def finished(self):
        """True when it is over: held long enough, or skipped."""
        return self.closed or self.time >= self.typed_at + VERDICT_HOLD

    def update(self, dt):
        """
        Move on by dt seconds. Returns the sounds: the show's (HYPE_SOUNDS)
        at the start, a "firework" for each of the AA's fireworks during the
        show (after it they would drown the talking), and "talk:GEMINI" /
        "talk:CLAUDE" blips while typing.
        """
        before, was_time = self.letters(), self.time
        self.time += dt
        events = list(HYPE_SOUNDS.get(self.hype, [])) if was_time == 0 else []
        events += ["firework" for t in self.firework_times() if was_time < t <= self.time and t < self.reveal]
        for (who, text), was, now in zip(self.lines, before, self.letters()):
            # A blip every GUIDE_BLIP_LETTERS letters typed (like the guide), not on a space.
            if now // GUIDE_BLIP_LETTERS > was // GUIDE_BLIP_LETTERS and text[now - 1] != " ":
                events.append(f"talk:{who}")
        return events

    def skip(self):
        """Space or the head: type everything at once, or close if it is all typed."""
        if self.all_typed():
            self.closed = True
        else:
            self.time = self.typed_at
