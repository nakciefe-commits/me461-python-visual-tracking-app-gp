"""
Sound effects.

Most sounds are made in code: a sound is just a long list of numbers telling
the speaker where to be at each moment, and a sine wave of those numbers is a
beep. A sound listed in SOUND_FILES is loaded from assets/sounds/ instead,
replacing the beep of the same name.

If the computer has no working sound device, the game keeps running silently.
"""

import os

import numpy as np
import pygame

SAMPLE_RATE = 44100   # numbers per second of sound
VOLUME = 0.4          # 0.0-1.0

SOUND_FOLDER = os.path.join("assets", "sounds")
# Sound name -> file in SOUND_FOLDER. These replace the generated beeps.
SOUND_FILES = {
    "state:TURNING": "luigi-hmm.mp3",   # the teacher is about to look up: stop copying!
    "lost_caught": "mgs-alert-sound.mp3",     # game over: caught copying
    "lost_warnings": "mgs-alert-sound.mp3",   # game over: too many warnings
}


def tone(freq, seconds, fade=True):
    """A beep at `freq` Hz. fade=True makes it die away instead of stopping abruptly."""
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    wave = np.sin(2 * np.pi * freq * t)
    if fade:
        wave *= np.linspace(1.0, 0.0, len(t))
    return wave


def scribble(seconds):
    """A short scratchy noise, like a pencil: random numbers instead of a sine wave."""
    noise = np.random.default_rng(0).uniform(-1.0, 1.0, int(SAMPLE_RATE * seconds))
    return 0.5 * noise * np.linspace(1.0, 0.0, len(noise))


def make_waves():
    """Sound name -> wave. Names match the events from game.update() and teacher.update()."""
    return {
        "tick": tone(1500, 0.03),                                         # short click
        "read": tone(880, 0.25),                                          # ding: neighbour's paper read
        "write": scribble(0.15),                                          # pencil on paper
        "warning": tone(150, 0.4, fade=False),                            # low buzz
        "won": np.concatenate([tone(f, 0.15) for f in (523, 659, 784)]),  # rising notes
        "lost_time": np.concatenate([tone(f, 0.25) for f in (400, 300, 200)]),  # falling notes
        # Seen copying: a fast rising alarm, "look away now!"
        "spotted": np.concatenate([tone(f, 0.07, fade=False) for f in (600, 900, 1200, 1500)]),
        # The teacher: "state:..." events come from teacher.update().
        # TURNING is the danger cue, so it is loud and clear: two quick high beeps
        # (replaced by a file in SOUND_FILES, if it loads).
        "state:TURNING": np.concatenate([tone(1200, 0.08), tone(0, 0.05), tone(1200, 0.08)]),
    }


class Sounds:
    def __init__(self):
        self.sounds = {}
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1)
        except pygame.error as error:
            print(f"No sound ({error}). The game will run silently.")
            return

        # The mixer may have opened in stereo even though we asked for mono.
        stereo = pygame.mixer.get_init()[2] == 2
        for name, wave in make_waves().items():
            samples = (wave * VOLUME * 32767).astype(np.int16)  # 16-bit numbers
            if stereo:
                samples = np.column_stack([samples, samples])   # same on both speakers
            self.sounds[name] = pygame.sndarray.make_sound(samples)

        for name, file_name in SOUND_FILES.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, file_name))
            except (pygame.error, FileNotFoundError) as error:
                # Missing or broken file: keep the beep instead.
                print(f"Could not load {file_name} ({error}); using a beep instead.")

    def play(self, name):
        """Play a sound once. Unknown names (and no sound device) do nothing."""
        if name in self.sounds:
            self.sounds[name].play()
