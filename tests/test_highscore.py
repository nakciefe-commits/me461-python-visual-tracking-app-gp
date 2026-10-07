"""Tests for the top scores file in highscore.py (uses a temporary folder)."""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.highscore import load_top, add_score, save_top
from settings import TOP_SCORES_KEPT


class TopScoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "highscore.json")

    def test_no_file_is_empty(self):
        self.assertEqual(load_top(self.path), [])

    def test_save_and_load(self):
        top = [{"score": 4230, "date": "7 OCT"}, {"score": 900, "date": "6 OCT"}]
        self.assertTrue(save_top(self.path, top))
        self.assertEqual(load_top(self.path), top)

    def test_old_best_score_file_still_loads(self):
        with open(self.path, "w") as file:
            json.dump({"best": 1500}, file)
        self.assertEqual(load_top(self.path), [{"score": 1500, "date": ""}])

    def test_broken_file_is_empty(self):
        with open(self.path, "w") as file:
            file.write("not json {")
        self.assertEqual(load_top(self.path), [])

    def test_cannot_write_does_not_crash(self):
        folder_path = os.path.dirname(self.path)
        self.assertFalse(save_top(folder_path, []))   # a folder, not a file

    def test_add_keeps_best_first(self):
        top, place = add_score([], 500, "A")
        top, place = add_score(top, 900, "B")
        self.assertEqual(place, 0)
        top, place = add_score(top, 700, "C")
        self.assertEqual(place, 1)
        self.assertEqual([entry["score"] for entry in top], [900, 700, 500])

    def test_only_the_best_are_kept(self):
        top = [{"score": 1000 * (i + 1), "date": ""} for i in range(TOP_SCORES_KEPT)][::-1]
        same, place = add_score(top, 10, "X")   # worse than all of them
        self.assertIsNone(place)
        self.assertEqual(same, top)
        new, place = add_score(top, 10**6, "Y")
        self.assertEqual(place, 0)
        self.assertEqual(len(new), TOP_SCORES_KEPT)

    def test_a_tie_goes_under_the_older_score(self):
        top, _ = add_score([], 800, "old")
        top, place = add_score(top, 800, "new")
        self.assertEqual(place, 1)

    def test_zero_never_counts(self):
        self.assertEqual(add_score([], 0, "X"), ([], None))


if __name__ == "__main__":
    unittest.main()
