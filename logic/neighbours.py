"""
Reading a neighbour's paper ("gradual focus", Emre's idea).

Look at a neighbour and their paper is blurry; it gets sharper the longer
you keep looking. After PAPER_FOCUS_TIME seconds without looking away it is
sharp: you have READ it (the letter, or "?" = "try the other side"). Every
new look starts blurry again, so reading means holding one risky look.
While the teacher sees you, the paper does not get sharper.

Reading only tells you the answer; you still write it yourself (or guess
without reading, see exam_paper.py).
"""

from tracking.head_tracker import LEFT, RIGHT
from settings import PAPER_FOCUS_TIME


class NeighbourPapers:
    def __init__(self):
        self.last_direction = None
        self.new_question()

    def new_question(self):
        """A new question: nothing read yet, both papers blurry."""
        self.read_sides = set()   # neighbours whose paper you have read for this question
        self.reset_focus()

    def reset_focus(self):
        """Both papers blurry again (a new look, or the camera was lost)."""
        # Seconds you have been looking at each neighbour in this look.
        self.focus_time = {LEFT: 0.0, RIGHT: 0.0}

    def clarity(self, side):
        """How sharp that neighbour's paper is: 0 = blurry, 1 = sharp."""
        return min(1.0, self.focus_time[side] / PAPER_FOCUS_TIME)

    def has_read(self, side):
        return side in self.read_sides

    def update(self, direction, dt, can_focus):
        """
        Move the focus forward by dt seconds. can_focus is False while the
        teacher sees you copying. Returns ["read"] the moment a paper gets
        sharp (once per side and question), else [].
        """
        # Every look is new: turning anywhere else blurs both papers again.
        if direction != self.last_direction:
            self.reset_focus()
        self.last_direction = direction
        if direction not in (LEFT, RIGHT) or not can_focus:
            return []
        self.focus_time[direction] = min(PAPER_FOCUS_TIME, self.focus_time[direction] + dt)
        if self.focus_time[direction] >= PAPER_FOCUS_TIME and not self.has_read(direction):
            self.read_sides.add(direction)
            return ["read"]
        return []
