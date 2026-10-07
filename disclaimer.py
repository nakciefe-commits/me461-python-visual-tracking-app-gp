"""
The disclaimer when the game opens, as an "official notice": a paper on
which the text is typed out, the player signs it (Space), and an
"APPROVED" stamp comes down on it. Then the game goes on by itself.

Like game.py, this file only keeps track of what is happening and when; it
draws nothing and plays nothing. update() returns events ("type", "sign",
"stamp") so main.py knows which sounds to play, and render.py's
draw_disclaimer() draws it. That way it can be tested (tests/test_disclaimer.py).
"""

from settings import NOTICE_TYPE_DELAY, NOTICE_TYPE_SPEED, NOTICE_SIGN_TIME, NOTICE_STAMP_HOLD


class Disclaimer:
    def __init__(self, total_letters):
        self.total_letters = total_letters   # how many letters the whole notice has
        self.time = 0.0                      # seconds since the notice appeared
        self.signed_at = None                # time the player signed, or None
        self.skipped = False                 # Space pressed after the stamp: go on now

    def letters(self):
        """How many letters of the notice are typed so far."""
        typed = int(max(0.0, self.time - NOTICE_TYPE_DELAY) * NOTICE_TYPE_SPEED)
        return min(self.total_letters, typed)

    def typed(self):
        return self.letters() == self.total_letters

    def stamp_time(self):
        """When the stamp comes down (the signature is done), or None before signing."""
        if self.signed_at is None:
            return None
        return self.signed_at + NOTICE_SIGN_TIME

    def sign_progress(self):
        """How much of the signature is written, 0..1."""
        if self.signed_at is None:
            return 0.0
        return min(1.0, (self.time - self.signed_at) / NOTICE_SIGN_TIME)

    def stamp_age(self):
        """Seconds since the stamp came down, or None if it has not yet."""
        stamp = self.stamp_time()
        if stamp is None or self.time < stamp:
            return None
        return self.time - stamp

    def done(self):
        """True when the game should go on to the next screen."""
        age = self.stamp_age()
        return self.skipped or (age is not None and age >= NOTICE_STAMP_HOLD)

    def update(self, dt):
        """Move on by dt seconds. Returns events for the sounds."""
        events = []
        letters_before, time_before = self.letters(), self.time
        self.time += dt
        if self.letters() > letters_before:
            events.append("type")
        stamp = self.stamp_time()
        if stamp is not None and time_before < stamp <= self.time:
            events.append("stamp")
        return events

    def press(self):
        """
        The player pressed Space (or clicked). While typing: show all the text
        at once. Then: sign. After the stamp: go on without waiting.
        Returns events, like update().
        """
        if not self.typed():
            self.time = NOTICE_TYPE_DELAY + self.total_letters / NOTICE_TYPE_SPEED
            return []
        if self.signed_at is None:
            self.signed_at = self.time
            return ["sign"]
        if self.stamp_age() is not None:
            self.skipped = True
        return []
