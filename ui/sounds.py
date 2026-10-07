"""
Sound effects.

Most sounds are made in code: a sound is just a long list of numbers telling
the speaker where to be at each moment, and a sine wave of those numbers is a
beep. A sound listed in SOUND_FILES is loaded from assets/sounds/ instead,
replacing the beep of the same name.

The background music (MUSIC_FILE) is different: it is long, so pygame plays
it straight from the file ("streaming", pygame.mixer.music) instead of
loading it all, over and over. It plays only in the menus and fades out
before an exam (main.py says when, see music()), and back in after it.

If the computer has no working sound device, or a file is missing, the game
keeps running (silently, or with a beep instead).
"""

import os

import numpy as np
import pygame

from settings import MUSIC_VOLUME, MUSIC_FADE_TIME

SAMPLE_RATE = 44100   # numbers per second of sound
VOLUME = 0.4          # 0.0-1.0

SOUND_FOLDER = os.path.join("assets", "sounds")
# Sound name -> file in SOUND_FOLDER. These replace the generated beeps.
SOUND_FILES = {
    "state:TURNING": "luigi-hmm.mp3",   # the teacher is about to look up: stop copying!
    "lost_caught": "mgs-alert-sound.mp3",     # game over: caught copying
    "lost_warnings": "mgs-alert-sound.mp3",   # game over: too many warnings
    "nooo": "noooo.mp3",                      # the game over screen (optional file)
}
MUSIC_FILE = "theme.mp3"   # the background music in SOUND_FOLDER (optional), looped


def tone(freq, seconds, fade=True):
    """A beep at `freq` Hz. fade=True makes it die away instead of stopping abruptly."""
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    wave = np.sin(2 * np.pi * freq * t)
    if fade:
        wave *= np.linspace(1.0, 0.0, len(t))
    return wave


def synth(freq, seconds):
    """
    An 80s synth note for the buttons: a sine with some of its odd harmonics
    (3x and 5x the frequency) added, which sounds brighter and "buzzier",
    like an old synthesizer. A very short start (no click) and a quick decay.
    """
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    wave = (np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * 3 * freq * t)
            + 0.15 * np.sin(2 * np.pi * 5 * freq * t)) / 1.5
    attack = np.minimum(1.0, t / 0.004)              # 4 ms fade in
    decay = np.exp(-t / (seconds / 3))               # dies away quickly
    return wave * attack * decay


def scribble(seconds):
    """A short scratchy noise, like a pencil: random numbers instead of a sine wave."""
    noise = np.random.default_rng(0).uniform(-1.0, 1.0, int(SAMPLE_RATE * seconds))
    return 0.5 * noise * np.linspace(1.0, 0.0, len(noise))


def rip(seconds):
    """
    Paper tearing: noise in short crackly bursts that get louder, then stop.
    Each 10 ms chunk gets a random loudness, which makes it crackle.
    """
    rng = np.random.default_rng(1)
    count = int(SAMPLE_RATE * seconds)
    noise = rng.uniform(-1.0, 1.0, count)
    chunk = SAMPLE_RATE // 100                          # 10 ms
    crackle = np.repeat(rng.uniform(0.3, 1.0, count // chunk + 1), chunk)[:count]
    return noise * crackle * np.linspace(0.4, 1.0, count)


def nooo(seconds):
    """
    A cartoon "nooooo": a low voice-like sound sliding down in pitch with a
    wobble (vibrato). Made of a few harmonics, loudest low ones, so it sounds
    more like an "o" than a beep.
    """
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    freq = np.linspace(260, 110, len(t)) * (1 + 0.03 * np.sin(2 * np.pi * 6 * t))
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE   # adding up the frequency = the phase
    wave = sum(np.sin(k * phase) / k for k in range(1, 6))
    return 0.6 * wave * np.minimum(1.0, 6 * (1 - t / seconds))   # fades out at the end


TALLY_TICKS = 16          # how many tally ticks are made (more parts reuse the highest one)
TALLY_BASE_PITCH = 440    # Hz, the first tally tick; each next one is a semitone higher


def tally_sound(i):
    """The name of the tick for the i-th part of the tally (0 = first)."""
    return f"tally{min(i, TALLY_TICKS - 1)}"


def make_waves():
    """Sound name -> wave. Names match the events from game.update() and teacher.update()."""
    return {
        "read": tone(880, 0.25),                                          # ding: neighbour's paper read
        "write": scribble(0.15),                                          # pencil on paper
        "warning": tone(150, 0.4, fade=False),                            # low buzz
        "won": np.concatenate([tone(f, 0.15) for f in (523, 659, 784)]),  # rising notes
        "close_call": np.concatenate([tone(f, 0.08) for f in (660, 990)]),  # phew: got away
        "time_up": np.concatenate([tone(f, 0.25) for f in (400, 300, 200)]),  # falling notes: the paper is collected
        # Seen copying: a fast rising alarm, "look away now!"
        "spotted": np.concatenate([tone(f, 0.07, fade=False) for f in (600, 900, 1200, 1500)]),
        # The teacher: "state:..." events come from teacher.update().
        # TURNING is the danger cue, so it is loud and clear: two quick high beeps
        # (replaced by a file in SOUND_FILES, if it loads).
        "state:TURNING": np.concatenate([tone(1200, 0.08), tone(0, 0.05), tone(1200, 0.08)]),
        # Buttons, as 80s synth notes: a short tick when the selection moves,
        # three notes up when something is chosen, two notes down for back.
        "menu_move": 0.6 * synth(1320, 0.05) + 0.2 * scribble(0.05)[:int(SAMPLE_RATE * 0.05)],
        "menu_select": np.concatenate([synth(f, 0.07) for f in (659, 988)] + [synth(1319, 0.22)]),
        "menu_back": np.concatenate([synth(784, 0.07), synth(523, 0.16)]),
        # The gossip slot machine: a click per mood rolling past, a ding when it stops.
        "slot_tick": 0.5 * synth(1760, 0.03),
        "slot_stop": sum(synth(f, 0.6) for f in (784, 988, 1175)) / 2,
        # Reading the right neighbour first: a quick sparkle.
        "sharp_eye": np.concatenate([synth(f, 0.06) for f in (1319, 1568, 2093)]),
        # Scenes: the teacher tears up your exam; the game over screen.
        "rip": rip(0.45),
        # The disclaimer notice: typewriter keys, the signature, the stamp.
        "type": 0.5 * tone(2600, 0.012, fade=True),
        "sign": scribble(0.65),
        "stamp": np.concatenate([0.9 * tone(70, 0.28) + 0.4 * scribble(0.28)]),
        "nooo": nooo(1.8),
        # The score tally on the end screen (tally.py): a chip-like tick per
        # part, a semitone higher each time like in Balatro, then a chord.
        **{f"tally{i}": tone(TALLY_BASE_PITCH * 2 ** (i / 12), 0.09) for i in range(TALLY_TICKS)},
        "tally_done": sum(tone(f, 0.5) for f in (523, 659, 784)) / 3,
        # A new top score: a fast run up the notes, then a big chord.
        "new_top": np.concatenate([tone(f, 0.07) for f in (523, 659, 784, 1047, 1319)]
                                  + [sum(tone(f, 0.8) for f in (523, 784, 1047, 1319)) / 4]),
    }


class Sounds:
    def __init__(self):
        self.sounds = {}
        self.muted = False   # the settings menu can turn sound off (the music too)
        self.has_music = False
        self.music_volume = 0.0   # 0..1, the music's volume right now (it fades)
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
            if not os.path.exists(os.path.join(SOUND_FOLDER, file_name)):
                continue   # not added (yet): keep the beep, nothing to complain about
            try:
                self.sounds[name] = pygame.mixer.Sound(os.path.join(SOUND_FOLDER, file_name))
            except (pygame.error, FileNotFoundError) as error:
                # Broken file: keep the beep instead.
                print(f"Could not load {file_name} ({error}); using a beep instead.")

    def play(self, name):
        """Play a sound once. Unknown names, no sound device or muted: nothing."""
        if name in self.sounds and not self.muted:
            self.sounds[name].play()

    def start_music(self):
        """Start the background music, looping forever. No file or no sound device: nothing."""
        path = os.path.join(SOUND_FOLDER, MUSIC_FILE)
        if not pygame.mixer.get_init() or not os.path.exists(path):
            return
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.0)   # music() fades it in
            pygame.mixer.music.play(loops=-1)    # -1 = loop forever
            self.has_music = True
        except pygame.error as error:
            print(f"Could not play {MUSIC_FILE} ({error}); no music.")

    def music(self, on, dt):
        """
        Call every frame: move the music's volume towards where it should be
        (MUSIC_VOLUME when `on`, silent when not or when muted), a little
        each frame, so it fades in and out over MUSIC_FADE_TIME.
        """
        if not self.has_music:
            return
        target = MUSIC_VOLUME if on and not self.muted else 0.0
        step = MUSIC_VOLUME * dt / MUSIC_FADE_TIME   # how far the volume may move this frame
        self.music_volume = min(target, self.music_volume + step) if target > self.music_volume \
            else max(target, self.music_volume - step)
        pygame.mixer.music.set_volume(self.music_volume)
