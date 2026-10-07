"""Tests for bag.py: random order, every item once per round, never twice in a row."""

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.bag import Bag


class BagTests(unittest.TestCase):
    def test_every_item_once_per_round(self):
        bag = Bag(range(8), random.Random(1))
        for _ in range(5):
            self.assertEqual(sorted(bag.draw() for _ in range(8)), list(range(8)))

    def test_never_the_same_twice_in_a_row(self):
        for seed in range(50):
            bag = Bag("abc", random.Random(seed))
            drawn = [bag.draw() for _ in range(30)]
            for a, b in zip(drawn, drawn[1:]):
                self.assertNotEqual(a, b, (seed, drawn))

    def test_order_is_not_always_the_same(self):
        orders = {tuple(Bag(range(6), random.Random(seed)).draw() for _ in range(6))
                  for seed in range(20)}
        self.assertGreater(len(orders), 1)

    def test_one_item_is_fine(self):
        bag = Bag(["only"], random.Random(2))
        self.assertEqual([bag.draw() for _ in range(3)], ["only"] * 3)


if __name__ == "__main__":
    unittest.main()
