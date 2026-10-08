"""
Drawing the run intro: the sarcastic "briefing" before the character
screen, timed to the character music. Part of Renderer (see render.py);
logic/run_intro.py says which line is on screen and where the beats are.

It also draws the quick title card before each exam (draw_exam_title()):
the exam's name slams in, then its sarcastic line ("THE FINAL - God,
please help me."), in the same style.

Like a chapter screen in Hotline Miami: diagonal neon stripes rush across
a dark screen, and on every strong hit of the music a new line slams in,
huge and tilted, with a white flash and the screen shaking. The text
thumps a little on every beat in between. The colours change with each line.
"""

import math

import pygame

from logic.run_intro import INTRO_LINES, current_line, since_line, since_beat
from settings import INTRO_FIRST_HIT, EXAM_TAGLINE_DELAY, EXAM_TITLE_TIME
from ui.style import WHITE, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, SHADOW, mix

# (stripe colour, background colour, text colour) for each line, in turn.
INTRO_PALETTES = [((255, 40, 160), (25, 0, 40), NEON_YELLOW),
                  ((40, 230, 255), (0, 15, 40), WHITE),
                  ((255, 235, 70), (40, 10, 0), NEON_PINK),
                  ((80, 255, 150), (0, 30, 20), WHITE),
                  ((255, 50, 80), (40, 0, 10), NEON_YELLOW)]
STRIPE_WIDTH = 46              # pixels, one diagonal stripe (and the gap after it)
STRIPE_SPEED = 420             # pixels per second the stripes rush sideways
STRIPE_ALPHA = 70              # 0-255, how strong the stripes are
SLAM_TIME = 0.14               # seconds a line takes to slam down from big to its size
SLAM_SIZE = 2.6                # how big a line starts (2.6 = 260 %)
FLASH_TIME = 0.18              # seconds the white flash takes to fade after a hit
SHAKE = 16                     # pixels the screen shakes right after a hit (then calms down)
SHAKE_TIME = 0.35              # seconds the shake takes to calm down
BEAT_THUMP = 0.05              # how much bigger the line is right on each beat
LINE_TILT = 6                  # degrees each line is tilted (left, right, left...)
INTRO_LINE_Y = 300             # pixels, the middle of the big line
# The title card's palette for each exam of the run (the last one for the practice).
EXAM_PALETTES = [INTRO_PALETTES[1], INTRO_PALETTES[2], INTRO_PALETTES[4], INTRO_PALETTES[3]]
TITLE_Y = 250                  # pixels, the middle of the exam's name on the title card
TAGLINE_Y = 370                # pixels, the middle of its sarcastic line
INTRO_HINT = "SPACE / ENTER / turn your head RIGHT = skip      LEFT = back to the menu"


class RunIntroDrawing:
    def draw_run_intro(self, t):
        """One frame of the intro, t seconds into the music."""
        line = current_line(t)
        palette = INTRO_PALETTES[(line or 0) % len(INTRO_PALETTES)]
        stripe, background, text_colour = palette
        since = since_line(t)
        self.screen.fill(background)
        self.intro_stripes(t, stripe)

        # Right after a hit the whole picture shakes, calming down.
        calm = max(0.0, 1 - since / SHAKE_TIME)
        dx = SHAKE * calm * math.sin(t * 90)
        dy = SHAKE * calm * math.cos(t * 70)

        cx = self.width // 2
        header = "ME461  //  SEMESTER BRIEFING"
        if int(t * 2) % 2 == 0 or line is not None:   # blinks until the first hit
            self.shadow_text(header, self.hud, NEON_CYAN, (cx + dx, 70 + dy), center=True)

        if line is None:
            # Before the first hit: the course name fades in.
            fade = min(1.0, t / INTRO_FIRST_HIT)
            image = self.neon_text("ME461", self.menu_title_font, mix(SHADOW, NEON_PINK, fade))
            self.blit_turned(image, (cx, INTRO_LINE_Y), 0, 0.8 + 0.2 * fade)
        else:
            # The line: slams down from big, then thumps on every beat.
            slam = max(0.0, 1 - since / SLAM_TIME)
            thump = BEAT_THUMP * max(0.0, 1 - since_beat(t) / 0.15)
            scale = 1 + (SLAM_SIZE - 1) * slam ** 2 + thump
            tilt = LINE_TILT if line % 2 else -LINE_TILT
            image = self.intro_line_image(INTRO_LINES[line], text_colour)
            self.blit_turned(image, (cx + dx, INTRO_LINE_Y + dy), tilt, scale)

            # Bars under it, one per line: how far through the briefing.
            for i in range(len(INTRO_LINES)):
                lit = i <= line
                box = pygame.Rect(0, 0, 36, 8)
                box.center = (cx + (i - (len(INTRO_LINES) - 1) / 2) * 46, 470)
                pygame.draw.rect(self.screen, stripe if lit else SHADOW, box)

        # The white flash of the hit, on top of everything.
        flash = max(0.0, 1 - since / FLASH_TIME)
        if flash > 0:
            self.darken(int(200 * flash), colour=WHITE)
        self.screen.blit(self.scanlines, (0, 0))
        self.footer(INTRO_HINT)

    def intro_line_image(self, text, colour):
        """The big neon line, made once per line and colour (it is the same every frame)."""
        key = ("intro", text, colour)
        if key not in self.neon_cache:
            image = self.neon_text(text, self.menu_title_font, colour, glow=True)
            # Too wide for the window: made smaller once, here.
            limit = self.width - 80
            if image.get_width() > limit:
                image = pygame.transform.smoothscale_by(image, limit / image.get_width())
            self.neon_cache[key] = image
        return self.neon_cache[key]

    def intro_stripes(self, t, colour):
        """Diagonal stripes rushing sideways across the whole screen."""
        layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        shift = (t * STRIPE_SPEED) % (2 * STRIPE_WIDTH)
        lean = self.height // 2   # how far right the top of a stripe is from its bottom
        for x in range(-lean - 2 * STRIPE_WIDTH, self.width + 2 * STRIPE_WIDTH, 2 * STRIPE_WIDTH):
            left = x + shift
            pygame.draw.polygon(layer, (*colour, STRIPE_ALPHA),
                                [(left + lean, 0), (left + lean + STRIPE_WIDTH, 0),
                                 (left + STRIPE_WIDTH, self.height), (left, self.height)])
        self.screen.blit(layer, (0, 0))

    def draw_exam_title(self, title, tagline, since, number, practice=False):
        """
        The quick card after the loading bar: `title` slams in with a flash,
        EXAM_TAGLINE_DELAY later the sarcastic `tagline` slams in under it,
        and the card fades to black at the end, into the exam.
        since: seconds since the card opened; number: 0 = the run's first exam.
        """
        stripe, background, text_colour = EXAM_PALETTES[-1 if practice else number % 3]
        self.screen.fill(background)
        self.intro_stripes(since, stripe)
        cx = self.width // 2
        shake = SHAKE * max(0.0, 1 - min(since, abs(since - EXAM_TAGLINE_DELAY)) / SHAKE_TIME)
        dx, dy = shake * math.sin(since * 90), shake * math.cos(since * 70)

        slam = max(0.0, 1 - since / SLAM_TIME)
        image = self.intro_line_image(title, text_colour)
        self.blit_turned(image, (cx + dx, TITLE_Y + dy), -LINE_TILT, 1 + (SLAM_SIZE - 1) * slam ** 2)

        late = since - EXAM_TAGLINE_DELAY   # seconds since the tagline slammed in
        if late >= 0 and tagline:
            slam = max(0.0, 1 - late / SLAM_TIME)
            line = self.neon_text(tagline.upper(), self.hud_big, WHITE)
            fit = min(1.0, (self.width - 120) / line.get_width())   # a long line is made smaller
            self.blit_turned(line, (cx - dx, TAGLINE_Y - dy), LINE_TILT / 2,
                             fit * (1 + (SLAM_SIZE - 1) * slam ** 2))

        # A flash on each slam, and a fade to black at the very end.
        flash = max(0.0, 1 - min(since, late if late >= 0 else 1e9) / FLASH_TIME)
        if flash > 0:
            self.darken(int(200 * flash), colour=WHITE)
        out = (since - (EXAM_TITLE_TIME - 0.3)) / 0.3
        if out > 0:
            self.darken(int(255 * min(1.0, out)))
        self.screen.blit(self.scanlines, (0, 0))
