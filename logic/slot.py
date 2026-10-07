"""
The slot machine on the hallway gossip screen: a reel with the exam's moods
spins and stops on today's mood, so the player sees that the mood is drawn
at random (run.py has already picked it).

The reel's position is a number: 0 = the first mood in the middle, 1 = the
second, and so on, going round and round. It goes SLOT_TURNS times all the
way round plus up to the picked mood, fast at first and slowing down
(ease-out, 1 - (1 - x)³), in SLOT_SPIN_TIME seconds. In the last part it
goes SLOT_BOUNCE too far and settles back (half a sine), like the "clunk"
of a real reel stopping. ui/draw_menus.py draws
it; main.py plays a tick each time a new mood passes the middle.

Only numbers here, so it is tested (tests/test_slot.py).
"""

import math

from settings import SLOT_SPIN_TIME, SLOT_TURNS, SLOT_BOUNCE

SETTLE_PART = 0.15   # the last 15 % of the spin is the overshoot and settling back


def reel_position(target, count, elapsed):
    """Where the reel is `elapsed` seconds after the spin started (see above)."""
    part = min(1.0, max(0.0, elapsed / SLOT_SPIN_TIME))
    eased = 1 - (1 - part) ** 3   # fast at first, slowing down to a stop
    # The overshoot: 0 until the last part, up to SLOT_BOUNCE, back to 0 at the end.
    settle = max(0.0, (part - (1 - SETTLE_PART)) / SETTLE_PART)
    return (SLOT_TURNS * count + target) * eased + SLOT_BOUNCE * math.sin(math.pi * settle)


def reel_speed(target, count, elapsed, step=0.02):
    """How fast the reel moves right now, in moods per second (for the blur)."""
    return abs(reel_position(target, count, elapsed + step)
               - reel_position(target, count, elapsed)) / step


def mood_in_middle(position, count):
    """Which mood (index) is closest to the middle of the window."""
    return round(position) % count


def has_stopped(elapsed):
    return elapsed >= SLOT_SPIN_TIME


def passed(before, after):
    """How many moods passed the middle between two positions (one tick each)."""
    return math.floor(after + 0.5) - math.floor(before + 0.5)
