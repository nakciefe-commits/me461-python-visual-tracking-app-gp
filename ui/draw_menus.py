"""
Drawing the menus and the screens around the game: the start screen
(webcam + Calibrate button), the loading screen before each exam, the
"waiting for camera" screen and the main/settings/how-to-play menus (the
results screens are in draw_results.py). Part of Renderer (see render.py).

The menu background is a pulsing three-colour gradient with turning light
rays, film grain, scanlines and dark corners; the selected item is bigger,
neon and rocking.
"""

import math
import time

import numpy as np
import pygame

from settings import CALIBRATION_TIME, QUIZZES
from ui.style import (WHITE, YELLOW, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_RED, SHADOW,
                      HUD_PURPLE, FOOTER_HEIGHT, GLOW_BLUR, SHADOW_OFFSET, TITLE_PULSE,
                      TITLE_WOBBLE, TITLE_WOBBLE_SPEED, mix)

BIG_PREVIEW_SIZE = (480, 360)  # webcam preview on the start screen, pixels
BUTTON_TEXT = "CALIBRATE  (SPACE)"
BUTTON_HEIGHT = 60             # pixels, the Calibrate button on the start screen
BUTTON_PADDING = 45            # pixels between its text and its slanted ends (each side)
# (top, middle, bottom) colours the menu background slowly moves between:
# sunset tones, a little soft, with many tones in between.
MENU_PALETTES = [((255, 120, 175), (185, 55, 150), (40, 10, 75)),    # pink sunset
                 ((100, 175, 255), (125, 70, 200), (35, 12, 80)),    # blue to violet
                 ((255, 165, 100), (220, 80, 125), (60, 12, 72))]    # orange sunset
COLOUR_CYCLE_TIME = 4.0        # seconds to move from one background palette to the next
RAY_COUNT = 12                 # light rays turning behind the title
RAY_SPEED = 0.15               # radians per second the rays turn
RAY_ALPHA = 60                 # 0-255, how visible the rays are in the middle (they fade outwards)
RAY_LENGTH = 1200              # pixels, long enough to reach past the corners
VIGNETTE_ALPHA = 150           # 0-255, how dark the corners of the menus get
GRAIN_ALPHA = 10               # 0-255, a very light film grain that hides colour steps
ITEM_WOBBLE = 5                # degrees the selected menu item rocks
ITEM_WOBBLE_SPEED = 4.0        # radians per second of that rocking
SELECTED_SCALE = 1.2           # the selected item is drawn this much bigger
MENU_ITEM_GAP = 68             # pixels between menu items
TITLE_MAX_WIDTH = 800          # pixels; a longer title is shrunk to fit, wobble included
MENU_PREVIEW_SIZE = (192, 144) # webcam preview in the menus, pixels
INDICATOR_HEIGHT = 28          # pixels, the "HEAD CONTROL" / "KEYBOARD" box in the menus
MENU_HINT = ("HEAD: tilt up/down = choose   turn right = select   turn left = back"
             "        KEYS: arrows, Enter, Esc")
# The "How to play" screen: (text, colour).
HELP_LINES = [
    ("A run is 3 exams: Quiz, Midterm, Final. Your score is the total.", NEON_CYAN),
    ("Turn LEFT or RIGHT: their paper gets sharper as you keep looking.", WHITE),
    ("One neighbour knows the letter (A-D), the other one shows \"?\".", WHITE),
    ("Look DOWN at your paper: A-D writes it, S leaves it blank.", WHITE),
    ("Guessing is allowed: right +1, wrong -0.5, blank 0.", NEON_YELLOW),
    ("Look at the SCREEN to see the teacher. Busy teacher = safe to copy.", WHITE),
    ("Listen! \"Hmm\" means the teacher is about to look up.", YELLOW),
    ("Seen copying = caught (0 points). Staring at him = a warning (3 = out).", WHITE),
    ("Hand in early for a bonus. Time up = your paper is collected as it is.", WHITE),
]
TOP_PANEL = (28, 245, 250, 230)  # x, y, width, height of the top scores box on the main menu, pixels


class MenuDrawing:
    def make_menu_layers(self):
        """
        The see-through layers of the menu background that never change, made
        once with numpy (it works on all the pixels at once, which is fast):
          ray_fade  multiplied into the rays, so they fade out away from the middle
          vignette  black, more and more solid towards the corners
          grain     light random dots, which hide the steps between colours
        The rays are drawn at half size and then smoothly stretched, which
        gives them soft edges (and is quicker).
        """
        half = (self.width // 2, self.height // 2)
        self.rays = pygame.Surface(half, pygame.SRCALPHA)
        # Distance of every pixel from the rays' middle point, 0 there, ~1 at the corners.
        xs = (np.arange(half[0]) - half[0] / 2) / half[0]
        ys = (np.arange(half[1]) - half[1] / 3) / half[1]
        distance = np.sqrt(xs[:, None] ** 2 + ys[None, :] ** 2)   # [x, y], like pygame
        self.ray_fade = pygame.Surface(half, pygame.SRCALPHA)
        self.ray_fade.fill((255, 255, 255, 255))
        pygame.surfarray.pixels_alpha(self.ray_fade)[:] = (
            255 * np.clip(1 - distance / 0.9, 0, 1) ** 1.5).astype(np.uint8)

        xs = (np.arange(self.width) - self.width / 2) / (self.width / 2)
        ys = (np.arange(self.height) - self.height / 2) / (self.height / 2)
        edge = np.sqrt(xs[:, None] ** 2 + ys[None, :] ** 2) / math.sqrt(2)   # 0 middle, 1 corners
        self.vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.vignette.fill((10, 0, 20, 255))
        pygame.surfarray.pixels_alpha(self.vignette)[:] = (
            VIGNETTE_ALPHA * np.clip(edge - 0.35, 0, 1) ** 1.6 / 0.65 ** 1.6).astype(np.uint8)

        noise = np.random.default_rng(2).integers(0, 256, (self.width, self.height))
        self.grain = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.grain.fill((255, 255, 255, 255))
        pygame.surfarray.pixels3d(self.grain)[:] = noise[:, :, None].astype(np.uint8)
        pygame.surfarray.pixels_alpha(self.grain)[:] = GRAIN_ALPHA

    def menu_background(self):
        """
        The menu background: a three-colour gradient slowly changing colours,
        soft turning light rays, film grain, scanlines and dark corners.
        """
        t = self.t
        # Slowly slide from one palette to the next. The smoothstep curve
        # (3f² - 2f³) makes it ease in and out instead of moving at one speed.
        phase = (t / COLOUR_CYCLE_TIME) % len(MENU_PALETTES)
        index = int(phase)
        f = phase - index
        f = f * f * (3 - 2 * f)
        now, after = MENU_PALETTES[index], MENU_PALETTES[(index + 1) % len(MENU_PALETTES)]
        top, middle, bottom = (mix(a, b, f) for a, b in zip(now, after))
        # One line per pixel row: top → middle in the upper half, middle → bottom below.
        for y in range(self.height):
            part = y / self.height
            if part < 0.5:
                colour = mix(top, middle, part * 2)
            else:
                colour = mix(middle, bottom, (part - 0.5) * 2)
            self.screen.fill(colour, (0, y, self.width, 1))

        # Light rays from a point behind the title, turning with t, drawn
        # small, faded towards the edges, then stretched (soft edges).
        self.rays.fill((0, 0, 0, 0))
        width, height = self.rays.get_size()
        centre = (width // 2, height // 3)
        for k in range(RAY_COUNT):
            start = t * RAY_SPEED + k * 2 * math.pi / RAY_COUNT
            end = start + math.pi / RAY_COUNT   # each ray is half as wide as the gap
            corners = [centre] + [(centre[0] + RAY_LENGTH * math.cos(a),
                                   centre[1] + RAY_LENGTH * math.sin(a)) for a in (start, end)]
            pygame.draw.polygon(self.rays, (255, 240, 250, RAY_ALPHA), corners)
        self.rays.blit(self.ray_fade, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.screen.blit(pygame.transform.smoothscale(self.rays, (self.width, self.height)), (0, 0))
        self.screen.blit(self.grain, (0, 0))
        self.screen.blit(self.scanlines, (0, 0))
        self.screen.blit(self.vignette, (0, 0))

    def menu_title(self, message, y):
        """The big title: rocks left and right, and thumps bigger on every beat."""
        key = (message, NEON_YELLOW)
        if key not in self.neon_cache:
            self.neon_cache[key] = self.neon_text(message, self.menu_title_font, NEON_YELLOW,
                                                  glow=True)
        scale = 1 + TITLE_PULSE * self.beat() ** 3
        scale *= min(1.0, TITLE_MAX_WIDTH / self.neon_cache[key].get_width())
        angle = TITLE_WOBBLE * math.sin(self.t * TITLE_WOBBLE_SPEED)
        self.blit_turned(self.neon_cache[key], (self.width // 2, y), angle, scale)

    def item_glow(self, label):
        """The blurred pink glow behind a selected menu item, made once per item."""
        key = ("glow", label)
        if key not in self.neon_cache:
            text = self.menu_item_font.render(label, True, NEON_PINK)
            margin = 2 * GLOW_BLUR
            halo = pygame.Surface((text.get_width() + 2 * margin, text.get_height() + 2 * margin),
                                  pygame.SRCALPHA)
            halo.blit(text, (margin, margin))
            self.neon_cache[key] = pygame.transform.gaussian_blur(halo, GLOW_BLUR)
        return self.neon_cache[key]

    def menu_items(self, labels, selected, top, select_progress, gap=MENU_ITEM_GAP):
        """
        The menu items, one under the other from `top`. The selected one is
        bigger, neon and rocking; under it a bar shows how long the head has
        been turned right (selecting). Remembers where each item is, for clicks.
        """
        t = self.t
        cx = self.width // 2
        self.menu_rects = []
        for i, label in enumerate(labels):
            y = top + i * gap
            # The clickable area: the plain text's size, a bit bigger.
            hit = pygame.Rect((0, 0), self.menu_item_font.size(label)).inflate(40, 10)
            hit.center = (cx, y)
            self.menu_rects.append(hit)
            if i == selected:
                glow = (math.sin(t * ITEM_WOBBLE_SPEED * 1.5) + 1) / 2   # 0..1, back and forth
                angle = ITEM_WOBBLE * math.sin(t * ITEM_WOBBLE_SPEED)
                # A soft pink glow behind it, pulsing with the colour.
                halo = self.item_glow(label)
                halo.set_alpha(int(150 + 105 * glow))
                self.blit_turned(halo, (cx, y), angle, SELECTED_SCALE)
                image = self.neon_text(label, self.menu_item_font,
                                       mix(NEON_YELLOW, WHITE, glow))
                self.blit_turned(image, (cx, y), angle, SELECTED_SCALE)
                if select_progress > 0:
                    bar = pygame.Rect(hit.x, hit.bottom + 8, hit.width, 8)
                    pygame.draw.rect(self.screen, SHADOW, bar)
                    bar.width = int(bar.width * select_progress)
                    pygame.draw.rect(self.screen, NEON_CYAN, bar)
            else:
                # Not selected: white with a shadow, no ghosts.
                self.blit_turned(self.menu_item_font.render(label, True, SHADOW),
                                 (cx + SHADOW_OFFSET // 2, y + SHADOW_OFFSET // 2))
                self.blit_turned(self.menu_item_font.render(label, True, WHITE), (cx, y))

    def footer(self, hint, back_progress=0.0):
        """The hint strip at the bottom, and a bar while the head is turned left (back)."""
        self.hud_strip(self.height - FOOTER_HEIGHT, FOOTER_HEIGHT, line_at_top=True)
        self.text(hint, self.small, WHITE, (self.width // 2, self.height - FOOTER_HEIGHT // 2),
                  center=True)
        if back_progress > 0:
            box = pygame.Rect(16, self.height - 80, 140, 30)
            self.shadow_text("< BACK", self.hud, NEON_PINK, (box.x, box.y - 6))
            pygame.draw.rect(self.screen, SHADOW, (box.x, box.bottom, box.width, 6))
            pygame.draw.rect(self.screen, NEON_PINK,
                             (box.x, box.bottom, int(box.width * back_progress), 6))


    def draw_start(self, camera_surface, face_found, seconds_left=None):
        """
        The start screen: a big webcam preview and a "Calibrate" button.
        While calibrating (seconds_left is a number) the button becomes a
        progress bar.
        """
        self.menu_background()
        cx = self.width // 2
        self.preview(camera_surface, cx - BIG_PREVIEW_SIZE[0] // 2, 20, BIG_PREVIEW_SIZE)

        if not face_found:
            message, colour = "Face not found - move into the camera", NEON_RED
        elif seconds_left is None:
            message, colour = "Sit normally, look at the screen, then press Calibrate", WHITE
        else:
            message, colour = "Keep looking at the screen...", NEON_YELLOW
        self.darken(150, (0, 400, self.width, 40))
        self.shadow_text(message, self.medium, colour, (cx, 420), center=True)

        r = self.button_rect
        if seconds_left is None:
            # A slanted neon button (a parallelogram, like the bars).
            hovered = r.collidepoint(pygame.mouse.get_pos())
            skew = r.height // 3
            corners = [(r.x + skew, r.y), (r.right + skew, r.y),
                       (r.right - skew, r.bottom), (r.x - skew, r.bottom)]
            pygame.draw.polygon(self.screen, NEON_YELLOW if hovered else NEON_PINK, corners)
            pygame.draw.polygon(self.screen, WHITE, corners, 3)
            self.shadow_text(BUTTON_TEXT, self.hud, WHITE, r.center, center=True)
        else:
            done = 1 - seconds_left / CALIBRATION_TIME
            self.bar(r.x, r.y + 15, r.width, 30, done, NEON_YELLOW)

        self.footer("In the game:  A/B/C/D = write answer    Q = quit    R = restart    "
                    "M = menu    K = recalibrate")

    def draw_loading(self, progress, number, title):
        """
        The short screen before each exam, like a chapter screen in Hotline
        Miami: which exam of the run, its name, the date and a loading bar.
        progress: 0..1 (main.py makes it fill unevenly, like a real one).
        number: 0 = the first exam of the run.
        """
        self.menu_background()
        cx = self.width // 2
        self.shadow_text(f"ME461 - CHAPTER {number + 1}/{len(QUIZZES)}", self.hud, NEON_CYAN,
                         (cx, 150), center=True)
        self.menu_title(title, 235)
        # Today's date, e.g. "7 OCTOBER 2026".
        date = time.strftime("%d %B %Y").lstrip("0").upper()
        self.shadow_text(date, self.hud, WHITE, (cx, 320), center=True)

        self.shadow_text("Sharpening pencils...", self.medium, NEON_YELLOW, (cx, 410), center=True)
        bar_width = 520
        bar_x = cx - bar_width // 2
        self.bar(bar_x, 445, bar_width, 26, progress, NEON_PINK)
        self.shadow_text(f"{int(progress * 100)}%", self.hud, WHITE,
                         (bar_x + bar_width + 20, 443))
        # Blinks on and off, twice a second.
        if int(self.t * 4) % 2 == 0:
            self.shadow_text("SIT STRAIGHT AND LOOK AT THE SCREEN", self.hud, WHITE,
                             (cx, 510), center=True)
        self.footer("Get ready...")

    def draw_camera_wait(self, message):
        """
        No picture from the webcam (starting or reconnecting): the game is
        paused and the window stays responsive. `message` is the camera's
        status (camera.py), wrapped to fit the window.
        """
        self.menu_background()
        cx, cy = self.width // 2, self.height // 2
        self.shout("WAITING FOR CAMERA", self.hud_huge, NEON_YELLOW, (cx, cy - 90))
        for i, line in enumerate(self.wrap(message, self.medium, self.width - 120)):
            self.shadow_text(line, self.medium, WHITE, (cx, cy - 10 + i * 34), center=True)
        self.shadow_text("The game is paused and reconnects by itself.", self.medium, WHITE,
                         (cx, cy + 90), center=True)
        self.shadow_text("Close other camera apps, or check CAMERA_INDEX in settings.py.",
                         self.small, WHITE, (cx, cy + 130), center=True)
        self.footer("Q = quit")

    def head_indicator(self, head_pause, x, y, width):
        """
        Who controls the menu: "KEYBOARD" in pink just after a key press, with
        a bar filling up as head control comes back, then "HEAD CONTROL" in
        cyan. head_pause: 1 = keys just used, 0 = head control is on.
        """
        colour = mix(NEON_CYAN, NEON_PINK, head_pause)   # slides from pink back to cyan
        label = "KEYBOARD" if head_pause > 0 else "HEAD CONTROL"
        self.darken(170, (x, y, width, INDICATOR_HEIGHT), HUD_PURPLE)
        pygame.draw.rect(self.screen, colour, (x, y, width, INDICATOR_HEIGHT), 2)
        self.shadow_text(label, self.hud_small, colour, (x + width // 2, y + INDICATOR_HEIGHT // 2 - 2),
                         center=True)
        if head_pause > 0:
            # The bar under the label: how far head control has come back.
            pygame.draw.rect(self.screen, NEON_CYAN, (x, y + INDICATOR_HEIGHT - 5,
                                                     int(width * (1 - head_pause)), 5))

    def draw_menu(self, title, labels, selected, select_progress, back_progress,
                  camera_surface, lines=None, head_pause=0.0, top=None):
        """
        A whole menu screen in the neon style: main menu, settings, or how to
        play (with `lines`, a list of (text, colour) shown in a dark box).
        select_progress / back_progress (0..1): how long the head has been
        turned right / left, drawn as bars. camera_surface None = no
        webcam preview (the how-to-play text needs the room). head_pause:
        see head_indicator(). top: the top scores (main menu), shown in a
        box at the left; None = no box.
        """
        self.menu_background()
        if lines is None:
            # Short menus (the main menu) get a big title; longer ones move up.
            if len(labels) <= 4:
                self.menu_title(title, 120)
                items_top = 270
            else:
                self.menu_title(title, 75)
                items_top = 195
        else:
            self.menu_title(title, 60)
            box_top = 110
            self.darken(170, (60, box_top, self.width - 120, len(lines) * 36 + 24))
            for i, (message, colour) in enumerate(lines):
                self.text(message, self.medium, colour, (84, box_top + 14 + i * 36))
            items_top = box_top + len(lines) * 36 + 75
        self.menu_items(labels, selected, items_top, select_progress)
        if top is not None:
            self.top_scores(top, TOP_PANEL)

        # The webcam, so the player can see the head is being tracked, and
        # above it who is in control (the head or the keys).
        x = self.width - MENU_PREVIEW_SIZE[0] - 16
        y = self.height - MENU_PREVIEW_SIZE[1] - 50
        if camera_surface is not None:
            self.preview(camera_surface, x, y, MENU_PREVIEW_SIZE)
            self.head_indicator(head_pause, x, y - INDICATOR_HEIGHT - 6, MENU_PREVIEW_SIZE[0])
        else:
            # No webcam (how to play): the box sits low, clear of the text.
            self.head_indicator(head_pause, x, self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10,
                                MENU_PREVIEW_SIZE[0])
        self.footer(MENU_HINT, back_progress)
