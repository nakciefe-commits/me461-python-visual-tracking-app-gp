"""
The "Glitch Please" studio intro: our team's logo, shown when a program starts
(like a film studio's logo before a film, or a DJ's tag before a song).

The name "GLITCH PLEASE" appears broken up like a glitching screen: its red
and blue copies slide apart, slices of it jump sideways, it flickers. Then it
settles, the "GP" mark appears above it with a glitched slice cut out, and
"presents" fades in. About 3 seconds; any key or click skips it.

This file is made to be copied into any of our projects: it only needs
pygame (and numpy for the sound; without numpy it is silent). Use it with
one line, after pygame.init() and opening the window:

    from ui import glitch_intro
    if not glitch_intro.play(screen):   # False = the window was closed
        ...quit...

All its numbers are at the top of this file, so it stays one file.
"""

import math
import random

import pygame

# --- Timing (seconds from the start) ---
INTRO_TIME = 3.4          # the whole intro
GLITCH_START = 0.35       # black until here, then the name glitches in
SETTLE_TIME = 1.5         # from here the name is still (with a small twitch now and then)
MARK_TIME = 1.5           # the "GP" mark appears
PRESENTS_TIME = 1.9       # "presents" starts to fade in
FADE_OUT_TIME = 2.8       # from here everything fades to black
FPS = 60                  # frames per second of the intro

# --- Look ---
NAME = "GLITCH PLEASE"
MARK = "GP"
RED = (255, 30, 90)       # the two copies of the text that slide apart; where
CYAN = (0, 230, 255)      # they overlap they add up to (almost) white
WHITE = (245, 245, 245)
GREY = (150, 150, 165)
FONTS = [("impact", False), ("arialblack", False), ("dejavusans", True)]   # first one found
SPLIT_PIXELS = 18         # how far the red and blue copies are apart at the start
SLICES = 9                # the name is cut into this many strips that jump sideways
SLICE_JUMP = 40           # pixels the strips jump at most
TWITCH_EVERY = 0.7        # seconds between small glitches after it settles
STATIC_LINES = 14         # bright lines flashing across the screen while glitching
DESIGN_HEIGHT = 600       # sizes above are for a window this high; they scale with it

SAMPLE_RATE = 44100       # sound: numbers per second


def find_font(size):
    """A bold font this computer has (the first of FONTS), or pygame's own."""
    for name, bold in FONTS:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size, bold=True)


def make_mark(font, colour):
    """The "GP" mark: the letters in a rounded box, like a film studio logo."""
    letters = font.render(MARK, True, colour)
    pad = letters.get_height() // 4
    box = pygame.Surface((letters.get_width() + 2 * pad, letters.get_height() + pad),
                         pygame.SRCALPHA)
    pygame.draw.rect(box, colour, box.get_rect(), max(3, pad // 3), border_radius=pad)
    box.blit(letters, letters.get_rect(center=box.get_rect().center))
    # The glitch in the mark: a strip through the middle, moved sideways
    # for good (it is our logo, after all).
    strip = pygame.Rect(0, box.get_height() * 45 // 100, box.get_width(), box.get_height() // 9)
    cut = box.subsurface(strip).copy()
    box.fill((0, 0, 0, 0), strip)
    box.blit(cut, (strip.x + pad // 2, strip.y))
    return box


def glitch_blit(screen, red, cyan, centre, split, jump, rng, slices=SLICES):
    """
    Draw the red and the cyan copy of a picture `split` pixels apart, added
    on top of each other (so they make white where they meet), cut into
    strips that each jump up to `jump` pixels sideways.
    """
    width, height = red.get_size()
    left = centre[0] - width // 2
    top = centre[1] - height // 2
    strip_height = max(1, math.ceil(height / slices))
    for y in range(0, height, strip_height):
        dx = rng.randint(-jump, jump) if jump and rng.random() < 0.5 else 0
        area = pygame.Rect(0, y, width, strip_height)
        screen.blit(red, (left + dx - split, top + y), area, special_flags=pygame.BLEND_ADD)
        screen.blit(cyan, (left + dx + split, top + y), area, special_flags=pygame.BLEND_ADD)


def static_lines(screen, rng, count, scale):
    """Thin bright lines at random heights, like a TV losing its signal."""
    width, height = screen.get_size()
    for _ in range(count):
        y = rng.randrange(height)
        length = rng.randint(width // 6, width)
        x = rng.randint(0, width - length)
        shade = rng.randint(60, 200)
        pygame.draw.line(screen, (shade, shade, shade), (x, y), (x + length, y),
                         max(1, int(2 * scale)))


def make_sound():
    """
    The intro sound, made in code: a few chopped digital "bzzt"s while the
    name glitches in, then a low soft hit when it settles. None without numpy
    or without a working sound device.
    """
    if pygame.mixer.get_init() is None:
        return None
    try:
        import numpy as np
    except ImportError:
        return None
    rng = np.random.default_rng(3)

    def silence(seconds):
        return np.zeros(int(SAMPLE_RATE * seconds))

    def bzzt(seconds, pitch):
        # A buzzy square wave mixed with noise, cut into short on/off bits.
        t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
        square = np.sign(np.sin(2 * np.pi * pitch * t))
        chop = (np.sin(2 * np.pi * 45 * t) > 0).astype(float)
        return 0.35 * (0.6 * square + 0.4 * rng.uniform(-1, 1, len(t))) * chop

    def hit(seconds):
        # A low tone sliding down a little, fading out: a soft "boom".
        t = np.arange(int(SAMPLE_RATE * seconds)) / SAMPLE_RATE
        freq = 110 * (1 - 0.3 * t / seconds)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        return 0.8 * (np.sin(phase) + 0.3 * np.sin(2 * phase)) * np.exp(-3 * t)

    wave = np.concatenate([
        silence(GLITCH_START),
        bzzt(0.12, 180), silence(0.08), bzzt(0.06, 420), silence(0.1),
        bzzt(0.18, 90), silence(0.12), bzzt(0.05, 600), silence(0.08),
        silence(max(0.0, SETTLE_TIME - GLITCH_START - 0.79)),
        hit(1.6),
    ])
    samples = (np.clip(wave, -1, 1) * 0.5 * 32767).astype(np.int16)
    if pygame.mixer.get_init()[2] == 2:
        samples = np.column_stack([samples, samples])   # stereo: same on both sides
    return pygame.sndarray.make_sound(samples)


def draw_frame(screen, t, pictures, scale):
    """Draw the intro as it looks `t` seconds after it started."""
    screen.fill((0, 0, 0))
    width, height = screen.get_size()
    centre = (width // 2, height // 2 + int(20 * scale))
    # A new random pattern every frame, but the same one for the same moment.
    rng = random.Random(int(t * FPS))

    if t < GLITCH_START:
        return
    if t < SETTLE_TIME:
        # Glitching in: big split and jumps that calm down, flickering off now and then.
        calm = (t - GLITCH_START) / (SETTLE_TIME - GLITCH_START)   # 0 → 1
        static_lines(screen, rng, int(STATIC_LINES * (1 - calm)), scale)
        if rng.random() < 0.15 * (1 - calm):
            return   # a flicker: this frame shows nothing but static
        split = int(SPLIT_PIXELS * scale * (1 - calm) ** 2) + 1
        jump = int(SLICE_JUMP * scale * (1 - calm) ** 2)
        glitch_blit(screen, pictures["name_red"], pictures["name_cyan"], centre, split, jump, rng)
        return

    # Settled. Now and then a short twitch, so it still feels alive.
    twitch = (t - SETTLE_TIME) % TWITCH_EVERY < 0.06
    split = int(6 * scale) if twitch else 1
    jump = int(14 * scale) if twitch else 0
    glitch_blit(screen, pictures["name_red"], pictures["name_cyan"], centre, split, jump, rng)

    # The mark above the name, fading in.
    mark_alpha = min(1.0, (t - MARK_TIME) / 0.3)
    if mark_alpha > 0:
        mark = pictures["mark"]
        mark.set_alpha(int(255 * mark_alpha))
        mark_centre = (centre[0], centre[1] - pictures["name_red"].get_height() // 2
                       - mark.get_height() // 2 - int(18 * scale))
        screen.blit(mark, mark.get_rect(center=mark_centre))

    # "presents" under the name, fading in.
    presents_alpha = min(1.0, max(0.0, (t - PRESENTS_TIME) / 0.4))
    if presents_alpha > 0:
        presents = pictures["presents"]
        presents.set_alpha(int(255 * presents_alpha))
        below = centre[1] + pictures["name_red"].get_height() // 2 + int(28 * scale)
        screen.blit(presents, presents.get_rect(center=(centre[0], below)))

    # The end: everything fades to black.
    if t > FADE_OUT_TIME:
        fade = min(1.0, (t - FADE_OUT_TIME) / (INTRO_TIME - FADE_OUT_TIME))
        black = pygame.Surface(screen.get_size())
        black.set_alpha(int(255 * fade))
        screen.blit(black, (0, 0))


def make_pictures(scale):
    """Everything drawn in the intro, made once (rendering text every frame is slow)."""
    name_font = find_font(int(84 * scale))
    mark_font = find_font(int(60 * scale))
    small_font = pygame.font.SysFont(None, int(34 * scale))
    return {
        # On a black background, not see-through: the copies are *added* to
        # the screen (glitch_blit), and adding black changes nothing, while
        # the colour hidden in see-through pixels would show up as a box.
        "name_red": name_font.render(NAME, True, RED, (0, 0, 0)),
        "name_cyan": name_font.render(NAME, True, CYAN, (0, 0, 0)),
        "mark": make_mark(mark_font, WHITE),
        "presents": small_font.render("p r e s e n t s", True, GREY),
    }


def play(screen, clock=None):
    """
    Play the intro on `screen` (the window). Returns True when it is over
    (or skipped with a key or a click), False if the window was closed.
    """
    clock = clock or pygame.time.Clock()
    scale = screen.get_height() / DESIGN_HEIGHT
    pictures = make_pictures(scale)
    sound = make_sound()
    if sound is not None:
        sound.play()
    start = pygame.time.get_ticks()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if sound is not None:
                    sound.stop()
                return False
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                if sound is not None:
                    sound.fadeout(200)
                return True
        t = (pygame.time.get_ticks() - start) / 1000
        if t >= INTRO_TIME:
            return True
        draw_frame(screen, t, pictures, scale)
        pygame.display.flip()
        clock.tick(FPS)
