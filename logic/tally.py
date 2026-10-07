"""
The score tally on the end screen, one part at a time, like in Balatro.

Only for a handed-in (or collected) exam; a failed one scores 0 and gets the
game over chat instead. The parts come from game.score_parts(): first each
question (+1000 right, -500 wrong, 0 blank), then the time bonus, close
calls and warnings. Part i appears TALLY_START + i * TALLY_STEP_TIME seconds
after the end screen opened, and the score counts up to include it over
TALLY_COUNT_TIME. main.py plays a rising "tick" for each part that appears.

Only numbers here (no drawing), so it is tested in tests/test_tally.py.
"""

from settings import TALLY_START, TALLY_STEP_TIME, TALLY_COUNT_TIME


def appear_time(i):
    """Seconds after the end screen opened when part i (0 = first) appears."""
    return TALLY_START + i * TALLY_STEP_TIME


def parts_shown(parts, elapsed):
    """How many of the parts have appeared after `elapsed` seconds."""
    return sum(1 for i in range(len(parts)) if appear_time(i) <= elapsed)


def is_done(parts, elapsed):
    """True once the last part has appeared and finished counting."""
    return elapsed >= appear_time(len(parts) - 1) + TALLY_COUNT_TIME if parts else True


def running_score(parts, elapsed):
    """
    The score as it is shown while counting: the parts already counted,
    plus the newest one counting up. When done, the real score (never below 0).
    """
    if is_done(parts, elapsed):
        return max(0, sum(points for _, points in parts))
    shown = parts_shown(parts, elapsed)
    total = 0.0
    for i in range(shown):
        counted = min(1.0, (elapsed - appear_time(i)) / TALLY_COUNT_TIME)
        total += parts[i][1] * counted
    return int(total)
