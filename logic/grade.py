"""
The semester's letter grade, like at METU: AA (the best) to FF, on a curve.

Like a real teacher, the game gives no letter for a single exam: after an
exam you see your score and the class average. The letter comes at the end
of the run (the semester), from its total score, graded against ALL the
earlier runs on this computer (the "class", kept in the top scores file,
see highscore.py): the total's "z" is how many standard deviations it is
above the class average, and GRADES (settings.py) says which letter each z
gets. So the grades follow how well people usually do here: an average run
is a CC, a great one an AA.

Until GRADE_CURVE_MIN earlier runs exist there is no class yet, and the
grade comes from a fixed table instead: the share of all the exam points
you got (Run.share()). A total of 0 is always FF.

Like game.py, this file draws nothing and does not import pygame, so it can
be tested without a camera or a window (see tests/test_grade.py).
"""

import statistics

from settings import GRADES, GRADE_CURVE_MIN

LETTERS = [letter for letter, _, _ in GRADES]   # best first
FAIL = LETTERS[-1]                              # "FF"


def curve(scores):
    """
    (average, standard deviation) of the earlier scores, or None if there
    are fewer than GRADE_CURVE_MIN of them (no curve yet).
    """
    if len(scores) < GRADE_CURVE_MIN:
        return None
    return statistics.mean(scores), statistics.pstdev(scores)


def class_average(scores):
    """The average of the earlier scores (rounded), or None if there are none."""
    return round(statistics.mean(scores)) if scores else None


def z_score(score, average, spread):
    """How many standard deviations above the average. No spread (all equal): 1, 0 or -1."""
    if spread > 0:
        return (score - average) / spread
    return (score > average) - (score < average)


def letter_for_z(z):
    """On the curve: the grade for this z."""
    for letter, least, _ in GRADES:
        if z >= least:
            return letter
    return FAIL


def letter_for_share(share):
    """Without a curve: the grade for this share of the points (1.0 = all right)."""
    for letter, _, least in GRADES:
        if share >= least:
            return letter
    return FAIL


def semester_grade(total, share, past_totals):
    """
    The run's letter. total: its score; share: the share of the exam points
    got (Run.share()); past_totals: the totals of all the earlier runs.
    """
    if total <= 0:
        return FAIL
    stats = curve(past_totals)
    if stats is None:
        return letter_for_share(share)
    return letter_for_z(z_score(total, *stats))
