"""
Drawing: everything the player sees, made from shapes and text (no art yet).

Each draw_... function paints one whole screen onto the pygame window. They
only read the game's state; they never change it.
"""

import cv2
import pygame

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from settings import (CALIBRATION_TIME, ANSWERS_NEEDED, MAX_WARNINGS,
                      STARE_GRACE_TIME, STARE_FILL_TIME)

# Colours are (Red, Green, Blue) in pygame, not (Blue, Green, Red) as in OpenCV!
BACKGROUND = (25, 28, 35)
WHITE = (240, 240, 240)
GREY = (110, 115, 125)
DARK_GREY = (55, 60, 70)
GREEN = (70, 200, 110)
YELLOW = (240, 200, 60)
RED = (220, 60, 60)
BLUE = (80, 150, 240)

PREVIEW_SIZE = (320, 240)   # webcam preview in the game, pixels
BIG_PREVIEW_SIZE = (480, 360)  # webcam preview on the start screen, pixels

# What to show for each head direction: (box number, title)
TITLES = {
    DOWN: "1 - Looking at the paper",
    SCREEN: "2 - Looking at the teacher",
    LEFT: "3 - Copying (left)",
    RIGHT: "3 - Copying (right)",
}
OPTION_BOXES = [  # (label, directions that light it up, colour)
    ("1  PAPER", (DOWN,), BLUE),
    ("2  SCREEN", (SCREEN,), YELLOW),
    ("3  NEIGHBOUR", (LEFT, RIGHT), GREEN),
]


def camera_to_surface(frame, size=PREVIEW_SIZE):
    """Turn an OpenCV webcam frame into a smaller, mirrored pygame image."""
    small = cv2.resize(cv2.flip(frame, 1), size)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(rgb.tobytes(), size, "RGB")


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        # Fonts are loaded once; None = pygame's built-in font.
        self.huge = pygame.font.SysFont(None, 72)
        self.big = pygame.font.SysFont(None, 52)
        self.medium = pygame.font.SysFont(None, 34)
        self.small = pygame.font.SysFont(None, 24)
        # The "Calibrate" button on the start screen. main.py checks clicks on it.
        self.button_rect = pygame.Rect(0, 0, 300, 60)
        self.button_rect.center = (self.width // 2, 500)

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def text(self, message, font, colour, pos, center=False):
        image = font.render(message, True, colour)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(image, rect)
        return rect

    def darken(self, alpha=170):
        """Lay a see-through black sheet over whatever is already drawn."""
        sheet = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        sheet.fill((0, 0, 0, alpha))
        self.screen.blit(sheet, (0, 0))

    def bar(self, x, y, width, height, fraction, colour):
        pygame.draw.rect(self.screen, DARK_GREY, (x, y, width, height), border_radius=6)
        if fraction > 0:
            pygame.draw.rect(self.screen, colour, (x, y, int(width * fraction), height),
                             border_radius=6)

    def preview(self, camera_surface, x, y, size=PREVIEW_SIZE):
        if camera_surface is not None:
            self.screen.blit(camera_surface, (x, y))
        pygame.draw.rect(self.screen, GREY, (x, y, *size), 2)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def draw_start(self, camera_surface, face_found, seconds_left=None):
        """
        The start screen: a big webcam preview and a "Calibrate" button.
        While calibrating (seconds_left is a number) the button becomes a
        progress bar.
        """
        self.screen.fill(BACKGROUND)
        cx = self.width // 2
        self.preview(camera_surface, cx - BIG_PREVIEW_SIZE[0] // 2, 20, BIG_PREVIEW_SIZE)

        if not face_found:
            self.text("Face not found - move into the camera", self.medium, RED,
                      (cx, 420), center=True)
        elif seconds_left is None:
            self.text("Sit normally, look at the screen, then press Calibrate",
                      self.medium, WHITE, (cx, 420), center=True)
        else:
            self.text("Keep looking at the screen...", self.medium, YELLOW,
                      (cx, 420), center=True)

        if seconds_left is None:
            hovered = self.button_rect.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(self.screen, GREEN if hovered else BLUE, self.button_rect,
                             border_radius=12)
            self.text("Calibrate  (Space)", self.medium, BACKGROUND,
                      self.button_rect.center, center=True)
        else:
            done = 1 - seconds_left / CALIBRATION_TIME
            r = self.button_rect
            self.bar(r.x, r.y + 15, r.width, 30, done, YELLOW)

        self.text("Q = quit", self.small, GREY, (cx, 575), center=True)

    def draw_game(self, game, direction, camera_surface, yaw, pitch, fps,
                  tracking_note=None, show_popup=True):
        self.screen.fill(BACKGROUND)

        # Top left: current option, answers and warnings.
        self.text(TITLES[direction], self.big, WHITE, (30, 30))

        self.text("Answers", self.medium, WHITE, (30, 112))
        for i in range(ANSWERS_NEEDED):
            box = (160 + i * 40, 108, 28, 28)
            if i < game.answers:
                pygame.draw.rect(self.screen, GREEN, box, border_radius=4)
            else:
                pygame.draw.rect(self.screen, GREY, box, 2, border_radius=4)
        self.text(f"{game.answers}/{ANSWERS_NEEDED}", self.medium, WHITE,
                  (170 + ANSWERS_NEEDED * 40, 112))

        self.text("Warnings", self.medium, WHITE, (30, 162))
        for i in range(MAX_WARNINGS):
            centre = (174 + i * 40, 172)
            if i < game.warnings:
                pygame.draw.circle(self.screen, RED, centre, 14)
            else:
                pygame.draw.circle(self.screen, GREY, centre, 14, 2)
        self.text(f"{game.warnings}/{MAX_WARNINGS}", self.medium, WHITE,
                  (170 + ANSWERS_NEEDED * 40, 162))

        # Top right: webcam preview and the angles (for tuning settings.py).
        px = self.width - PREVIEW_SIZE[0] - 20
        self.preview(camera_surface, px, 20)
        self.text(f"yaw {yaw:+.0f}   pitch {pitch:+.0f}   {fps:.0f} fps", self.small, GREY,
                  (px, 266))
        if tracking_note:
            # e.g. "face lost..." or "head down": the face is not tracked
            # right now, and the game is guessing the direction.
            self.text(tracking_note, self.small, YELLOW, (px + 230, 266))

        # Middle: the three options, the active one lit up.
        for i, (label, directions, colour) in enumerate(OPTION_BOXES):
            box = pygame.Rect(30 + i * 310, 300, 280, 90)
            if direction in directions:
                pygame.draw.rect(self.screen, colour, box, border_radius=10)
                self.text(label, self.medium, BACKGROUND, box.center, center=True)
            else:
                pygame.draw.rect(self.screen, GREY, box, 2, border_radius=10)
                self.text(label, self.medium, GREY, box.center, center=True)

        # Bottom: the two bars.
        bar_x, bar_width = 190, self.width - 190 - 30
        self.text("Copying", self.medium, WHITE, (30, 436))
        self.bar(bar_x, 430, bar_width, 34, game.copy_progress, GREEN)

        # The suspicion bar has two parts: the free grace time (yellow), then
        # the part that leads to a warning (red), split by a white marker.
        self.text("Suspicion", self.medium, WHITE, (30, 496))
        grace_width = int(bar_width * STARE_GRACE_TIME / (STARE_GRACE_TIME + STARE_FILL_TIME))
        grace_fraction = min(game.stare_time / STARE_GRACE_TIME, 1.0)
        self.bar(bar_x, 490, bar_width, 34, 0, RED)  # empty background
        if grace_fraction > 0:
            pygame.draw.rect(self.screen, YELLOW,
                             (bar_x, 490, int(grace_width * grace_fraction), 34), border_radius=6)
        if game.suspicion > 0:
            pygame.draw.rect(self.screen, RED,
                             (bar_x + grace_width, 490,
                              int((bar_width - grace_width) * game.suspicion), 34))
        pygame.draw.line(self.screen, WHITE, (bar_x + grace_width, 484),
                         (bar_x + grace_width, 529), 3)

        self.text("Q = quit    R = restart    C = recalibrate", self.small, GREY, (30, 568))

        # On top of everything: the warning popup (hidden under pause/end
        # screens, where it would clash with their text).
        if game.popup_text and show_popup:
            self.popup(game.popup_text)

    def popup(self, message):
        image = self.medium.render(message, True, WHITE)
        box = image.get_rect(center=(self.width // 2, self.height // 2 - 60)).inflate(60, 50)
        pygame.draw.rect(self.screen, RED, box, border_radius=12)
        pygame.draw.rect(self.screen, WHITE, box, 3, border_radius=12)
        self.screen.blit(image, image.get_rect(center=box.center))

    def draw_paused(self):
        """Drawn on top of the game screen while no face is seen."""
        self.darken()
        cx, cy = self.width // 2, self.height // 2
        self.text("Face not found", self.huge, RED, (cx, cy - 30), center=True)
        self.text("Game paused - look at the camera to continue", self.medium, WHITE,
                  (cx, cy + 30), center=True)

    def draw_end(self, game):
        """Drawn on top of the last game screen when the game is over."""
        self.darken(200)
        cx, cy = self.width // 2, self.height // 2
        if game.state == "WON":
            self.text("All answers filled!", self.huge, GREEN, (cx, cy - 50), center=True)
            self.text("You win", self.big, WHITE, (cx, cy + 10), center=True)
        else:
            self.text("Too many warnings", self.huge, RED, (cx, cy - 50), center=True)
            self.text("Game over", self.big, WHITE, (cx, cy + 10), center=True)
        self.text("R = play again    Q = quit", self.medium, GREY, (cx, cy + 80), center=True)
