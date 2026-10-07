"""
Typing a name for a new top score, like on an arcade machine: three
letters, each one rolled through the alphabet.

With the head (the same actions as the menus, see menu.py):
    tilt UP / DOWN   the letter rolls to the next / previous one (Z → A)
    turn RIGHT       on to the next letter; after the last one, done
    turn LEFT        back to the letter before
With the keys: type a letter (it is set and the next one is chosen),
Backspace goes back, Enter is done.

Like game.py, this file draws nothing and does not import pygame, so it can
be tested without a camera or a window (see tests/test_name_entry.py).
"""

from settings import NAME_LETTERS

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class NameEntry:
    def __init__(self, start=""):
        """start: the letters to begin with (e.g. the last name typed); "A"s if none."""
        start = "".join(letter for letter in start.upper() if letter in ALPHABET)
        self.letters = list((start + "A" * NAME_LETTERS)[:NAME_LETTERS])
        self.slot = 0        # which letter is being chosen (0 = the first)
        self.done = False

    def name(self):
        return "".join(self.letters)

    def roll(self, step):
        """+1 = the next letter of the alphabet, -1 = the one before; it wraps round."""
        if self.done:
            return
        i = ALPHABET.index(self.letters[self.slot])
        self.letters[self.slot] = ALPHABET[(i + step) % len(ALPHABET)]

    def next(self):
        """On to the next letter; after the last one the name is done."""
        if self.done:
            return
        if self.slot == NAME_LETTERS - 1:
            self.done = True
        else:
            self.slot += 1

    def back(self):
        """Back to the letter before (stays on the first one)."""
        if not self.done:
            self.slot = max(0, self.slot - 1)

    def type(self, letter):
        """A typed letter: set it here and go on. Anything but A-Z does nothing."""
        letter = letter.upper()
        if self.done or letter not in ALPHABET or len(letter) != 1:
            return
        self.letters[self.slot] = letter
        self.next()

    def finish(self):
        """Done now, with the letters as they are."""
        self.done = True
