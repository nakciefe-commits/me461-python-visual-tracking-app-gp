"""
The characters the player can be (CHARACTERS in settings.py).

Each character bends a few rules, with an advantage and a price: the guy
with the cap fills the suspicion bar slower but it creeps up whenever he
is not looking at his paper; glasses read faster but see the classroom
blurry at first; the nerd has a joker but must hand in early; and so on.
Almost all of it is numbers that the rules already have (how fast a paper
gets sharp, how fast the bar fills, how long the teacher is busy), so a
character is only data: rules() fills in what a character does not list.

The energy drink addict is the only one with a state of his own (Energy
below): every exam a coin toss gives him a sugar rush (the world runs
slower for him) or a crash (sleepy spells, when he reads slowly).

No pygame and no camera here, so it is tested on its own
(tests/test_character.py).
"""

from settings import CHARACTERS, DEFAULT_CHARACTER

RUSH, CRASH = "RUSH", "CRASH"   # the energy drink addict's two kinds of day

# What every rule is for a character that does not mention it: no change.
# (What each one means is explained above CHARACTERS in settings.py.)
DEFAULTS = {
    "focus_speed": 1.0, "seen_speed": 1.0, "stare_speed": 1.0, "creep_time": None,
    "screen_focus_time": 0.0, "screen_blur_start": 1.0,
    "jokers": 0, "hand_in_share": 0.0, "late_penalty": 0,
    "busy_times": 1.0, "watching_times": 1.0,
    "both_know": False,
    "energy": False, "rush_chance": 0.5, "rush_chance_drop": 0.0, "rush_speed": 1.0, "crash_every": (10.0, 10.0), "crash_time": 0.0,
    "crash_focus": 1.0,
}


def names():
    """Every character's key, in the order of the character screen."""
    return list(CHARACTERS)


def rules(name=DEFAULT_CHARACTER):
    """The character's rules: its entry in CHARACTERS, with DEFAULTS for the rest."""
    merged = dict(DEFAULTS)
    merged.update(CHARACTERS[name])
    return merged


def screen_clarity(character_rules, look_time):
    """
    How sharp the classroom is (0 = very blurry, 1 = sharp) after looking
    at the screen for look_time seconds. Only glasses make it blurry.
    """
    focus_time = character_rules["screen_focus_time"]
    if focus_time <= 0:
        return 1.0
    start = character_rules["screen_blur_start"]
    return start + (1 - start) * min(1.0, look_time / focus_time)


def rush_chance(character_rules, rushes_before):
    """The chance (0..1) of a sugar rush after `rushes_before` rushes in this run."""
    chance = character_rules["rush_chance"] - character_rules["rush_chance_drop"] * rushes_before
    return max(0.0, chance)


class Energy:
    """
    The energy drink addict's day, tossed at the start of each exam:
      RUSH   the world (the teacher, the clock, the suspicion bar) runs at
             rush_speed, but your eyes do not: you read at the normal speed.
      CRASH  every crash_every seconds you get sleepy for crash_time
             seconds: reading runs at crash_focus (your eyelids close).
    """

    def __init__(self, rng, character_rules, rushes_before=0):
        self.rules = character_rules
        self.rng = rng
        # The coin is not quite fair: every sugar rush already had in this
        # run (rushes_before) makes another one less likely.
        self.day = RUSH if rng.random() < rush_chance(character_rules, rushes_before) else CRASH
        self.sleepy_left = 0.0   # seconds of the sleepy spell still to come; 0 = awake
        self.next_spell = self.wait()

    def wait(self):
        """Seconds until the next sleepy spell."""
        return self.rng.uniform(*self.rules["crash_every"])

    def is_sleepy(self):
        return self.sleepy_left > 0

    def world_speed(self):
        """How fast the world runs for you: below 1 in a sugar rush."""
        return self.rules["rush_speed"] if self.day == RUSH else 1.0

    def focus_speed(self):
        """How fast you read right now: slower while sleepy."""
        return self.rules["crash_focus"] if self.is_sleepy() else 1.0

    def update(self, dt):
        """Move on by dt seconds. Returns ["sleepy"] when a spell starts, ["awake"] when it ends."""
        if self.day != CRASH:
            return []
        if self.is_sleepy():
            self.sleepy_left = max(0.0, self.sleepy_left - dt)
            if not self.is_sleepy():
                self.next_spell = self.wait()
                return ["awake"]
            return []
        self.next_spell -= dt
        if self.next_spell <= 0:
            self.sleepy_left = self.rules["crash_time"]
            return ["sleepy"]
        return []
