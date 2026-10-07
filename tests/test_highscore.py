"""Tests for the best score file in highscore.py (uses a temporary folder)."""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from highscore import load_best, save_best


class HighScoreTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = os.path.join(folder.name, "highscore.json")

    def test_no_file_is_zero(self):
        self.assertEqual(load_best(self.path), 0)

    def test_save_and_load(self):
        self.assertTrue(save_best(self.path, 4230))
        self.assertEqual(load_best(self.path), 4230)

    def test_broken_file_is_zero(self):
        with open(self.path, "w") as file:
            file.write("not json {")
        self.assertEqual(load_best(self.path), 0)

    def test_cannot_write_does_not_crash(self):
        folder_path = os.path.dirname(self.path)
        self.assertFalse(save_best(folder_path, 10))   # a folder, not a file


if __name__ == "__main__":
    unittest.main()
