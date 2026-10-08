"""
The run intro: a short, sarcastic "briefing" before the character screen,
timed to the character music (like the chapter screens of Hotline Miami).

On every strong hit of the music (the start of each bar, INTRO_FIRST_HIT
and then every 4 beats) a new line slams onto the screen: "3 EXAMS.",
"1 SEMESTER."... When the music "drops" (INTRO_DROP, where it gets twice
as loud) the intro is over and the characters slide in. The beats keep
going on the character screen, so it thumps along too.

All times are seconds since the music started (main.py takes them from
the music player, or counts them itself when there is no sound). Only
numbers here, so it is tested (tests/test_run_intro.py).
"""

from settings import CHARACTER_MUSIC_BPM, INTRO_FIRST_HIT, INTRO_DROP

BEAT = 60 / CHARACTER_MUSIC_BPM   # seconds per beat
BAR = 4 * BEAT                    # seconds per bar (4 beats)

# One line per bar, in order. The last one comes just before the drop.
INTRO_LINES = [
    "3 EXAMS.",
    "1 SEMESTER.",
    "0 HOURS OF STUDYING.",
    "YOUR FAMILY EXPECTS...",
    "...THE MAXIMUM SCORE.",
    "NO PRESSURE.",
    "(A LOT OF PRESSURE.)",
]


def line_time(i):
    """Seconds into the music when line i (0 = first) slams in."""
    return INTRO_FIRST_HIT + i * BAR


def current_line(t):
    """The index of the line on screen at time t, or None before the first one."""
    shown = [i for i in range(len(INTRO_LINES)) if line_time(i) <= t]
    return shown[-1] if shown else None


def since_line(t):
    """Seconds since the current line slammed in (a big number before the first)."""
    line = current_line(t)
    return t - line_time(line) if line is not None else 1e9


def is_over(t):
    """True from the drop on: time for the characters."""
    return t >= INTRO_DROP


def since_beat(t):
    """Seconds since the last beat (0 right on it); the beats line up with the first hit."""
    return (t - INTRO_FIRST_HIT) % BEAT


def beat_number(t):
    """How many beats have passed since the first hit (it goes up by one on every beat)."""
    return int((t - INTRO_FIRST_HIT) // BEAT)


def since_bar(t):
    """Seconds since the last bar's first beat (the strong hit)."""
    return (t - INTRO_FIRST_HIT) % BAR
