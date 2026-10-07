"""
The shared look of every screen: colours, fonts and small drawing helpers.

Everything is drawn in a neon 80s style, a bit like the game Hotline Miami:
slanted bold text with a dark shadow and pink and cyan "ghost" copies,
see-through dark purple strips with a neon pink edge, slanted bars, big
words that rock and thump on a "beat". The helpers here are used by all the
draw_*.py files (see render.py for how they fit together).
"""

import math

import pygame

# Colours are (Red, Green, Blue) in pygame, not (Blue, Green, Red) as in OpenCV!
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GREY = (110, 115, 125)
YELLOW = (240, 200, 60)
PREVIEW_SIZE = (240, 180)      # webcam preview in the game, pixels

# --- Neon style (Hotline Miami-like) ---
NEON_PINK = (255, 40, 160)
NEON_CYAN = (40, 230, 255)
NEON_YELLOW = (255, 235, 70)
NEON_GREEN = (80, 255, 150)
NEON_RED = (255, 50, 80)
SHADOW = (30, 0, 50)           # dark purple shadow under the text
HUD_PURPLE = (25, 0, 45)       # colour of the see-through strips in the game
HUD_ALPHA = 190                # 0-255, how solid those strips are
HUD_LINE = 3                   # pixels, the neon pink line along each strip
FOOTER_HEIGHT = 34             # pixels, the hint strip at the bottom of the menus
TEXT_SHADOW = 2                # pixels the shadow of small texts is moved
TEXT_WOBBLE = 3                # degrees big game texts (popup, end, clock) rock
GLOW_BLUR = 10                 # pixels; how soft the glow behind the menu texts is
GHOST_ALPHA = 150              # 0-255, how strong the pink and cyan copies of the text are
GHOST_OFFSET = 4               # pixels the pink and cyan copies of the text are moved
SHADOW_OFFSET = 6              # pixels the shadow is moved down-right
BEAT_TIME = 0.5                # seconds per "beat": the title thumps bigger on each one
TITLE_PULSE = 0.06             # how much bigger the title is on a beat (0.06 = 6 %)
TITLE_WOBBLE = 4               # degrees the title rocks left and right
TITLE_WOBBLE_SPEED = 1.3       # radians per second of that rocking
SCANLINE_GAP = 3               # pixels between the dark "old TV" lines
SCANLINE_ALPHA = 20            # 0-255, how dark those lines are
# Font files to try for the menus, in order: (name, bold). Impact looks most
# like the game; DejaVu Sans Bold comes with most Linux systems.
MENU_FONTS = [("impact", False), ("arialblack", False), ("dejavusans", True)]
MONO_FONTS = [("couriernew", True), ("courier", True), ("nimbusmonops", True), ("dejavusansmono", True),
              ("liberationmono", True)]   # typewriter-looking fonts, first one found


def mix(colour_a, colour_b, fraction):
    """The colour `fraction` (0..1) of the way from colour_a to colour_b."""
    return tuple(int(a + (b - a) * fraction) for a, b in zip(colour_a, colour_b))


def menu_font(size):
    """The first font in MENU_FONTS that this computer has, slanted like Hotline Miami."""
    font = None
    for name, bold in MENU_FONTS:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            font = pygame.font.Font(path, size)
            break
    if font is None:
        font = pygame.font.SysFont(None, size, bold=True)   # pygame's own font
    font.italic = True   # pygame slants it for us
    return font


def mono_font(size):
    """A typewriter-looking font (the first of MONO_FONTS this computer has)."""
    for name, bold in MONO_FONTS:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.SysFont(None, size)


class NeonStyle:
    """Small drawing helpers; part of Renderer (see render.py)."""

    def text(self, message, font, colour, pos, center=False):
        image = font.render(message, True, colour)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(image, rect)
        return rect

    def shadow_text(self, message, font, colour, pos, center=False):
        """Text with a dark purple shadow under it, so it reads on any picture."""
        x, y = pos
        self.text(message, font, SHADOW, (x + TEXT_SHADOW, y + TEXT_SHADOW), center)
        return self.text(message, font, colour, pos, center)

    def darken(self, alpha=170, rect=None, colour=BLACK):
        """
        Lay a see-through sheet (black, or `colour`) over whatever is already
        drawn: over the whole window, or only over `rect` (x, y, width, height).
        alpha: 0 = invisible, 255 = fully covered.
        """
        x, y, width, height = rect or (0, 0, self.width, self.height)
        sheet = pygame.Surface((width, height), pygame.SRCALPHA)
        sheet.fill((*colour, alpha))
        self.screen.blit(sheet, (x, y))

    def panel(self, rect):
        """A see-through dark purple box with a neon pink edge, like the strips in the game."""
        self.darken(HUD_ALPHA, rect, HUD_PURPLE)
        pygame.draw.rect(self.screen, NEON_PINK, rect, 2)

    def hud_strip(self, y, height, line_at_top):
        """A see-through dark purple strip with a neon pink line along one edge."""
        self.darken(HUD_ALPHA, (0, y, self.width, height), HUD_PURPLE)
        line_y = y if line_at_top else y + height - HUD_LINE
        self.screen.fill(NEON_PINK, (0, line_y, self.width, HUD_LINE))

    def bar(self, x, y, width, height, fraction, colour):
        """
        A slanted bar (a parallelogram, like everything in Hotline Miami):
        dark background, the filled part in `colour`, a white outline.
        """
        def slanted(w):
            # Top edge moved right by half the height: a / shape.
            skew = height // 2
            return [(x + skew, y), (x + skew + w, y), (x + w, y + height), (x, y + height)]

        pygame.draw.polygon(self.screen, SHADOW, slanted(width))
        if fraction > 0:
            pygame.draw.polygon(self.screen, colour, slanted(max(1, int(width * fraction))))
        pygame.draw.polygon(self.screen, WHITE, slanted(width), 2)

    def beat(self, period=BEAT_TIME):
        """1 right on each beat, falling to 0 just before the next. For thumping text."""
        return 1 - (self.t / period) % 1

    def neon_text(self, message, font, colour, glow=False):
        """
        A picture of the text in the neon style: a soft shadow, a cyan and a
        pink copy a few pixels to each side (half see-through), and the
        coloured text on top. glow=True also puts a blurred pink glow behind
        it (slower: for titles, made once, and the selected menu item).
        """
        top = font.render(message, True, colour)
        width, height = top.get_size()
        margin = 2 * GLOW_BLUR if glow else 0   # room for the glow around the text
        sheet = pygame.Surface((width + 2 * GHOST_OFFSET + SHADOW_OFFSET + 2 * margin,
                                height + SHADOW_OFFSET + 2 * margin), pygame.SRCALPHA)
        if glow:
            halo = pygame.Surface(sheet.get_size(), pygame.SRCALPHA)
            halo.blit(font.render(message, True, NEON_PINK), (margin + GHOST_OFFSET, margin))
            sheet.blit(pygame.transform.gaussian_blur(halo, GLOW_BLUR), (0, 0))
        shadow = font.render(message, True, SHADOW)
        shadow.set_alpha(170)
        sheet.blit(shadow, (margin + GHOST_OFFSET + SHADOW_OFFSET, margin + SHADOW_OFFSET))
        for ghost, x in ((NEON_CYAN, 0), (NEON_PINK, 2 * GHOST_OFFSET)):
            copy = font.render(message, True, ghost)
            copy.set_alpha(GHOST_ALPHA)
            sheet.blit(copy, (margin + x, margin))
        sheet.blit(top, (margin + GHOST_OFFSET, margin))
        return sheet

    def blit_turned(self, image, centre, angle=0.0, scale=1.0):
        """Draw a picture turned by `angle` degrees and scaled, centred on `centre`."""
        if angle or scale != 1.0:
            image = pygame.transform.rotozoom(image, angle, scale)
        self.screen.blit(image, image.get_rect(center=centre))

    def shout(self, message, font, colour, centre, wobble=TEXT_WOBBLE, pulse=TITLE_PULSE):
        """
        Neon text that rocks left and right and thumps on the beat, like the
        big words in Hotline Miami. For texts that change, like the clock.
        """
        angle = wobble * math.sin(self.t * TITLE_WOBBLE_SPEED * 2)
        scale = 1 + pulse * self.beat() ** 3   # cubed: a short thump, not a slow swell
        self.blit_turned(self.neon_text(message, font, colour), centre, angle, scale)

    def wrap(self, message, font, max_width):
        """Split a message into lines no wider than max_width, between words."""
        lines = [""]
        for word in message.split():
            longer = (lines[-1] + " " + word).strip()
            if font.size(longer)[0] <= max_width or not lines[-1]:
                lines[-1] = longer
            else:
                lines.append(word)
        return lines

    def preview(self, camera_surface, x, y, size=PREVIEW_SIZE):
        """The webcam picture with a neon frame."""
        if camera_surface is not None:
            self.screen.blit(camera_surface, (x, y))
        pygame.draw.rect(self.screen, NEON_CYAN, (x, y, *size), 3)
