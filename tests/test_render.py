"""Check paper visibility, single-question neighbours and gradual blur headlessly."""

import os
import random
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pygame
from game import Game
from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from render import Renderer
from settings import NEIGHBOUR_PAPER_RECT, PAPER_RECT, PAPER_FOCUS_TIME, ANSWERS_NEEDED
from teacher import Teacher


class PaperRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.display.init()
        pygame.font.init()
        cls.screen = pygame.display.set_mode((960, 600))
        cls.renderer = Renderer(cls.screen)

    @classmethod
    def tearDownClass(cls):
        pygame.display.quit()
        pygame.font.quit()

    def setUp(self):
        self.game = Game(random.Random(1))
        self.teacher = Teacher(random.Random(1))

    def draw(self, direction, debug=False):
        self.renderer.draw_game(self.game, self.teacher, direction,
                                1 if direction == SCREEN else 0, None, 0, 0, 30, '', debug)

    def question_labels(self, text_spy):
        return [call.args[0] for call in text_spy.call_args_list
                if call.args[0].endswith('. soru')]

    def test_teacher_view_has_no_paper_even_with_debug_enabled(self):
        for debug in (False, True):
            with self.subTest(debug=debug):
                self.draw(SCREEN, debug)
                # This centre region used to contain the compact own paper.
                region = (30, 280, 650, 225)
                actual = pygame.surfarray.array3d(self.screen.subsurface(region))
                expected = pygame.surfarray.array3d(
                    self.renderer.classroom[self.teacher.image_name()].subsurface(region))
                np.testing.assert_array_equal(actual, expected)

    def test_each_neighbour_initially_displays_only_question_one(self):
        for direction in (LEFT, RIGHT):
            with self.subTest(direction=direction):
                with patch.object(self.renderer, 'text', wraps=self.renderer.text) as text:
                    self.draw(direction)
                self.assertEqual(self.question_labels(text), ['1. soru'])

    def test_answer_advances_neighbour_view_to_only_the_next_question(self):
        self.game.answer(self.game.answer_key[0], DOWN)
        with patch.object(self.renderer, 'text', wraps=self.renderer.text) as text:
            self.draw(LEFT)
        self.assertEqual(self.question_labels(text), ['2. soru'])
        self.assertEqual(self.game.answers, 1)

    def test_own_paper_keeps_all_questions_and_is_sharp(self):
        with (patch.object(self.renderer, 'text', wraps=self.renderer.text) as text,
              patch.object(self.renderer, 'blur_paper') as blur):
            self.draw(DOWN)
        self.assertEqual(self.question_labels(text),
                         [f'{number}. soru' for number in range(1, ANSWERS_NEEDED + 1)])
        blur.assert_not_called()

    def test_paper_edges_become_progressively_clearer(self):
        contrast = []
        for clarity in (0.0, 0.5, 1.0):
            self.game.paper_focus_time = clarity * PAPER_FOCUS_TIME
            self.draw(LEFT)
            pixels = pygame.surfarray.array3d(self.screen.subsurface(NEIGHBOUR_PAPER_RECT))
            grey = pixels.astype(float).mean(axis=2)
            contrast.append(np.square(np.diff(grey, axis=0)).mean()
                            + np.square(np.diff(grey, axis=1)).mean())
        self.assertLess(contrast[0], contrast[1])
        self.assertLess(contrast[1], contrast[2])

    def test_drawing_never_advances_focus_or_changes_answers(self):
        before = self.game.player_answers.copy()
        self.draw(LEFT)
        self.draw(LEFT)
        self.assertEqual(self.game.paper_clarity, 0)
        self.assertEqual(self.game.player_answers, before)
        self.assertEqual(self.game.active_question, 0)


if __name__ == '__main__':
    unittest.main()
