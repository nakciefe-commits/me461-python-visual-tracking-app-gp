"""
The top scores: the best TOP_SCORES_KEPT runs, kept in a small file
(HIGH_SCORE_FILE, JSON) so they are still there the next time the game
starts. Each entry is {"score": 5230, "date": "7 OCT", "name": "EFE"},
best first. The name is the player's three letters (see name_entry.py);
"" until they are typed, and in files from before names.

The same file keeps the history of ALL the plays on this computer (not only
the best), for the letter grade's curve and the class averages (see
grade.py): {"runs": [every run's total], "exams": {"THE QUIZ": [every score
of that exam], ...}}, the newest GRADE_HISTORY_KEPT of each.

A missing or broken file counts as "no scores yet"; an old file with only
{"best": ...} (before the top list) becomes a list with that one score. If
the file cannot be written (e.g. no permission), the game goes on without
saving.
"""

import json

from settings import TOP_SCORES_KEPT, NAME_LETTERS, GRADE_HISTORY_KEPT


def load_top(path):
    """The saved top scores, best first, or [] if there are none (or the file is broken)."""
    try:
        with open(path) as file:
            data = json.load(file)
        if "top" in data:
            top = [{"score": int(entry["score"]), "date": str(entry.get("date", "")),
                    "name": str(entry.get("name", ""))[:NAME_LETTERS]}
                   for entry in data["top"]]
        else:
            top = [{"score": int(data["best"]), "date": "", "name": ""}]   # the old file
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return []
    top = [entry for entry in top if entry["score"] > 0]
    return sorted(top, key=lambda entry: entry["score"], reverse=True)[:TOP_SCORES_KEPT]


def add_score(top, score, date, name=""):
    """
    Put a run's score into the list (if it is good enough), with no name
    yet unless one is given (set_name() adds it once it is typed).
    Returns (the new list, its place 0 = first), or (the same list, None)
    if it did not make it. 0 points never counts.
    """
    if score <= 0:
        return top, None
    new = sorted(top + [{"score": score, "date": date, "name": name}],
                 key=lambda entry: entry["score"], reverse=True)
    # A tie with an older score goes under it: the older one got there first.
    place = max(i for i, entry in enumerate(new) if entry["score"] == score)
    if place >= TOP_SCORES_KEPT:
        return top, None
    return new[:TOP_SCORES_KEPT], place


def set_name(top, place, name):
    """The list with the name of the score at `place` set (a new list; `top` is not changed)."""
    new = [dict(entry) for entry in top]
    new[place]["name"] = name
    return new


def empty_history():
    return {"runs": [], "exams": {}}


def load_history(path):
    """Every earlier run's total and every earlier exam score; empty if there are none."""
    try:
        with open(path) as file:
            data = json.load(file)["history"]
        runs = [int(score) for score in data["runs"]]
        exams = {str(title): [int(score) for score in scores]
                 for title, scores in data["exams"].items()}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return empty_history()
    return {"runs": runs, "exams": exams}


def remember(scores, score):
    """The list with `score` added at the end, keeping only the newest GRADE_HISTORY_KEPT."""
    return (scores + [score])[-GRADE_HISTORY_KEPT:]


def save_top(path, top, history=None):
    """Save the top scores (and the history, if given). Returns False if they could not be written."""
    data = {"top": top}
    if history is not None:
        data["history"] = history
    try:
        with open(path, "w") as file:
            json.dump(data, file)
        return True
    except OSError as error:
        print(f"Could not save the top scores ({error}).")
        return False
