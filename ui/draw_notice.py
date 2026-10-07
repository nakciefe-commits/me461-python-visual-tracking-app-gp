"""
Drawing the opening screen: an official notice on a wooden desk. The paper
slides in, the text is typed out, Space signs it and an "APPROVED" stamp
comes down. Its timing is in disclaimer.py (no drawing there, so it is
tested); this file only draws it. Part of Renderer (see render.py).
"""

import math
import random

import pygame

from ui.style import BLACK, WHITE, mix, menu_font

# The disclaimer shown when the game opens: (text, colour). Satire, but the
# last line is meant seriously.
# The disclaimer, as an official notice typed on a paper: (text, ink colour).
INK = (35, 35, 50)
FADED_INK = (110, 110, 125)
BLUE_INK = (30, 60, 160)
DISCLAIMER_LINES = [
    ("This game does not represent any real-life situation.", INK),
    ("Any resemblance to real exams, classrooms or professors", INK),
    ("is purely coincidental (and slightly suspicious).", INK),
    ("It is purely for entertainment purposes.", INK),
    ("No neighbours' answers were harmed in the making of this game.", FADED_INK),
    ("We love our professor and we respect academic honesty.", BLUE_INK),
]
# The letters of the notice, for disclaimer.Disclaimer.
DISCLAIMER_LETTERS = sum(len(text) for text, _ in DISCLAIMER_LINES)
NOTICE_TITLE = "OFFICIAL NOTICE"
NOTICE_FROM = "ACADEMIC INTEGRITY DEPARTMENT  -  ME461"
PAPER = (246, 241, 228)          # the paper's colour
PAPER_RECT = (100, 34, 760, 516) # x, y, width, height of the paper, pixels
PAPER_SLIDE = 0.5                # seconds the paper takes to slide in from below
STAMP_RED = (200, 30, 40)
STAMP_ANGLE = 14                 # degrees the stamp is turned
STAMP_SLAM = 0.12                # seconds the stamp takes to come down (from big to its size)
DESK_DARK = (45, 26, 16)         # the wooden desk behind the paper: dark and light wood
DESK_LIGHT = (95, 58, 34)


class NoticeDrawing:
    def make_desk(self):
        """
        A wooden desk to lie the notice on, made once: a dark-to-light
        gradient with wavy grain lines, darker towards the corners.
        """
        desk = pygame.Surface((self.width, self.height))
        for y in range(self.height):
            # The light comes from the middle: lightest there, darker at the edges.
            light = 1 - abs(y / self.height - 0.5) * 1.6
            desk.fill(mix(DESK_DARK, DESK_LIGHT, max(0.0, light)), (0, y, self.width, 1))
        grain = random.Random(5)
        for _ in range(70):
            # Each grain line is a gentle wave across the desk.
            y0 = grain.uniform(0, self.height)
            wave, speed = grain.uniform(2, 7), grain.uniform(0.004, 0.012)
            shade = mix(DESK_DARK, BLACK, grain.uniform(0.0, 0.4))
            points = [(x, y0 + wave * math.sin(x * speed + y0)) for x in range(0, self.width + 20, 20)]
            pygame.draw.lines(desk, shade, False, points, 1)
        return desk

    def make_stamp(self):
        """The red "APPROVED" stamp: a double frame and the word, a bit see-through, turned."""
        font = menu_font(54)
        font.italic = False
        word = font.render("APPROVED", True, STAMP_RED)
        pad = 18
        stamp = pygame.Surface((word.get_width() + 2 * pad, word.get_height() + pad), pygame.SRCALPHA)
        frame = stamp.get_rect()
        pygame.draw.rect(stamp, STAMP_RED, frame, 5, border_radius=10)
        pygame.draw.rect(stamp, STAMP_RED, frame.inflate(-14, -14), 2, border_radius=6)
        stamp.blit(word, word.get_rect(center=frame.center))
        stamp.set_alpha(215)   # ink on paper: you can see the paper a little through it
        return pygame.transform.rotozoom(stamp, STAMP_ANGLE, 1.0)

    def signature(self, x, y, width, progress):
        """
        A scribbled signature, written from left to right as progress goes
        0 → 1: a line that loops with two sine waves of different speeds.
        """
        total = 300   # points along the whole signature; many, so it is smooth
        steps = int(total * progress)
        if steps < 2:
            return
        points = []
        for i in range(steps):
            s = i / total
            # Moving right with small loops back (the sine on x), going up
            # and down in bigger waves that get smaller to the end.
            points.append((x + s * width + 9 * math.sin(s * 38),
                           y - 13 * math.sin(s * 19) * (1 - 0.5 * s) - 5 * math.sin(s * 57)))
        pygame.draw.aalines(self.screen, BLUE_INK, False, points)
        pygame.draw.lines(self.screen, BLUE_INK, False, points, 2)

    def draw_disclaimer(self, notice):
        """
        The first screen: an official notice on a desk. The paper slides in,
        the text is typed out, Space signs it, and an "APPROVED" stamp
        comes down. `notice` is a disclaimer.Disclaimer.
        """
        self.screen.blit(self.desk, (0, 0))
        x, y, width, height = PAPER_RECT
        # Sliding in from below, slowing down at the end (1 - (1-f)³).
        slide = min(1.0, notice.time / PAPER_SLIDE)
        y += int((self.height - y) * (1 - slide) ** 3)
        # The stamp shakes the paper when it comes down.
        age = notice.stamp_age()
        if age is not None and age < 0.25:
            shake = int(8 * (1 - age / 0.25) * math.sin(age * 90))
            x, y = x + shake, y + shake // 2
        paper = pygame.Rect(x, y, width, height)
        self.darken(110, paper.move(10, 12))            # its shadow on the desk
        pygame.draw.rect(self.screen, PAPER, paper)

        cx = paper.centerx
        self.text(NOTICE_TITLE, self.type_title_font, INK, (cx, y + 42), center=True)
        self.text(NOTICE_FROM, self.type_font, FADED_INK, (cx, y + 78), center=True)
        pygame.draw.line(self.screen, INK, (x + 40, y + 100), (paper.right - 40, y + 100), 2)

        # The text, typed letter by letter.
        letters = notice.letters()
        for i, (message, colour) in enumerate(DISCLAIMER_LINES):
            if letters <= 0:
                break
            shown = message[:letters]
            letters -= len(message)
            line_x, line_y = x + 45, y + 128 + i * 36
            image = self.text(shown, self.type_font, colour, (line_x, line_y))
            if 0 < len(shown) < len(message) and int(self.t * 3) % 2 == 0:
                # The typewriter's cursor after the last letter, blinking.
                self.screen.fill(INK, (image.right + 2, line_y + 2, 10, image.height - 4))

        # Where to sign.
        sign_y = y + height - 80
        self.text("Signed:", self.type_font, INK, (x + 45, sign_y - 14))
        pygame.draw.line(self.screen, INK, (x + 150, sign_y + 8), (x + 450, sign_y + 8), 2)
        self.signature(x + 165, sign_y - 6, 260, notice.sign_progress())

        if age is not None:
            # Slam: starts big and lands at its size in STAMP_SLAM seconds.
            scale = 1 + 1.2 * max(0.0, 1 - age / STAMP_SLAM)
            self.blit_turned(self.stamp, (paper.right - 175, sign_y - 40), 0, scale)

        # What to do now, blinking under the paper.
        if notice.signed_at is None and int(self.t * 2) % 2 == 0:
            hint = ("Press Space to solemnly swear you will never try this in a real exam"
                    if notice.typed() else "Press Space to read faster")
            self.shadow_text(hint, self.small, WHITE, (self.width // 2, self.height - 22),
                             center=True)
