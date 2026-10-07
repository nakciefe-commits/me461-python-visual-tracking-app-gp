"""
The best score, kept in a small file (HIGH_SCORE_FILE, JSON) so it is still
there the next time the game starts.

A missing or broken file counts as "no best score yet" (0); if the file
cannot be written (e.g. no permission), the game goes on without saving.
"""

import json


def load_best(path):
    """The best score saved in `path`, or 0 if there is none (or it is broken)."""
    try:
        with open(path) as file:
            return max(0, int(json.load(file)["best"]))
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_best(path, score):
    """Save `score` as the best score. Returns False if it could not be written."""
    try:
        with open(path, "w") as file:
            json.dump({"best": score}, file)
        return True
    except OSError as error:
        print(f"Could not save the best score ({error}).")
        return False
