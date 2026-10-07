"""
One run: three exams in a row (QUIZZES in settings.py), like a semester.

    THE QUIZ  ->  THE MIDTERM  ->  THE FINAL

Each exam has its own time and number of questions, and the teacher is in
a mood picked at random from that exam's two (MOODS in settings.py). The
rules of one exam stay in game.py; this file only puts the exams in order
and adds up their scores. A failed exam (caught, or too many warnings)
scores 0, and the run goes on to the next one, so a run is always three
exams. The run's score is the total; the top scores are the best runs.

No pygame and no camera here, so it is tested on its own (tests/test_run.py).
"""

import random

from logic.game import Game, WON
from settings import QUIZZES, MOODS


class Run:
    def __init__(self, rng=None):
        # Tests pass a random.Random with a fixed seed.
        self.rng = rng or random.Random()
        # Today's mood for each exam, picked now so the whole run is known.
        self.moods = [self.rng.choice(quiz["moods"]) for quiz in QUIZZES]
        self.results = []   # one per finished exam, see finish_quiz()

    def number(self):
        """Index (0 = the first exam) of the exam being played or next."""
        return len(self.results)

    def quiz(self):
        """The settings of the current exam (title, time, questions, moods)."""
        return QUIZZES[self.number()]

    def mood(self):
        """The teacher's mood name for the current exam."""
        return self.moods[self.number()]

    def gossip(self):
        """
        Today's mood as the "hallway gossip" screen tells it before the exam:
        {"gossip": ..., "story": [lines], "good": [...], "bad": [...]} (and
        its numbers).
        """
        return MOODS[self.mood()]

    def pool(self):
        """All the moods the current exam can pick from (the slot machine's reel)."""
        return [MOODS[name] for name in self.quiz()["moods"]]

    def chosen(self):
        """Which of pool() is today's mood."""
        return self.quiz()["moods"].index(self.mood())

    def new_game(self):
        """A fresh Game for the current exam: its own time and questions, 0 warnings."""
        quiz = self.quiz()
        return Game(self.rng, exam_time=quiz["time"], questions=quiz["questions"],
                    suspicious_at=quiz["suspicious"])

    def finish_quiz(self, game):
        """The current exam is over (handed in, collected or failed): keep its result."""
        self.results.append({
            "title": self.quiz()["title"],
            "handed_in": game.state == WON,
            "lose_reason": game.lose_reason,
            "points": game.paper.points() if game.state == WON else 0,
            "questions": game.paper.size(),
            "score": game.score(),   # 0 when failed
        })

    def is_over(self):
        """True after the last exam."""
        return self.number() == len(QUIZZES)

    def score_parts(self):
        """Each finished exam's score as (title, points), for the run's score count."""
        return [(result["title"], result["score"]) for result in self.results]

    def total(self):
        """The run's score: all exam scores added up."""
        return sum(result["score"] for result in self.results)
