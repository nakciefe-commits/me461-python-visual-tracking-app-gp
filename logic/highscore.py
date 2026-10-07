"""
The top scores: the best TOP_SCORES_KEPT runs, kept in a small file
(HIGH_SCORE_FILE, JSON) so they are still there the next time the game
starts. Each entry is {"score": 5230, "date": "7 OCT"}, best first.

A missing or broken file counts as "no scores yet"; an old file with only
{"best": ...} (before the top list) becomes a list with that one score. If
the file cannot be written (e.g. no permission), the game goes on without
saving.
"""

import json

from settings import TOP_SCORES_KEPT


def load_top(path):
    """The saved top scores, best first, or [] if there are none (or the file is broken)."""
    try:
        with open(path) as file:
            data = json.load(file)
        if "top" in data:
            top = [{"score": int(entry["score"]), "date": str(entry.get("date", ""))}
                   for entry in data["top"]]
        else:
            top = [{"score": int(data["best"]), "date": ""}]   # the old file
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []
    top = [entry for entry in top if entry["score"] > 0]
    return sorted(top, key=lambda entry: entry["score"], reverse=True)[:TOP_SCORES_KEPT]


def add_score(top, score, date):
    """
    Put a run's score into the list (if it is good enough).
    Returns (the new list, its place 0 = first), or (the same list, None)
    if it did not make it. 0 points never counts.
    """
    if score <= 0:
        return top, None
    new = sorted(top + [{"score": score, "date": date}],
                 key=lambda entry: entry["score"], reverse=True)
    # A tie with an older score goes under it: the older one got there first.
    place = max(i for i, entry in enumerate(new) if entry["score"] == score)
    if place >= TOP_SCORES_KEPT:
        return top, None
    return new[:TOP_SCORES_KEPT], place


def save_top(path, top):
    """Save the top scores. Returns False if they could not be written."""
    try:
        with open(path, "w") as file:
            json.dump({"top": top}, file)
        return True
    except OSError as error:
        print(f"Could not save the top scores ({error}).")
        return False
