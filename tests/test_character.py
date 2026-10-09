"""Tests for the characters (logic/character.py and how game.py uses them)."""

import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from logic.character import neighbour_letter, rules, names, screen_clarity, Energy, RUSH, CRASH, DEFAULTS, rush_chance
from logic.run import Run
from logic.exam_paper import UNKNOWN
from logic.game import Game, WON
from logic.teacher import Teacher, BUSY, WATCHING
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (SCORE_TIME_BONUS, PRACTICE_QUIZ, CHARACTERS, DEFAULT_CHARACTER, PAPER_FOCUS_TIME, CAUGHT_TIME, EXAM_TIME,
                      TEACHER_DURATIONS)

DT = 0.125   # adds up exactly in floating point


def run(game, direction, seconds, teacher=None):
    """Call update() for `seconds` of game time; return all events."""
    events = []
    for _ in range(math.ceil(seconds / DT - 1e-9)):
        events += game.update(direction, DT, teacher)
    return events


class AlwaysWatching:
    """A stand-in teacher who always watches the class."""

    def is_watching(self):
        return True

    def is_facing_class(self):
        return True


class AlwaysBusy:
    """A stand-in teacher who never looks up."""

    def is_watching(self):
        return False

    def is_facing_class(self):
        return False


def game_as(character, seed=1):
    return Game(random.Random(seed), character=character)


class RulesTests(unittest.TestCase):
    def test_every_character_has_its_texts(self):
        for name in names():
            entry = CHARACTERS[name]
            for key in ("name", "tagline", "plus", "minus"):
                self.assertIn(key, entry, name)

    def test_only_known_rules(self):
        # A typo in settings.py ("seen_sped") would silently do nothing.
        texts = {"name", "tagline", "plus", "minus"}
        for name in names():
            for key in CHARACTERS[name]:
                self.assertTrue(key in DEFAULTS or key in texts, f"{name}: unknown rule {key}")

    def test_plain_character_changes_nothing(self):
        self.assertEqual(rules(DEFAULT_CHARACTER), {**DEFAULTS, **CHARACTERS[DEFAULT_CHARACTER]})
        for key, value in DEFAULTS.items():
            self.assertEqual(rules(DEFAULT_CHARACTER)[key], value)


class CapTests(unittest.TestCase):
    def test_bar_creeps_up_when_not_looking_at_the_paper(self):
        game = game_as("cap")
        run(game, SCREEN, 4, AlwaysBusy())
        self.assertAlmostEqual(game.suspicion.level, 4 / CHARACTERS["cap"]["creep_time"])

    def test_looking_down_still_drains(self):
        game = game_as("cap")
        run(game, SCREEN, 4, AlwaysBusy())
        before = game.suspicion.level
        run(game, DOWN, 1, AlwaysBusy())
        self.assertLess(game.suspicion.level, before)

    def test_being_seen_fills_slower(self):
        plain, cap = game_as("npc"), game_as("cap")
        for game in (plain, cap):
            run(game, LEFT, CAUGHT_TIME / 2, AlwaysWatching())
        self.assertLess(cap.suspicion.level, plain.suspicion.level)


class GlassesTests(unittest.TestCase):
    def test_reads_faster(self):
        game = game_as("glasses")
        speed = CHARACTERS["glasses"]["focus_speed"]
        events = run(game, LEFT, PAPER_FOCUS_TIME / speed + DT)
        self.assertIn("read", events)
        plain = game_as("npc")
        self.assertNotIn("read", run(plain, LEFT, PAPER_FOCUS_TIME / speed - DT))

    def test_classroom_needs_to_get_sharp(self):
        glasses = rules("glasses")
        self.assertAlmostEqual(screen_clarity(glasses, 0), glasses["screen_blur_start"])
        self.assertEqual(screen_clarity(glasses, glasses["screen_focus_time"]), 1.0)
        self.assertEqual(screen_clarity(rules("npc"), 0), 1.0)


class NerdTests(unittest.TestCase):
    def test_joker_writes_the_right_answer_once(self):
        game = game_as("nerd")
        right = game.paper.right_letters[0]
        self.assertEqual(game.use_joker(SCREEN), [])   # only looking at your paper
        events = game.use_joker(DOWN)
        self.assertIn("joker", events)
        self.assertEqual(game.paper.written, [right])
        self.assertEqual(game.use_joker(DOWN), [])     # no jokers left
        self.assertEqual(game_as("npc").use_joker(DOWN), [])

    def test_late_hand_in_costs_points(self):
        game = game_as("nerd")
        late = EXAM_TIME - game.deadline() + 1
        run(game, DOWN, late)
        self.assertTrue(game.missed_deadline)
        while game.state != WON:
            game.write("A", DOWN)
        self.assertIn(("NERD WAS LATE", -CHARACTERS["nerd"]["late_penalty"]), game.score_parts())

    def test_early_bonus_counts_from_the_deadline(self):
        share = CHARACTERS["nerd"]["hand_in_share"]
        for left_share, bonus in ((share, 0), ((1 + share) / 2, SCORE_TIME_BONUS // 2)):
            game = game_as("nerd")
            game.time_left = EXAM_TIME * left_share
            while game.state != WON:
                game.write("A", DOWN)
            parts = dict(game.score_parts())
            self.assertAlmostEqual(parts.get("EARLY BONUS", 0), bonus, delta=1)
            self.assertNotIn("NERD WAS LATE", parts)

    def test_early_hand_in_is_fine(self):
        game = game_as("nerd")
        while game.state != WON:
            game.write("A", DOWN)
        self.assertNotIn("NERD WAS LATE", [name for name, _ in game.score_parts()])


class EnergyTests(unittest.TestCase):
    def energy_game(self, day):
        """A game with the energy drink addict on that kind of day (the coin toss is random)."""
        for seed in range(100):
            game = game_as("energy", seed)
            if game.energy.day == day:
                return game
        self.fail(f"no seed gives {day}")

    def test_both_days_happen(self):
        days = {Energy(random.Random(seed), rules("energy")).day for seed in range(50)}
        self.assertEqual(days, {RUSH, CRASH})

    def test_rush_slows_the_clock_not_the_eyes(self):
        game = self.energy_game(RUSH)
        run(game, DOWN, 4)
        self.assertAlmostEqual(game.time_left, EXAM_TIME - 4 * CHARACTERS["energy"]["rush_speed"])
        self.assertIn("read", run(game, LEFT, PAPER_FOCUS_TIME))

    def test_crash_brings_sleepy_spells(self):
        game = self.energy_game(CRASH)
        longest_wait = CHARACTERS["energy"]["crash_every"][1]
        # Step until the spell starts (the wait is random, at most longest_wait).
        events = []
        for _ in range(math.ceil(longest_wait / DT) + 1):
            events += game.update(DOWN, DT)
            if "sleepy" in events:
                break
        self.assertIn("sleepy", events)
        self.assertTrue(game.is_sleepy())
        self.assertAlmostEqual(game.focus_speed(), CHARACTERS["energy"]["crash_focus"])
        events = run(game, DOWN, CHARACTERS["energy"]["crash_time"] + DT)
        self.assertIn("awake", events)
        self.assertFalse(game.is_sleepy())


class RushChanceTests(unittest.TestCase):
    def test_each_rush_makes_the_next_less_likely(self):
        energy = rules("energy")
        first = rush_chance(energy, 0)
        self.assertEqual(first, energy["rush_chance"])
        self.assertAlmostEqual(rush_chance(energy, 1), first - energy["rush_chance_drop"])
        self.assertGreaterEqual(rush_chance(energy, 100), 0.0)

    def test_run_counts_its_rushes(self):
        run = Run(random.Random(4), character="energy")
        rushes = 0
        for _ in range(3):
            game = run.new_game()
            self.assertEqual(game.rushes_before, rushes)
            rushes += game.energy.day == RUSH
            while game.state != WON:
                game.write("A", DOWN)
            run.finish_quiz(game)
        self.assertEqual(run.rushes(), rushes)


class PracticeEaseTests(unittest.TestCase):
    def test_practice_is_easier(self):
        ease = PRACTICE_QUIZ["ease"]
        practice = Run(random.Random(1), practice=True).new_game()
        self.assertEqual(practice.ease, ease)
        self.assertAlmostEqual(practice.focus_speed(), 1 / ease)
        plain = game_as("npc")
        for game in (practice, plain):
            run(game, LEFT, CAUGHT_TIME / 2, AlwaysWatching())
        self.assertAlmostEqual(practice.suspicion.level, plain.suspicion.level * ease)


def teacher_as(character):
    """A teacher with the character's busy and watching times (as main.py sets them)."""
    character_rules = rules(character)
    teacher = Teacher(random.Random(1))
    teacher.set_mood(None, character_rules["busy_times"], character_rules["watching_times"])
    return teacher


class FrontRowTests(unittest.TestCase):
    def test_teacher_checks_less_often_but_longer(self):
        frontrow = rules("frontrow")
        teacher = teacher_as("frontrow")
        self.assertEqual(teacher.durations[BUSY],
                         tuple(t * frontrow["busy_times"] for t in TEACHER_DURATIONS[BUSY]))
        self.assertEqual(teacher.durations[WATCHING],
                         tuple(t * frontrow["watching_times"] for t in TEACHER_DURATIONS[WATCHING]))


class VeteranTests(unittest.TestCase):
    def test_shorter_stares(self):
        veteran = rules("veteran")
        self.assertLess(veteran["watching_times"], 1)
        self.assertEqual(teacher_as("veteran").durations[WATCHING],
                         tuple(t * veteran["watching_times"] for t in TEACHER_DURATIONS[WATCHING]))

    def test_seen_faster(self):
        plain, veteran = game_as("npc"), game_as("veteran")
        for game in (plain, veteran):
            run(game, LEFT, CAUGHT_TIME / 2, AlwaysWatching())
        self.assertGreater(veteran.suspicion.level, plain.suspicion.level)


class NotMeTests(unittest.TestCase):
    def test_staring_fills_slower(self):
        plain, notme = game_as("npc"), game_as("notme")
        for game in (plain, notme):
            run(game, SCREEN, 2, AlwaysWatching())
        self.assertGreater(plain.suspicion.level, 0)
        self.assertLess(notme.suspicion.level, plain.suspicion.level)

    def test_answers_are_greek(self):
        notme = rules("notme")
        self.assertEqual([neighbour_letter(notme, letter) for letter in "ABCD"], ["α", "β", "γ", "δ"])
        self.assertEqual(neighbour_letter(notme, UNKNOWN), UNKNOWN)   # "?" is "?" in every language
        self.assertEqual(neighbour_letter(rules("npc"), "B"), "B")

    def test_reads_at_the_normal_speed(self):
        self.assertIn("read", run(game_as("notme"), LEFT, PAPER_FOCUS_TIME + DT))


class AskerTests(unittest.TestCase):
    def test_teacher_busy_longer(self):
        asker = rules("asker")
        self.assertGreater(asker["busy_times"], 1)
        self.assertEqual(teacher_as("asker").durations[BUSY],
                         tuple(t * asker["busy_times"] for t in TEACHER_DURATIONS[BUSY]))

    def test_bar_creeps_up_when_not_looking_at_the_paper(self):
        game = game_as("asker")
        run(game, SCREEN, 4, AlwaysBusy())
        self.assertAlmostEqual(game.suspicion.level, 4 / CHARACTERS["asker"]["creep_time"])


class LazyTests(unittest.TestCase):
    def test_both_neighbours_know(self):
        game = game_as("lazy")
        for side in (LEFT, RIGHT):
            self.assertEqual(game.paper.says(side), game.paper.right_letters[0])
        self.assertNotEqual(game_as("npc").paper.says(LEFT), game_as("npc").paper.says(RIGHT))

    def test_no_sharp_eye(self):
        game = game_as("lazy")
        events = run(game, LEFT, PAPER_FOCUS_TIME)
        self.assertIn("read", events)
        self.assertNotIn("sharp_eye", events)
        self.assertTrue(game.knows_answer())

    def test_alarmed_faster(self):
        plain, lazy = game_as("npc"), game_as("lazy")
        for game in (plain, lazy):
            run(game, LEFT, CAUGHT_TIME / 2, AlwaysWatching())
        self.assertGreater(lazy.suspicion.level, plain.suspicion.level)


if __name__ == "__main__":
    unittest.main()
