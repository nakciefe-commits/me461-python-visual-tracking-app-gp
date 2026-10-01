"""
Sound effects.

For the demo the sounds are made in code (a sound is just a list of numbers
describing the speaker's position over time), so no sound files are needed.
Later, files in assets/sounds/ will replace them.

If the computer has no working sound device, the game keeps running silently.
"""

import numpy as np
import pygame

SAMPLE_RATE = 44100   # numbers per second of sound
VOLUME = 0.4          # 0.0-1.0, for all generated sounds


def sine(freq, duration, fade=True):
    """A pure tone. fade=True makes it die away instead of stopping abruptly."""
    t = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    wave = np.sin(2 * np.pi * freq * t)
    if fade:
        wave *= np.linspace(1.0, 0.0, len(t)) ** 2
    return wave


def square(freq, duration):
    """A harsh 'buzz' tone."""
    return np.sign(sine(freq, duration, fade=False)) * 0.6


def sweep(start_freq, end_freq, duration):
    """A tone that slides from one pitch to another."""
    t = np.arange(int(SAMPLE_RATE * duration)) / SAMPLE_RATE
    freq = np.linspace(start_freq, end_freq, len(t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase) * np.linspace(1.0, 0.0, len(t))


def generated_sounds():
    """name -> wave (numpy array of floats from -1 to 1)."""
    return {
        "tick": sine(1500, 0.03),
        "answer": sine(880, 0.25),
        "warning": square(150, 0.4),
        "won": np.concatenate([sine(f, 0.15) for f in (523, 659, 784)]),
        "lost": sweep(400, 150, 0.8),
    }


class Sounds:
    def __init__(self):
        self.sounds = {}
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1)
        except pygame.error as error:
            print(f"No sound ({error}). The game will run silently.")
            self.enabled = False
            return
        self.enabled = True

        # The mixer may have opened in stereo even though we asked for mono.
        channels = pygame.mixer.get_init()[2]
        for name, wave in generated_sounds().items():
            samples = (wave * VOLUME * 32767).astype(np.int16)  # 16-bit numbers
            if channels == 2:
                samples = np.column_stack([samples, samples])   # same on both speakers
            self.sounds[name] = pygame.sndarray.make_sound(np.ascontiguousarray(samples))

    def play(self, name):
        """Play a sound once. Unknown names and missing audio do nothing."""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def loop(self, name):
        """Start a looping sound (used from Step 5 on)."""

    def stop(self, name):
        """Stop a looping sound (used from Step 5 on)."""
