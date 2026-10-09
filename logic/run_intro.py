"""
The run intro: a short, sarcastic "briefing" before the character screen,
timed to the character music (like the chapter screens of Hotline Miami).

On every strong hit of the music (the start of each bar, INTRO_FIRST_HIT
and then every 4 beats) a new line slams onto the screen: "3 EXAMS.",
"1 SEMESTER."... Each line hits harder than the one before. The last one,
the game's name "DON'T GET CAUGHT.", comes a bar later like the others,
just after the drop (INTRO_DROP, where the music gets twice as loud), and
stays longer (INTRO_TITLE_BEATS); then the characters slide in.
The beats keep going on the character screen, so it thumps along too.

All times are seconds since the music started (main.py takes them from
the music player, or counts them itself when there is no sound). Only
numbers here, so it is tested (tests/test_run_intro.py).
"""

from settings import CHARACTER_MUSIC_BPM, INTRO_FIRST_HIT, INTRO_TITLE_BEATS

BEAT = 60 / CHARACTER_MUSIC_BPM   # seconds per beat
BAR = 4 * BEAT                    # seconds per bar (4 beats)

# One line per bar, in order; the last one (the game's name) stays longer.
INTRO_LINES = [
    "3 EXAMS.",
    "1 SEMESTER.",
    "0 HOURS OF STUDYING.",
    "YOUR FAMILY EXPECTS...",
    "...THE MAXIMUM SCORE.",
    "NO PRESSURE.",
    "(A LOT OF PRESSURE.)",
    "DON'T GET CAUGHT.",
]
FINAL_LINE = len(INTRO_LINES) - 1   # the game's name: drawn biggest of all


def line_time(i):
    """Seconds into the music when line i (0 = first) slams in."""
    return INTRO_FIRST_HIT + i * BAR


# Seconds into the music when the title is gone and the characters come.
INTRO_END = line_time(FINAL_LINE) + INTRO_TITLE_BEATS * BEAT


def intensity(line):
    """0 for the first line, rising to 1 for the last: how wild the drawing gets."""
    return line / FINAL_LINE if line is not None else 0.0


def current_line(t):
    """The index of the line on screen at time t, or None before the first one."""
    shown = [i for i in range(len(INTRO_LINES)) if line_time(i) <= t]
    return shown[-1] if shown else None


def since_line(t):
    """Seconds since the current line slammed in (a big number before the first)."""
    line = current_line(t)
    return t - line_time(line) if line is not None else 1e9


def is_over(t):
    """True once the title has stayed its beats after the drop: time for the characters."""
    return t >= INTRO_END


def since_beat(t):
    """Seconds since the last beat (0 right on it); the beats line up with the first hit."""
    return (t - INTRO_FIRST_HIT) % BEAT


def beat_number(t):
    """How many beats have passed since the first hit (it goes up by one on every beat)."""
    return int((t - INTRO_FIRST_HIT) // BEAT)


def since_bar(t):
    """Seconds since the last bar's first beat (the strong hit)."""
    return (t - INTRO_FIRST_HIT) % BAR
