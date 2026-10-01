"""
Sound effects.

For the demo the sounds are made in code: a sound is just a long list of
numbers telling the speaker where to be at each moment, and a sine wave of
those numbers is a beep. Later, files in assets/sounds/ will replace them.

If the computer has no working sound device, the game keeps running silently.
"""

import numpy as np
import pygame

SAMPLE_RATE = 44100   # numbers per second of sound
VOLUME = 0.4          # 0.0-1.0


def tone(freq, seconds, fade=True):
    """A beep at `freq` Hz. fade=True makes it die away instead of stopping abruptly."""
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    wave = np.sin(2 * np.pi * freq * t)
    if fade:
        wave *= np.linspace(1.0, 0.0, len(t))
    return wave


def make_waves():
    """Sound name -> wave. Names match the events from game.update()."""
    return {
        "tick": tone(1500, 0.03),                                         # short click
        "answer": tone(880, 0.25),                                        # ding
        "warning": tone(150, 0.4, fade=False),                            # low buzz
        "won": np.concatenate([tone(f, 0.15) for f in (523, 659, 784)]),  # rising notes
        "lost": np.concatenate([tone(f, 0.25) for f in (400, 300, 200)]), # falling notes
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

    def play(self, name):
        """Play a sound once. Unknown names (and no sound device) do nothing."""
        if name in self.sounds:
            self.sounds[name].play()
