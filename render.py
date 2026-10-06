"""
Drawing: everything the player sees.

The game screen is the classroom picture (assets/images/classroom_*.jpeg),
with see-through strips on top: answers, warnings and the exam clock at the
top, the two bars at the bottom, the webcam preview on the right.

The classroom with the teacher is only shown while the player looks at the
screen. Looking away shows what the player looks at instead (their own paper,
or a neighbour's paper) with no teacher in it, so the teacher can only be
checked by really looking (and heard, through the sounds).

Each draw_... function paints one whole screen onto the pygame window. They
only read the game's state; they never change it.
"""

import os

import cv2
import pygame

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from game import WON, GRACE_PART, UNKNOWN
from settings import CALIBRATION_TIME, ANSWERS_NEEDED, MAX_WARNINGS, COPY_TIME, CLASSROOM_TOP

# Colours are (Red, Green, Blue) in pygame, not (Blue, Green, Red) as in OpenCV!
BACKGROUND = (25, 28, 35)
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GREY = (110, 115, 125)
DARK_GREY = (55, 60, 70)
GREEN = (70, 200, 110)
YELLOW = (240, 200, 60)
RED = (220, 60, 60)
BLUE = (80, 150, 240)

PREVIEW_SIZE = (240, 180)      # webcam preview in the game, pixels
BIG_PREVIEW_SIZE = (480, 360)  # webcam preview on the start screen, pixels
TOP_BAR = 56                   # height of the strip at the top, pixels
BOTTOM_BAR = 80                # height of the strip at the bottom, pixels
CLOCK_RED_BELOW = 15           # seconds; the exam clock turns red under this

IMAGE_FOLDER = os.path.join("assets", "images")
CLASSROOM_IMAGES = ["classroom_board_busy", "classroom_board_watching",
                    "classroom_desk_busy", "classroom_desk_watching"]
# What the player sees while looking away. None of these show the teacher.
LOOK_AWAY_IMAGES = {
    DOWN: "classroom_desk_looking_down",
    LEFT: "classroom_desk_looking_left",
    RIGHT: "classroom_desk_looking_right",
}
# The neighbour's paper once you have read it: the letter (or "?") written
# on it. "left_B" = the left neighbour with B circled on their paper.
SIDE_NAMES = {LEFT: "left", RIGHT: "right"}
PAPER_IMAGES = [f"{SIDE_NAMES[side]}_{shown}" for side in (LEFT, RIGHT)
                for shown in ["A", "B", "C", "D", "unknown"]]
LOOK_AWAY_STRIP = 70           # height of the strip with the "Copying from..." text, pixels
# Where each neighbour's paper is in their picture (window pixels). If a
# paper picture is missing, the letter is drawn in a white note above it.
PAPER_SPOT = {LEFT: (460, 300), RIGHT: (630, 310)}
NOTE_SIZE = (100, 90)          # the note with the letter, pixels
# Where the answer lines 1-5 are in the "looking down" picture (window pixels).
OWN_ANSWER_X = 410
OWN_ANSWER_Y = [310, 352, 397, 440, 487]
PENCIL = (40, 50, 90)          # colour of the letters you write
ORANGE = (240, 140, 40)

# Which neighbour, for the look-away text ("Copying answer 2 from the left")
LOOK_AWAY = {
    LEFT: "from the left",
    RIGHT: "from the right",
}
# The disclaimer shown when the game opens: (text, colour). Satire, but the
# last line is meant seriously.
DISCLAIMER_LINES = [
    ("This game does not represent any real-life situation.", WHITE),
    ("Any resemblance to real exams, classrooms or professors", WHITE),
    ("is purely coincidental (and slightly suspicious).", WHITE),
    ("It is purely for entertainment purposes.", WHITE),
    ("No neighbours' answers were harmed in the making of this game.", GREY),
    ("We love our professor and we respect academic honesty.", YELLOW),
]
END_TEXTS = {   # lose_reason -> big text on the end screen
    "caught": "Caught copying!",
    "warnings": "Too many warnings",
    "time": "Time's up",
}


def camera_to_surface(frame, size=PREVIEW_SIZE):
    """Turn an OpenCV webcam frame into a smaller, mirrored pygame image."""
    small = cv2.resize(cv2.flip(frame, 1), size)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(rgb.tobytes(), size, "RGB")


def load_classroom(name, width, height):
    """
    Load one classroom picture and fit it to the window: scale it to the
    window's width, then cut CLASSROOM_TOP pixels off the top (mostly ceiling)
    and whatever doesn't fit off the bottom.
    """
    image = pygame.image.load(os.path.join(IMAGE_FOLDER, name + ".jpeg")).convert()
    scaled_height = image.get_height() * width // image.get_width()
    image = pygame.transform.smoothscale(image, (width, scaled_height))
    return image.subsurface((0, CLASSROOM_TOP, width, height)).copy()


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        # Fonts are loaded once; None = pygame's built-in font.
        self.giant = pygame.font.SysFont(None, 96)
        self.huge = pygame.font.SysFont(None, 72)
        self.big = pygame.font.SysFont(None, 52)
        self.medium = pygame.font.SysFont(None, 34)
        self.small = pygame.font.SysFont(None, 24)
        # The "Calibrate" button on the start screen. main.py checks clicks on it.
        self.button_rect = pygame.Rect(0, 0, 300, 60)
        self.button_rect.center = (self.width // 2, 500)
        # Loaded once at the start, not every frame: loading and scaling are slow.
        self.classroom = {name: load_classroom(name, self.width, self.height)
                          for name in CLASSROOM_IMAGES + list(LOOK_AWAY_IMAGES.values())}
        # The paper pictures are optional: a missing one falls back to the note.
        for name in PAPER_IMAGES:
            if os.path.exists(os.path.join(IMAGE_FOLDER, name + ".jpeg")):
                self.classroom[name] = load_classroom(name, self.width, self.height)

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def text(self, message, font, colour, pos, center=False):
        image = font.render(message, True, colour)
        rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
        self.screen.blit(image, rect)
        return rect

    def darken(self, alpha=170, rect=None):
        """
        Lay a see-through black sheet over whatever is already drawn: over
        the whole window, or only over `rect` (x, y, width, height).
        alpha: 0 = invisible, 255 = fully black.
        """
        x, y, width, height = rect or (0, 0, self.width, self.height)
        sheet = pygame.Surface((width, height), pygame.SRCALPHA)
        sheet.fill((0, 0, 0, alpha))
        self.screen.blit(sheet, (x, y))

    def bar(self, x, y, width, height, fraction, colour):
        pygame.draw.rect(self.screen, DARK_GREY, (x, y, width, height), border_radius=6)
        if fraction > 0:
            pygame.draw.rect(self.screen, colour, (x, y, int(width * fraction), height),
                             border_radius=6)

    def answer_boxes(self, game, x, y, graded=False):
        """
        One box per question with the letter you wrote. graded=True (end
        screen) colours them: green = right, red = wrong.
        """
        for i in range(ANSWERS_NEEDED):
            box = pygame.Rect(x + i * 30, y, 22, 22)
            if i < game.answers:
                right = game.written[i] == game.right_letters[i]
                colour = (GREEN if right else RED) if graded else BLUE
                pygame.draw.rect(self.screen, colour, box, border_radius=4)
                self.text(game.written[i], self.small, BACKGROUND, box.center, center=True)
            else:
                pygame.draw.rect(self.screen, GREY, box, 2, border_radius=4)

    def neighbour_picture(self, game, side):
        """
        The picture of a neighbour. Before the copy bar is full
        (paper_shows() is None) it is the plain one, so nothing gives the
        answer away; after it, the one with the letter or "?" on their paper.
        """
        shown = game.paper_shows(side)
        if shown is None:
            return LOOK_AWAY_IMAGES[side]
        name = f"{SIDE_NAMES[side]}_{'unknown' if shown == UNKNOWN else shown}"
        return name if name in self.classroom else None

    def neighbour_note(self, side, shown):
        """The letter (or "?") read from a neighbour, on a white note above their paper."""
        note = pygame.Rect(0, 0, *NOTE_SIZE)
        note.midbottom = PAPER_SPOT[side]
        # A small triangle pointing down at the paper, like a speech bubble.
        tip = (note.centerx, note.bottom + 18)
        pygame.draw.polygon(self.screen, WHITE, [(note.centerx - 14, note.bottom - 2),
                                                 (note.centerx + 14, note.bottom - 2), tip])
        pygame.draw.rect(self.screen, WHITE, note, border_radius=12)
        colour = ORANGE if shown == UNKNOWN else PENCIL
        self.text(shown, self.giant, colour, note.center, center=True)

    def look_away_texts(self, game, direction):
        """The two lines in the look-away strip: what is happening, and a hint."""
        q = game.question() + 1
        if direction == DOWN:
            if game.can_write():
                first = f"Press A, B, C or D to write answer {q}"
            else:
                first = f"Read answer {q} from a neighbour first"
            # Looking at the paper you hear nothing either (see teacher.sounds()).
            return first, "You can't see or hear the teacher"
        shown = game.paper_shows(direction)
        if shown is None:
            first = f"Copying answer {q} {LOOK_AWAY[direction]}"
        elif shown == UNKNOWN:
            first = "They don't know this one - try the other side"
        else:
            first = "Remember it, then look at your paper and write it"
        return first, "You can't see the teacher - listen!"

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
            message, colour = "Face not found - move into the camera", RED
        elif seconds_left is None:
            message, colour = "Sit normally, look at the screen, then press Calibrate", WHITE
        else:
            message, colour = "Keep looking at the screen...", YELLOW
        self.text(message, self.medium, colour, (cx, 420), center=True)

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

        self.text("In the game:  A/B/C/D = write answer    Q = quit    R = restart    "
                  "K = recalibrate    T = show the teacher (testing)",
                  self.small, GREY, (cx, 575), center=True)

    def draw_disclaimer(self):
        """The first screen: a satirical warning. Space or a click continues."""
        self.screen.fill(BACKGROUND)
        cx = self.width // 2
        self.text("WARNING", self.huge, RED, (cx, 90), center=True)
        y = 170
        for message, colour in DISCLAIMER_LINES:
            self.text(message, self.medium, colour, (cx, y), center=True)
            y += 48
        self.text("Press Space to solemnly swear you will never try this in a real exam",
                  self.small, GREY, (cx, 560), center=True)

    def draw_game(self, game, teacher, direction, view, camera_surface, yaw, pitch, fps,
                  tracking_note, show_teacher_state):
        """
        view: how visible the classroom is, 0 = black (looking away) to
        1 = fully shown. main.py raises it over FADE_TIME after the player
        looks at the screen.
        """
        cx = self.width // 2

        # The classroom, or what you look at while looking away.
        if view > 0:
            self.screen.blit(self.classroom[teacher.image_name()], (0, 0))
            if view < 1:
                self.darken(int(255 * (1 - view)))   # fading in from black
        elif direction in LOOK_AWAY_IMAGES:
            if direction == DOWN:
                self.screen.blit(self.classroom[LOOK_AWAY_IMAGES[DOWN]], (0, 0))
                # Your answers so far, "handwritten" on the answer lines.
                for i, letter in enumerate(game.written):
                    self.text(letter, self.big, PENCIL, (OWN_ANSWER_X, OWN_ANSWER_Y[i]),
                              center=True)
                strip_top = TOP_BAR   # at the top: lines 4 and 5 are at the bottom
            else:
                picture = self.neighbour_picture(game, direction)
                if picture is not None:
                    self.screen.blit(self.classroom[picture], (0, 0))
                else:
                    # No picture with that letter: the plain one with a note.
                    self.screen.blit(self.classroom[LOOK_AWAY_IMAGES[direction]], (0, 0))
                    self.neighbour_note(direction, game.paper_shows(direction))
                # Just above the bars, so it does not cover the neighbour's paper.
                strip_top = self.height - BOTTOM_BAR - LOOK_AWAY_STRIP
            first, hint = self.look_away_texts(game, direction)
            self.darken(170, (0, strip_top, self.width, LOOK_AWAY_STRIP))
            self.text(first, self.medium, WHITE, (cx, strip_top + 22), center=True)
            self.text(hint, self.small, GREY, (cx, strip_top + 50), center=True)
        else:
            # Just turned back to the screen: black before the fade-in starts.
            self.screen.fill(BLACK)

        # Top strip: answers, warnings, exam clock, tracking numbers.
        self.darken(170, (0, 0, self.width, TOP_BAR))
        self.text("Answers", self.small, WHITE, (16, 20))
        self.answer_boxes(game, 96, 16)

        self.text("Warnings", self.small, WHITE, (270, 20))
        for i in range(MAX_WARNINGS):
            centre = (365 + i * 30, 27)
            if i < game.warnings:
                pygame.draw.circle(self.screen, RED, centre, 10)
            else:
                pygame.draw.circle(self.screen, GREY, centre, 10, 2)

        seconds = int(game.time_left + 0.999)   # round up: "0:00" only when time is up
        clock_colour = RED if game.time_left < CLOCK_RED_BELOW else WHITE
        self.text(f"{seconds // 60}:{seconds % 60:02d}", self.big, clock_colour,
                  (cx + 60, TOP_BAR // 2), center=True)

        self.text(f"yaw {yaw:+.0f}  pitch {pitch:+.0f}  {fps:.0f} fps", self.small, GREY,
                  (self.width - 250, 12))
        # e.g. "face lost..." or "head down": the face is not tracked right
        # now, and the game is guessing the direction.
        self.text(tracking_note, self.small, YELLOW, (self.width - 250, 32))

        # Right: webcam preview, under the top strip.
        self.preview(camera_surface, self.width - PREVIEW_SIZE[0] - 12, TOP_BAR + 8)

        # Testing aid (D key): name the teacher's state.
        if show_teacher_state:
            self.text(f"teacher: {teacher.state} at the {teacher.place}", self.medium,
                      YELLOW, (16, TOP_BAR + 12))

        # Bottom strip: the two bars.
        top = self.height - BOTTOM_BAR
        self.darken(170, (0, top, self.width, BOTTOM_BAR))
        bar_x, bar_width = 120, self.width - 120 - 20
        # The copy bar shows the neighbour you look at, or else the one you
        # got furthest with.
        if direction in game.copy_time:
            copied = game.copy_time[direction]
        else:
            copied = max(game.copy_time.values())
        self.text("Copying", self.small, WHITE, (16, top + 14))
        self.bar(bar_x, top + 10, bar_width, 24, min(1.0, copied / COPY_TIME), GREEN)

        # Suspicion: yellow during the free staring time, red after it, and red
        # once the teacher has seen you copying (then it fills fast). The white
        # line marks where the free staring time ends.
        self.text("Suspicion", self.small, WHITE, (16, top + 50))
        suspicion = game.suspicion()
        danger = suspicion >= GRACE_PART or game.seen_copying
        self.bar(bar_x, top + 46, bar_width, 24, suspicion, RED if danger else YELLOW)
        marker_x = bar_x + bar_width * GRACE_PART
        pygame.draw.line(self.screen, WHITE, (marker_x, top + 42), (marker_x, top + 74), 3)

    def draw_popup(self, message):
        """A red box with a message, drawn on top of the game screen."""
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
        if game.state == WON:
            self.text("Exam handed in!", self.huge, GREEN, (cx, cy - 70), center=True)
            self.text(f"{game.correct_count()}/{ANSWERS_NEEDED} correct", self.big, WHITE,
                      (cx, cy - 10), center=True)
            # Which ones were right (green) and wrong (red).
            self.answer_boxes(game, cx - (ANSWERS_NEEDED * 30 - 8) // 2, cy + 30, graded=True)
        else:
            self.text(END_TEXTS[game.lose_reason], self.huge, RED, (cx, cy - 50), center=True)
            self.text("Game over", self.big, WHITE, (cx, cy + 10), center=True)
        self.text("R = play again    Q = quit", self.medium, GREY, (cx, cy + 80), center=True)
