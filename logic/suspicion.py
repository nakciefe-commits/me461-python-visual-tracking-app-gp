"""
The suspicion bar, 0 (empty) to 1 (full).

- Seen copying (looking sideways while the teacher watches): it fills in
  CAUGHT_TIME. Full = caught.
- Staring at the teacher while they look at the class: it fills in
  WARNING_TIME (a free part, then the dangerous part). Full = a warning.
- Neither: it drains slowly (SUSPICION_DRAIN_TIME for a full bar).
- A character can change the two fill speeds, and the guy with the cap
  makes it creep up slowly (creep_time) whenever he is not looking at his
  paper, instead of draining (see logic/character.py).
- Seen and got away in time: a close call, worth more the fuller the bar was.

Both fill the same bar, so staring after being seen carries on from there.
It never jumps back to empty by itself, because that would tell the player
the teacher looked away.

The bar only says that it is full; game.py decides what that means (caught
or a warning).
"""

from settings import (STARE_GRACE_TIME, STARE_FILL_TIME, CAUGHT_TIME, SUSPICION_DRAIN_TIME,
                      CLOSE_CALL_MIN, CLOSE_CALL_PER_BAR, CLOSE_CALL_EDGE, CLOSE_CALL_EDGE_BONUS)

# Staring this long (from an empty bar) gives a warning.
WARNING_TIME = STARE_GRACE_TIME + STARE_FILL_TIME
# The free part of the bar: staring only gets dangerous past it.
GRACE_PART = STARE_GRACE_TIME / WARNING_TIME
# The bar counts as full from here. Adding up many small dt / time steps can
# end just below 1 because of rounding (e.g. 24 steps of 0.125 / 3.0).
FULL = 1 - 1e-9


def close_call_points(level):
    """
    What getting away is worth when the bar was this full (0..1): the
    closer you came to being caught, the more. Above CLOSE_CALL_EDGE it is
    a "razor close" call with an extra bonus.
    """
    points = CLOSE_CALL_MIN + CLOSE_CALL_PER_BAR * level
    if level >= CLOSE_CALL_EDGE:
        points += CLOSE_CALL_EDGE_BONUS
    return int(points)


class SuspicionBar:
    def __init__(self, seen_speed=1.0, stare_speed=1.0, creep_time=None):
        # The character's numbers (1.0 = normal; creep_time None = no creeping).
        self.seen_speed = seen_speed
        self.stare_speed = stare_speed
        self.creep_time = creep_time
        self.level = 0.0
        self.seen_copying = False   # raised by being seen copying (drawn red)
        self.was_seen = False       # seen copying last frame? (the alarm plays when it starts)
        self.close_calls = 0        # times you were seen copying and got away
        self.close_call_score = 0   # what those were worth together (see close_call_points())
        self.last_close_call = 0    # points of the latest one (for the popup)

    def is_full(self):
        return self.level >= FULL

    def start_over(self):
        """After a warning the bar is empty again."""
        self.level = 0.0
        self.seen_copying = False

    def update(self, seen, staring, dt, away=False):
        """
        Fill or drain the bar for dt seconds. away: not looking at your paper
        (only matters with creep_time). Returns events: "spotted" when the
        teacher starts seeing you copy (the alarm), "close_call" when you
        looked away in time.
        """
        events = []
        before = self.level
        if seen:
            if not self.was_seen:
                events.append("spotted")   # the screen is black, so the player must hear it
            self.seen_copying = True
            self.level += self.seen_speed * dt / CAUGHT_TIME
        elif staring:
            self.level += self.stare_speed * dt / WARNING_TIME
        elif away and self.creep_time:
            self.level += dt / self.creep_time   # the cap: it creeps up, it never drains
        else:
            self.level = max(0.0, self.level - dt / SUSPICION_DRAIN_TIME)
            if self.level == 0:
                self.seen_copying = False
        if self.was_seen and not seen:
            # The teacher saw you copying, and you got away. It counts how
            # full the bar was at the end of being seen (before this frame).
            self.close_calls += 1
            self.last_close_call = close_call_points(before)
            self.close_call_score += self.last_close_call
            events.append("close_call")
        self.was_seen = seen
        return events
