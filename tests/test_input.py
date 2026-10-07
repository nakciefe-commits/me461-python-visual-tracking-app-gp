"""Keyboard and main-loop tests: answers use the current tracked direction."""

import os
import random
import sys
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pygame
import main
from game import Game
from head_tracker import DOWN, SCREEN, LEFT
from settings import ANSWER_CHOICES, ANSWERS_NEEDED


class KeyboardTests(unittest.TestCase):
    def test_c_and_d_write_answers_instead_of_triggering_old_shortcuts(self):
        game = Game(random.Random(1))
        main.handle_exam_key(game, pygame.K_c, SCREEN)
        main.handle_exam_key(game, pygame.K_d, DOWN)
        self.assertEqual(game.player_answers[:2], ["c", "d"])

    def test_keyboard_maps_all_five_options(self):
        for choice in ANSWER_CHOICES:
            with self.subTest(choice=choice):
                game = Game()
                main.handle_exam_key(game, getattr(pygame, "K_" + choice), SCREEN)
                self.assertEqual(game.player_answers[0], choice)

    def test_arrow_keys_revisit_questions(self):
        game = Game()
        main.handle_exam_key(game, pygame.K_UP, SCREEN)
        self.assertEqual(game.active_question, ANSWERS_NEEDED - 1)
        main.handle_exam_key(game, pygame.K_DOWN, DOWN)
        self.assertEqual(game.active_question, 0)

    def test_shortcuts_and_sideways_input_do_not_write(self):
        game = Game()
        for key in (pygame.K_F2, pygame.K_F3, pygame.K_r, pygame.K_q):
            main.handle_exam_key(game, key, SCREEN)
        main.handle_exam_key(game, pygame.K_a, LEFT)
        main.handle_exam_key(game, pygame.K_b, None)
        self.assertEqual(game.answers, 0)

    def test_main_uses_fresh_direction_and_blocks_input_while_paused(self):
        game = Game(random.Random(1))
        tracker = MagicMock()
        tracker.relative_angles.return_value = (0, 0)
        # Sideways/paused presses are discarded, then C and D write normally.
        tracker.current_direction.side_effect = [LEFT, None, SCREEN, DOWN, DOWN]
        batches = [[pygame.event.Event(pygame.KEYDOWN, key=key)]
                   for key in (pygame.K_SPACE, pygame.K_SPACE,
                               pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d)]
        batches.append([pygame.event.Event(pygame.QUIT)])
        camera = MagicMock()
        calibration = MagicMock()
        calibration.done.return_value = True
        with (patch.object(main.pygame, "init"),
              patch.object(main.pygame, "quit"),
              patch.object(main.pygame.display, "set_caption"),
              patch.object(main.pygame.display, "flip"),
              patch.object(main.pygame.event, "get", side_effect=batches),
              patch.object(main.pygame.time, "Clock"),
              patch.object(main, "open_window"),
              patch.object(main, "Renderer"),
              patch.object(main, "Sounds"),
              patch.object(main, "camera_to_surface"),
              patch.object(main, "Camera", return_value=camera),
              patch.object(main, "HeadTracker", return_value=tracker),
              patch.object(main, "Calibration", return_value=calibration),
              patch.object(main, "Game", return_value=game)):
            main.main()
        self.assertEqual(game.player_answers[:2], ["c", "d"])
        self.assertEqual(game.answers, 2)
        camera.release.assert_called_once()
        tracker.close.assert_called_once()

    def test_camera_gap_keeps_window_open_and_freezes_teacher_exam_and_keys(self):
        game = Game(random.Random(1))
        teacher = MagicMock()
        teacher.is_watching.return_value = False
        teacher.is_facing_class.return_value = False
        teacher.sounds.return_value = []
        tracker = MagicMock()
        tracker.relative_angles.return_value = (0, 0)
        tracker.current_direction.side_effect = [SCREEN, DOWN]
        camera = MagicMock()
        picture = MagicMock()
        camera.read.side_effect = [picture, picture, None, None, picture, picture]
        camera.status = 'Camera 1 stopped sending pictures; reconnecting...'
        batches = [[pygame.event.Event(pygame.KEYDOWN, key=key)]
                   for key in (pygame.K_SPACE, pygame.K_SPACE,
                               pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d)]
        batches.append([pygame.event.Event(pygame.QUIT)])
        calibration = MagicMock()
        calibration.done.return_value = True
        with (patch.object(main.pygame, 'init'),
              patch.object(main.pygame, 'quit'),
              patch.object(main.pygame.display, 'set_caption'),
              patch.object(main.pygame.display, 'flip'),
              patch.object(main.pygame.event, 'get', side_effect=batches),
              patch.object(main.pygame.time, 'Clock'),
              patch.object(main, 'open_window'),
              patch.object(main, 'Renderer') as renderer,
              patch.object(main, 'Sounds'),
              patch.object(main, 'camera_to_surface'),
              patch.object(main, 'Camera', return_value=camera),
              patch.object(main, 'HeadTracker', return_value=tracker),
              patch.object(main, 'Calibration', return_value=calibration),
              patch.object(main, 'Teacher', return_value=teacher),
              patch.object(main, 'Game', return_value=game),
              patch.object(game, 'update', wraps=game.update) as update):
            main.main()
        self.assertEqual(renderer.return_value.draw_camera_wait.call_count, 2)
        self.assertEqual(game.player_answers[:2], ['c', 'd'])
        self.assertEqual(game.answers, 2)
        self.assertEqual(update.call_count, 2)
        self.assertEqual(teacher.update.call_count, 2)
        tracker.reset_tracking.assert_called_once()
        camera.release.assert_called_once()

    def test_quit_works_if_the_camera_never_produces_a_picture(self):
        camera = MagicMock()
        camera.read.return_value = None
        camera.running = False
        camera.status = 'Camera 1 could not open; retrying.'
        with (patch.object(main.pygame, 'init'),
              patch.object(main.pygame, 'quit'),
              patch.object(main.pygame.display, 'set_caption'),
              patch.object(main.pygame.display, 'flip'),
              patch.object(main.pygame.event, 'get', side_effect=[[], [pygame.event.Event(pygame.QUIT)]]),
              patch.object(main.pygame.time, 'Clock'),
              patch.object(main, 'open_window'),
              patch.object(main, 'Renderer') as renderer,
              patch.object(main, 'Sounds'),
              patch.object(main, 'Camera', return_value=camera),
              patch.object(main, 'HeadTracker'),
              patch.object(main, 'Calibration'),
              patch.object(main, 'Teacher') as teacher,
              patch.object(main, 'Game') as game):
            main.main()
        renderer.return_value.draw_camera_wait.assert_called_once()
        teacher.return_value.update.assert_not_called()
        game.return_value.update.assert_not_called()
        camera.release.assert_called_once()

    def test_tracker_initialization_error_still_releases_the_camera(self):
        camera = MagicMock()
        with (patch.object(main.pygame, 'init'),
              patch.object(main.pygame, 'quit') as quit_game,
              patch.object(main.pygame.display, 'set_caption'),
              patch.object(main.pygame.time, 'Clock'),
              patch.object(main, 'open_window'),
              patch.object(main, 'Renderer'),
              patch.object(main, 'Sounds'),
              patch.object(main, 'Camera', return_value=camera),
              patch.object(main, 'HeadTracker', side_effect=RuntimeError('model failed'))):
            with self.assertRaisesRegex(RuntimeError, 'model failed'):
                main.main()
        camera.release.assert_called_once()
        quit_game.assert_called_once()


if __name__ == "__main__":
    unittest.main()
