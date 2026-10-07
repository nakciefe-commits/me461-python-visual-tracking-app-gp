"""Tests for typing a top score's name in name_entry.py (no camera or window needed)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.name_entry import NameEntry, ALPHABET
from settings import NAME_LETTERS


class NameEntryTests(unittest.TestCase):
    def test_starts_with_as(self):
        entry = NameEntry()
        self.assertEqual(entry.name(), "A" * NAME_LETTERS)
        self.assertEqual(entry.slot, 0)
        self.assertFalse(entry.done)

    def test_starts_with_the_given_letters(self):
        self.assertEqual(NameEntry("efe").name(), ("EFE" + "A" * NAME_LETTERS)[:NAME_LETTERS])
        self.assertEqual(NameEntry("a1!").name(), "A" * NAME_LETTERS)   # only letters count

    def test_rolling_wraps_round(self):
        entry = NameEntry()
        entry.roll(-1)
        self.assertEqual(entry.letters[0], "Z")
        entry.roll(1)
        entry.roll(1)
        self.assertEqual(entry.letters[0], "B")

    def test_head_through_all_letters(self):
        entry = NameEntry()
        for _ in range(NAME_LETTERS - 1):
            entry.roll(1)
            entry.next()
        self.assertFalse(entry.done)
        entry.next()
        self.assertTrue(entry.done)
        self.assertEqual(entry.name(), "B" * (NAME_LETTERS - 1) + "A")

    def test_back_goes_to_the_letter_before(self):
        entry = NameEntry()
        entry.back()
        self.assertEqual(entry.slot, 0)   # nowhere to go back to
        entry.next()
        entry.back()
        self.assertEqual(entry.slot, 0)

    def test_typing(self):
        entry = NameEntry()
        for letter in "efe"[:NAME_LETTERS]:
            entry.type(letter)
        self.assertTrue(entry.done)
        self.assertEqual(entry.name(), "EFE"[:NAME_LETTERS])

    def test_typing_ignores_other_keys(self):
        entry = NameEntry()
        entry.type("7")
        entry.type("")
        self.assertEqual(entry.slot, 0)
        self.assertEqual(entry.name(), "A" * NAME_LETTERS)

    def test_nothing_changes_once_done(self):
        entry = NameEntry()
        entry.finish()
        entry.roll(1)
        entry.type("Z")
        entry.back()
        self.assertEqual(entry.name(), "A" * NAME_LETTERS)
        self.assertTrue(entry.done)

    def test_alphabet(self):
        self.assertEqual(len(ALPHABET), 26)


if __name__ == "__main__":
    unittest.main()
