"""
Your exam paper: the answer key, what you wrote, and the grade.

- Each question has a right letter (A-D), and only ONE neighbour (left or
  right, chosen at random) knows it. The other one's paper shows "?".
- You may write any letter at any time, even without copying it: a guess.
  Or you leave the question blank.
- Grading (the numbers are in settings.py): right = +1, wrong = -0.5,
  blank = 0. So a wild guess is a gamble: with four letters it is right only
  one time in four, and a wrong one costs you.

No pygame and no camera here, so it is tested on its own
(tests/test_exam_paper.py).
"""

from tracking.head_tracker import LEFT, RIGHT
from settings import ANSWERS_NEEDED, POINTS_CORRECT, POINTS_WRONG, POINTS_BLANK

LETTERS = "ABCD"   # the choices of every question
UNKNOWN = "?"      # what the neighbour who does not know the answer shows
BLANK = "-"        # written on your paper for a question you left blank

# How each written answer is graded, and what it is worth.
CORRECT, WRONG, EMPTY = "CORRECT", "WRONG", "EMPTY"
POINTS = {CORRECT: POINTS_CORRECT, WRONG: POINTS_WRONG, EMPTY: POINTS_BLANK}


class ExamPaper:
    def __init__(self, rng, questions=ANSWERS_NEEDED):
        # rng: a random.Random. Tests give one with a fixed seed, so the
        # "random" answer key is the same every run.
        self.right_letters = [rng.choice(LETTERS) for _ in range(questions)]
        self.knowing_side = [rng.choice((LEFT, RIGHT)) for _ in range(questions)]
        self.written = []   # what you wrote, in order: a letter, or BLANK

    def size(self):
        """How many questions this exam has."""
        return len(self.right_letters)

    def question(self):
        """Index (0 = question 1) of the question you are working on."""
        return len(self.written)

    def is_full(self):
        """True when every question has an answer (or a blank): hand it in."""
        return len(self.written) == self.size()

    def write(self, answer):
        """Write a letter (or BLANK) for the current question; on to the next one."""
        self.written.append(answer)

    def says(self, side):
        """
        What that neighbour's paper says for the current question: the
        letter, or "?" if they do not know it. None after the last question.
        """
        if self.is_full():
            return None
        q = self.question()
        return self.right_letters[q] if side == self.knowing_side[q] else UNKNOWN

    def results(self):
        """CORRECT, WRONG or EMPTY for each answer written so far, in order."""
        results = []
        for written, right in zip(self.written, self.right_letters):
            if written == BLANK:
                results.append(EMPTY)
            elif written == right:
                results.append(CORRECT)
            else:
                results.append(WRONG)
        return results

    def count(self, result):
        """How many answers got this result, e.g. count(CORRECT)."""
        return self.results().count(result)

    def points(self):
        """The grade: the points of all written answers (can be below 0)."""
        return sum(POINTS[result] for result in self.results())
