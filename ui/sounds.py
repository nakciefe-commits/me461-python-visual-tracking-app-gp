"""
Sound effects.

Most sounds are made in code: a sound is just a long list of numbers telling
the speaker where to be at each moment, and a sine wave of those numbers is a
beep. A sound listed in SOUND_FILES is loaded from assets/sounds/ instead,
replacing the beep of the same name.

The music (MUSIC_FILES) is different: it is long, so pygame plays it
straight from the file ("streaming", pygame.mixer.music) instead of
loading it all. pygame can stream only one file at a time, so there are
three tracks, "menu", "exam" and "character": main.py says which one
should play (see music()), and when it changes, the old one fades out and
the new one fades in from its beginning. The run intro is timed to its
music, so it does not wait for a fade: cut_to() starts it at once, and
music_position() says where in the song it is.

Under some sounds (the heartbeat of a razor close call) the music sounds
far away for a moment: the part of the song playing right now is made
muffled and echoing (far_away()) and played instead, while the real music
goes almost silent and then comes back.

A few sounds loop while something lasts (the chalk while the teacher
erases the board): main.py turns them on and off every frame with loop().

If the computer has no working sound device, or a file is missing, the game
keeps running (silently, or with a beep instead).
"""

import os

import numpy as np
import pygame

from settings import (MUSIC_VOLUME, EXAM_MUSIC_VOLUME, MUSIC_FADE_TIME, CHALK_VOLUME, LOOP_FADE_TIME,
                      EXAM_TITLE_TIME, HEARTBEAT_BPM, HEARTBEAT_TIME, HEARTBEAT_MUSIC_DUCK,
                      FAR_MUSIC_CUTOFF, FAR_MUSIC_ECHO, MUGSHOT_WRITE_TIME)

SAMPLE_RATE = 44100   # numbers per second of sound
VOLUME = 0.4          # 0.0-1.0

SOUND_FOLDER = os.path.join("assets", "sounds")
# Sound name -> file in SOUND_FOLDER. These replace the generated beeps.
SOUND_FILES = {
    "state:TURNING": "luigi-hmm.mp3",   # the teacher is about to look up: stop copying!
    "lost_caught": "mgs-alert-sound.mp3",     # game over: caught copying
    "lost_warnings": "mgs-alert-sound.mp3",   # game over: too many warnings
    "nooo": "noooo.mp3",                      # the game over screen (optional file)
    "chalk": "Erasing Chalk On Chalkboard Sound Effect.mp3",   # loops while he erases the board
    "footsteps": "footsteps.mp3",             # he walks to your desk / to the other place (optional file)
    "rip": "paper-rip.mp3",                   # he tears up your exam (optional file)
    "heartbeat": "heartbeat.mp3",             # a razor close call (optional file)
    "pen": "marker.mp3",                      # "GOT CAUGHT!" written on the mugshot (optional file)
    # The school bell on the title card before each exam.
    "bell": "School Bell Sound Effect (Download) - Soundspace Sound Effects (128k).mp3",
}
# Sounds played quieter than the rest, 0..1.
SOUND_VOLUMES = {"chalk": CHALK_VOLUME}
# Sounds cut to a fixed length (seconds), fading out at the end, so they
# end with what they go with: the bell lasts exactly as long as the title card.
SOUND_LENGTHS = {"bell": EXAM_TITLE_TIME, "heartbeat": HEARTBEAT_TIME, "pen": MUGSHOT_WRITE_TIME}
# Sounds under which the music sounds far away, for this many seconds.
SOUND_DUCKS = {"heartbeat": HEARTBEAT_TIME}
FAR_TRACKS = ("exam",)   # music tracks loaded whole too, so they can be made far away (short loops only)
CUT_FADE_TIME = 0.35   # seconds over which a cut sound fades out
MARKER_STROKES = 12    # strokes of the marker writing "GOT CAUGHT!" (about one per letter, and the underline)
# Music track -> file in SOUND_FOLDER (optional), looped while it plays.
MUSIC_FILES = {"menu": "theme.mp3", "exam": "thrilling.mp3",
               "character": "character_[cut_180sec].mp3"}   # the run intro and the character screen
MUSIC_VOLUMES = {"menu": MUSIC_VOLUME, "exam": EXAM_MUSIC_VOLUME, "character": MUSIC_VOLUME}


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


def marker(seconds, strokes):
    """
    A whiteboard marker writing fast: `strokes` quick strokes with short
    gaps. Each stroke is a soft hiss (the felt tip rubbing) plus the
    marker's squeak: a high note whose pitch wobbles as the hand moves.
    The last stroke is long (the angry underline).
    """
    rng = np.random.default_rng(2)
    # How long each stroke is: random, the last one three times as long.
    lengths = rng.uniform(0.6, 1.4, strokes)
    lengths[-1] *= 3
    lengths *= 0.75 * seconds / lengths.sum()   # strokes fill 3/4 of the time, gaps the rest
    gap = np.zeros(int(SAMPLE_RATE * 0.25 * seconds / strokes))
    parts = []
    for length in lengths:
        t = np.arange(int(SAMPLE_RATE * length)) / SAMPLE_RATE
        hiss = np.diff(rng.uniform(-1.0, 1.0, len(t) + 1))   # bright noise (high part only)
        pitch = rng.uniform(1700, 2600) + 300 * np.sin(2 * np.pi * rng.uniform(5, 9) * t)
        squeak = np.sin(2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE)   # cumsum: the pitch can change
        # Pressed down quickly, lifted at the end; the squeak comes and goes.
        shape = np.minimum(1.0, t / 0.01) * np.minimum(1.0, (length - t) / 0.02)
        squeak_level = 0.25 * (0.5 + 0.5 * np.sin(2 * np.pi * rng.uniform(2, 4) * t)) ** 2
        parts += [(0.35 * hiss + squeak_level * squeak) * shape, gap]
    return np.clip(np.concatenate(parts), -1.0, 1.0)


def tear(seconds, rng):
    """
    One pull of tearing paper: bright noise (each number minus the one
    before keeps only the high, hissy part), in crackly 5 ms chunks of
    random loudness, with sharp little clicks (the fibres snapping). It
    starts at once, gets louder as the tear speeds up, and stops sharply.
    """
    count = int(SAMPLE_RATE * seconds)
    noise = np.diff(rng.uniform(-1.0, 1.0, count + 1))   # high-pass: paper is bright
    chunk = SAMPLE_RATE // 200                           # 5 ms
    crackle = np.repeat(rng.uniform(0.2, 1.0, count // chunk + 1), chunk)[:count]
    clicks = (rng.random(count) < 0.004) * rng.uniform(1.0, 2.5, count)   # a few sharp snaps
    shape = np.minimum(1.0, np.linspace(0, 6, count)) * np.linspace(0.6, 1.0, count)
    return 0.5 * (noise * crackle + clicks * noise) * shape


def rip(seconds):
    """
    Tearing up an exam: two pulls (rrrip... rrrrip!), the second longer and
    louder, with a short gap; the paper being torn in half, then again.
    """
    rng = np.random.default_rng(1)
    first = 0.7 * tear(seconds * 0.4, rng)
    gap = np.zeros(int(SAMPLE_RATE * seconds * 0.12))
    second = tear(seconds * 0.48, rng)
    return np.clip(np.concatenate([first, gap, second]), -1.0, 1.0)


def step(seconds, rng):
    """One footstep: a low thud (a quickly falling low note) and a short scuff of noise."""
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    thud = np.sin(2 * np.pi * (90 - 300 * t) * t) * np.exp(-t / 0.03)   # heel on the floor
    scuff = rng.uniform(-1.0, 1.0, len(t)) * np.exp(-t / 0.015) * 0.3     # the shoe's sole
    return thud + scuff


def heart_thump(seconds, pitch):
    """
    One thump of a heart: a low note that falls fast and dies away. Pushed
    through tanh ("overdriven"), so it is hard and punchy, and the extra
    overtones make it heard on laptop speakers too, which play no deep bass.
    """
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    note = np.sin(2 * np.pi * (pitch - 250 * t) * t) * np.exp(-t / 0.05)
    return np.tanh(4 * note)


def heartbeat(bpm, seconds):
    """A pounding heart: "lub-DUB" at `bpm` beats per minute for `seconds`, a little louder each beat."""
    wave = np.zeros(int(SAMPLE_RATE * seconds))
    gap = int(SAMPLE_RATE * 60 / bpm)
    lub, dub = heart_thump(0.16, 75), 0.8 * heart_thump(0.12, 95)
    dub_at = int(gap * 0.3)   # the second, shorter thump comes soon after the first
    for start in range(0, len(wave) - dub_at - len(dub), gap):
        loud = 0.7 + 0.3 * start / len(wave)
        wave[start:start + len(lub)] += loud * lub
        wave[start + dub_at:start + dub_at + len(dub)] += loud * dub
    return np.clip(wave, -1.0, 1.0)


def boom(seconds):
    """
    A big explosion (the AA's show): a deep thump that falls and rings on,
    a burst of noise (the blast, darker as it dies away), overdriven so it hits.
    """
    rng = np.random.default_rng(4)
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    thump = np.sin(2 * np.pi * (60 - 40 * t) * t) * np.exp(-t / 0.35)
    noise = rng.uniform(-1.0, 1.0, len(t))
    # Averaging the noise with itself shifted takes the hiss away: a darker rumble.
    rumble = np.convolve(noise, np.ones(30) / 30, mode="same") * 4
    blast = (0.6 * noise * np.exp(-t / 0.06) + rumble * np.exp(-t / 0.5))
    return np.tanh(2.5 * (thump + blast)) * 0.95


def firework(seconds, seed):
    """
    One firework going off: a sharp pop, then a crackle of tiny snaps
    (random clicks that thin out). `seed` makes each one a little different.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    pop = rng.uniform(-1.0, 1.0, len(t)) * np.exp(-t / 0.025) + np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05)
    clicks = (rng.random(len(t)) < 0.003 * np.exp(-t / (seconds / 3))) * rng.uniform(0.3, 0.8, len(t))
    crackle = np.convolve(clicks, rng.uniform(-1.0, 1.0, 60), mode="same")   # each click a tiny snap
    return np.clip(0.9 * pop + 0.6 * crackle * (t > 0.08), -1.0, 1.0)


def far_away(samples, rate):
    """
    Music as if heard from far away, through a wall: the high notes cut
    (above FAR_MUSIC_CUTOFF) and a long echo added (FAR_MUSIC_ECHO). The
    echo is the music mixed with itself delayed by every amount at once,
    each a bit quieter (random noise that dies away = a big hall's echo).
    Done with the FFT, which makes this mixing fast. `samples`: floats,
    one column per speaker; the result is longer by the echo.
    """
    rng = np.random.default_rng(3)
    echo_count = int(rate * FAR_MUSIC_ECHO)
    t = np.arange(echo_count) / rate
    echo = rng.uniform(-1.0, 1.0, echo_count) * np.exp(-t / (FAR_MUSIC_ECHO / 7))   # 1/1000 at the end
    echo[0] = 1.0   # a little of the music itself too
    size = len(samples) + echo_count
    fft_size = 1 << (size - 1).bit_length()   # a power of two: the FFT is much faster then
    freqs = np.fft.rfftfreq(fft_size, 1 / rate)
    muffle = 1 / (1 + (freqs / FAR_MUSIC_CUTOFF) ** 4)   # lets the low notes through, not the high
    columns = samples.reshape(len(samples), -1)
    wet = np.fft.irfft(np.fft.rfft(columns, fft_size, axis=0) * (np.fft.rfft(echo, fft_size) * muffle)[:, None],
                       fft_size, axis=0)[:size]
    # As loud as the music was, at most.
    wet *= np.abs(columns).max() / max(np.abs(wet).max(), 1e-9)
    return wet.reshape((size,) + samples.shape[1:])


def footsteps(count, every):
    """`count` footsteps, one every `every` seconds, a little louder each (coming closer)."""
    rng = np.random.default_rng(2)
    gap = int(SAMPLE_RATE * every)
    wave = np.zeros(gap * count)
    for i in range(count):
        one = step(min(every, 0.15), rng) * (0.5 + 0.5 * (i + 1) / count)
        wave[i * gap:i * gap + len(one)] += one
    return 0.9 * wave


def chalk(seconds):
    """
    Stand-in for the chalk file: soft scratchy strokes of noise going back
    and forth (about 3 a second), made to loop without a click.
    """
    rng = np.random.default_rng(3)
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    noise = np.diff(rng.uniform(-1.0, 1.0, len(t) + 1))
    strokes = np.abs(np.sin(2 * np.pi * 1.5 * t))   # whole number of strokes: loops cleanly
    return 0.4 * noise * strokes


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


def school_bell(seconds):
    """
    Stand-in for the bell file: an electric school bell, a bright metal ring
    (a high note and its clangy overtone) hammered 25 times a second, which
    fades out at the end.
    """
    t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
    ring = np.sin(2 * np.pi * 1150 * t) + 0.5 * np.sin(2 * np.pi * 2730 * t)
    hammer = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * 12.5 * t))   # 25 hits a second
    return 0.45 * ring * hammer * fade_out(len(t), int(SAMPLE_RATE * CUT_FADE_TIME))


def fade_out(count, fade_count):
    """count numbers: 1, 1, 1, ... then down to 0 over the last fade_count (multiply a sound by it)."""
    shape = np.ones(count)
    fade_count = min(fade_count, count)
    if fade_count > 0:
        shape[count - fade_count:] = np.linspace(1.0, 0.0, fade_count)
    return shape


def cut_sound(samples, count, fade_count):
    """
    The first `count` samples of a sound (one number per sample, or one row
    of two for stereo), fading out over the last `fade_count`. A shorter
    sound is padded with silence.
    """
    cut = np.zeros((count,) + samples.shape[1:], dtype=np.float64)
    length = min(count, len(samples))
    cut[:length] = samples[:length]
    shape = fade_out(count, fade_count)
    return cut * (shape[:, None] if cut.ndim == 2 else shape)


TALLY_TICKS = 16          # how many tally ticks are made (more parts reuse the highest one)
TALLY_BASE_PITCH = 440    # Hz, the first tally tick; each next one is a semitone higher


def tally_sound(i):
    """The name of the tick for the i-th part of the tally (0 = first)."""
    return f"tally{min(i, TALLY_TICKS - 1)}"


# The game over chat's talking blips (like in Animal Crossing): each logo
# has its own voice, Gemini higher than Claude; a few pitches each, picked
# at random, so the talking sounds less like a machine gun.
TALK_PITCHES = {"GEMINI": (784, 880, 698), "CLAUDE": (523, 587, 466)}   # Hz


def talk_sound(who, i):
    """The name of a talking blip: speaker `who` ("GEMINI" / "CLAUDE"), pitch number i."""
    return f"talk_{who}{i % len(TALK_PITCHES[who])}"


def make_waves():
    """Sound name -> wave. Names match the events from game.update() and teacher.update()."""
    return {
        "read": tone(880, 0.25),                                          # ding: neighbour's paper read
        "write": scribble(0.15),                                          # pencil on paper
        "warning": tone(150, 0.4, fade=False),                            # low buzz
        "won": np.concatenate([tone(f, 0.15) for f in (523, 659, 784)]),  # rising notes
        "close_call": np.concatenate([tone(f, 0.08) for f in (660, 990)]),  # phew: got away
        "heartbeat": heartbeat(HEARTBEAT_BPM, HEARTBEAT_TIME),           # ... but only just
        # An AA's show (logic/verdict.py): an explosion, then fireworks.
        "boom": boom(1.4),
        "firework": firework(0.9, 5),
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
        # The characters: the nerd's joker (a magic run up), the nerd too
        # slow (a sad "wah-wah"), the energy drink crash (a sleepy yawn down)
        # and waking up from it (a quick blip up).
        "joker": np.concatenate([synth(f, 0.05) for f in (784, 988, 1175, 1568, 1976)]),
        "nerd_late": np.concatenate([synth(392, 0.25), synth(370, 0.25), synth(349, 0.5)]),
        "sleepy": np.concatenate([tone(f, 0.12) for f in (440, 392, 349, 294, 262)]),
        "awake": np.concatenate([synth(f, 0.05) for f in (660, 990)]),
        # Reading the right neighbour first: a quick sparkle.
        "sharp_eye": np.concatenate([synth(f, 0.06) for f in (1319, 1568, 2093)]),
        # Scenes: the teacher tears up your exam; the game over screen.
        "rip": rip(0.9),
        "pen": marker(MUGSHOT_WRITE_TIME, MARKER_STROKES),   # "GOT CAUGHT!" on the mugshot
        "footsteps": footsteps(4, 0.2),     # he walks to your desk (about TEACHER_APPROACH_TIME)
        "chalk": chalk(2.0),                # replaced by the chalk file, if it loads
        # The disclaimer notice: typewriter keys, the signature, the stamp.
        "type": 0.5 * tone(2600, 0.012, fade=True),
        "sign": scribble(0.65),
        "stamp": np.concatenate([0.9 * tone(70, 0.28) + 0.4 * scribble(0.28)]),
        "nooo": nooo(1.8),
        "bell": school_bell(EXAM_TITLE_TIME),   # replaced by the bell file, if it loads
        # The chat bubbles typing: a very short soft synth blip per voice.
        **{talk_sound(who, i): 0.5 * synth(f, 0.045)
           for who, pitches in TALK_PITCHES.items() for i, f in enumerate(pitches)},
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
        self.has_music = False   # True once start_music() was called and there is a sound device
        self.track = None        # the music track loaded right now ("menu", "exam" or None)
        self.loops = {}          # looping sound name -> the channel it plays on
        self.music_volume = 0.0   # 0..1, the music's volume right now (it fades)
        self.duck_left = 0.0      # seconds the music stays quieter for (SOUND_DUCKS)
        self.track_samples = {}   # FAR_TRACKS track -> the whole song as numbers (for far_away())
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
        for name, seconds in SOUND_LENGTHS.items():
            if name in self.sounds:
                self.sounds[name] = self.cut(self.sounds[name], seconds)
        for name, volume in SOUND_VOLUMES.items():
            if name in self.sounds:
                self.sounds[name].set_volume(volume)

    @staticmethod
    def cut(sound, seconds):
        """The sound, `seconds` long (cut, or padded with silence), fading out at the end."""
        rate = pygame.mixer.get_init()[0]
        samples = pygame.sndarray.array(sound)
        cut = cut_sound(samples, int(rate * seconds), int(rate * CUT_FADE_TIME))
        return pygame.sndarray.make_sound(cut.astype(samples.dtype))

    def play(self, name):
        """Play a sound once. Unknown names, no sound device or muted: nothing."""
        if name in self.sounds and not self.muted:
            self.sounds[name].play()
            if name in SOUND_DUCKS:
                self.far_music(SOUND_DUCKS[name])

    def far_music(self, seconds):
        """
        For `seconds`, the music sounds far away: the next `seconds` of the
        song, made muffled and echoing, play as a sound, and the real music
        drops almost silent at once (music() brings it back slowly after).
        """
        samples = self.track_samples.get(self.track)
        position = self.music_position(self.track)
        if samples is None or position is None or self.music_volume == 0:
            return
        rate = pygame.mixer.get_init()[0]
        # The song loops, so the position may be past its end: wrap around.
        start = int(position * rate) % len(samples)
        part = np.take(samples, range(start, start + int(seconds * rate)), axis=0, mode="wrap")
        far = far_away(part.astype(float), rate)
        sound = pygame.sndarray.make_sound(np.clip(far, -32768, 32767).astype(samples.dtype))
        sound.set_volume(self.music_volume)
        sound.play()
        self.duck_left = seconds
        self.music_volume *= HEARTBEAT_MUSIC_DUCK
        pygame.mixer.music.set_volume(self.music_volume)

    def loop(self, name, on):
        """
        Call every frame: keep sound `name` looping while `on` (and not
        muted), fading in and out over LOOP_FADE_TIME. Unknown name or no
        sound device: nothing.
        """
        if name not in self.sounds:
            return
        on = on and not self.muted
        fade_ms = int(LOOP_FADE_TIME * 1000)
        if on and name not in self.loops:
            self.loops[name] = self.sounds[name].play(loops=-1, fade_ms=fade_ms)
        elif not on and name in self.loops:
            channel = self.loops.pop(name)
            if channel is not None:   # None: there was no free channel to play it on
                channel.fadeout(fade_ms)

    def start_music(self):
        """Let the music begin (it waits until the intro and the notice are over)."""
        self.has_music = pygame.mixer.get_init() is not None

    def music(self, track, dt):
        """
        Call every frame with the track that should play: "menu", "exam" or
        None (silence). The volume moves a little each frame, so it fades
        over MUSIC_FADE_TIME. A different track waits until the old one has
        faded out, then starts from its beginning and fades in.
        """
        if not self.has_music:
            return
        if track not in MUSIC_FILES or not os.path.exists(os.path.join(SOUND_FOLDER, MUSIC_FILES[track])):
            track = None   # file not added: silence
        if track is not None and track != self.track and self.music_volume == 0.0:
            self.load_track(track)
        playing_it = track is not None and track == self.track
        target = MUSIC_VOLUMES[track] if playing_it and not self.muted else 0.0
        # While the far-away music plays (far_music()) the real one stays quiet.
        self.duck_left = max(0.0, self.duck_left - dt)
        if self.duck_left > 0:
            target *= HEARTBEAT_MUSIC_DUCK
        step = MUSIC_VOLUME * dt / MUSIC_FADE_TIME   # how far the volume may move this frame
        self.music_volume = min(target, self.music_volume + step) if target > self.music_volume \
            else max(target, self.music_volume - step)
        pygame.mixer.music.set_volume(self.music_volume)

    def cut_to(self, track):
        """Start `track` from its beginning right now, at full volume (no fade): the intro is timed to it."""
        if not self.has_music or not os.path.exists(os.path.join(SOUND_FOLDER, MUSIC_FILES[track])):
            return
        self.load_track(track)
        self.music_volume = 0.0 if self.muted else MUSIC_VOLUMES[track]
        pygame.mixer.music.set_volume(self.music_volume)

    def music_position(self, track):
        """Seconds since `track` started, or None if it is not playing (no sound device, no file)."""
        if not self.has_music or self.track != track or not pygame.mixer.music.get_busy():
            return None
        return pygame.mixer.music.get_pos() / 1000

    def load_track(self, track):
        """Start a music track from its beginning, silent (music() fades it in), looping."""
        try:
            pygame.mixer.music.load(os.path.join(SOUND_FOLDER, MUSIC_FILES[track]))
            pygame.mixer.music.set_volume(0.0)
            pygame.mixer.music.play(loops=-1)    # -1 = loop forever
        except pygame.error as error:
            print(f"Could not play {MUSIC_FILES[track]} ({error}); no music.")
            pygame.mixer.music.stop()
        # Remembered even if it failed, so a broken file is not retried every frame.
        self.track = track
        if track in FAR_TRACKS and track not in self.track_samples:
            self.track_samples[track] = self.load_samples(MUSIC_FILES[track])

    @staticmethod
    def load_samples(file_name):
        """The whole song as numbers (for far_away()), or None if it cannot be loaded."""
        try:
            return pygame.sndarray.array(pygame.mixer.Sound(os.path.join(SOUND_FOLDER, file_name)))
        except (pygame.error, FileNotFoundError):
            return None   # then the music just stays as it is
