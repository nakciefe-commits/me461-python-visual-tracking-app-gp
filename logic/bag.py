"""
A "bag" of items handed out in a random order, like the pieces in Tetris:
every item comes once before any item comes again, so nothing repeats too
soon, but the order still cannot be guessed. The first item of a new round
is never the one that came last, so the same item never comes twice in a
row.

Used for the game over chat (a different joke every time). PLAN.md 11.4
plans the same for the teacher's moves.

No pygame here, so it is tested on its own (tests/test_bag.py).
"""

import random


class Bag:
    def __init__(self, items, rng=None):
        # rng: a random.Random; tests give one with a fixed seed.
        self.items = list(items)
        self.rng = rng or random.Random()
        self.left = []     # what is still in the bag this round
        self.last = None   # the item handed out last

    def draw(self):
        """The next item. When the bag is empty, it is refilled and shuffled."""
        if not self.left:
            self.left = list(self.items)
            self.rng.shuffle(self.left)
            # draw() takes from the end: never start a round with the last item.
            if len(self.left) > 1 and self.left[-1] == self.last:
                self.left[0], self.left[-1] = self.left[-1], self.left[0]
        self.last = self.left.pop()
        return self.last
