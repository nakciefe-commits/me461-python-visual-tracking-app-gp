"""
The score tally on the end screen, one part at a time, like in Balatro.

Only for a handed-in (or collected) exam; a failed one scores 0 and gets the
game over chat instead. The parts come from game.score_parts(): first each
question (+1000 right, -500 wrong, 0 blank), then the time bonus, close
calls and warnings. Part i appears TALLY_START + i * TALLY_STEP_TIME seconds
after the end screen opened, and the score counts up to include it over
TALLY_COUNT_TIME. main.py plays a rising "tick" for each part that appears.

The score is drawn like the reels of a slot machine (ui/draw_results.py):
running_value() is the score with its fraction, so each digit's reel can
roll smoothly, and strength() says how wild the effects are, from 0 (a
small score) to 1 (a huge one); jackpot() is true for a very big score.

Only numbers here (no drawing), so it is tested in tests/test_tally.py.
"""

from settings import (TALLY_START, TALLY_STEP_TIME, TALLY_COUNT_TIME, TALLY_FX_FULL_SCORE,
                      TALLY_JACKPOT_SHARE)


def appear_time(i):
    """Seconds after the end screen opened when part i (0 = first) appears."""
    return TALLY_START + i * TALLY_STEP_TIME


def parts_shown(parts, elapsed):
    """How many of the parts have appeared after `elapsed` seconds."""
    return sum(1 for i in range(len(parts)) if appear_time(i) <= elapsed)


def done_time(parts):
    """Seconds after the end screen opened when the count is over (0 if there is nothing to count)."""
    return appear_time(len(parts) - 1) + TALLY_COUNT_TIME if parts else 0.0


def is_done(parts, elapsed):
    """True once the last part has appeared and finished counting."""
    return elapsed >= done_time(parts)


def running_value(parts, elapsed):
    """
    The score as it is shown while counting, with its fraction: the parts
    already counted, plus the newest one counting up. When done, the real
    score (never below 0).
    """
    if is_done(parts, elapsed):
        return float(max(0, sum(points for _, points in parts)))
    total = 0.0
    for i in range(parts_shown(parts, elapsed)):
        counted = min(1.0, (elapsed - appear_time(i)) / TALLY_COUNT_TIME)
        total += parts[i][1] * counted
    return total


def running_score(parts, elapsed):
    """running_value() as a whole number, for the text."""
    return int(running_value(parts, elapsed))


def is_counting(parts, elapsed):
    """True while the newest part is still counting up (the reels are spinning)."""
    shown = parts_shown(parts, elapsed)
    return shown > 0 and not is_done(parts, elapsed) and elapsed - appear_time(shown - 1) < TALLY_COUNT_TIME


def strength(score, exams=1):
    """
    How wild the slot-machine effects are for this score: 0 = calm, 1 =
    TALLY_FX_FULL_SCORE per exam or more. exams: how many exams the score
    is the total of (the run's total is bigger, so it needs more).
    """
    return min(1.0, max(0.0, score / (TALLY_FX_FULL_SCORE * exams)))


def jackpot(score, exams=1):
    """True for a score big enough for "JACKPOT!" at the end of the count."""
    return strength(score, exams) >= TALLY_JACKPOT_SHARE
