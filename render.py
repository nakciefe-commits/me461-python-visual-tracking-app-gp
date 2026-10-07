"""
Drawing: everything the player sees.

The classroom is shown when facing forward; the player's paper is shown only
when looking down. Sideways looks show one neighbour question, slowly focusing.

Neighbours' marks are visible on their papers; only keyboard input writes
onto the player's own paper. The teacher stays hidden behind the desk view.

Each draw_... function paints one whole screen onto the pygame window. They
only read the game's state; they never change it.
"""

import os

import cv2
import pygame

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from game import PLAYING, WON, GRACE_PART
from settings import (CALIBRATION_TIME, ANSWERS_NEEDED, MAX_WARNINGS, CLASSROOM_TOP,
                      ANSWER_CHOICES, PAPER_RECT, NEIGHBOUR_PAPER_RECT,
                      NEIGHBOUR_QUESTION_HEIGHT, PAPER_BLUR_SIGMA, PAPER_BLUR_WORK_SIGMA,
                      PAPER_QUESTIONS_PER_PAGE, PAPER_PADDING, PAPER_HEADER_HEIGHT,
                      PAPER_FOOTER_HEIGHT, PAPER_FONT_SIZE,
                      PAPER_SMALL_FONT_SIZE, PAPER_OPTION_RADIUS,
                      PAPER_SHADOW_OFFSET, PAPER_BORDER_WIDTH, PAPER_CORNER_RADIUS,
                      PAPER_COLOUR, PAPER_INK, PAPER_LINE, PAPER_ACTIVE_COLOUR,
                      PAPER_MARK_COLOUR, DESK_COLOUR, DESK_LINE_COLOUR,
                      DESK_LINE_SPACING)

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
        self.huge = pygame.font.SysFont(None, 72)
        self.big = pygame.font.SysFont(None, 52)
        self.medium = pygame.font.SysFont(None, 34)
        self.small = pygame.font.SysFont(None, 24)
        # DejaVu Sans includes Turkish letters and arrow symbols on Linux.
        self.paper_font = pygame.font.SysFont("dejavusans", PAPER_FONT_SIZE)
        self.paper_small = pygame.font.SysFont("dejavusans", PAPER_SMALL_FONT_SIZE)
        # The "Calibrate" button on the start screen. main.py checks clicks on it.
        self.button_rect = pygame.Rect(0, 0, 300, 60)
        self.button_rect.center = (self.width // 2, 500)
        # Loaded once at the start, not every frame: loading and scaling are slow.
        self.classroom = {name: load_classroom(name, self.width, self.height)
                          for name in CLASSROOM_IMAGES}

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

    def preview(self, camera_surface, x, y, size=PREVIEW_SIZE):
        if camera_surface is not None:
            self.screen.blit(camera_surface, (x, y))
        pygame.draw.rect(self.screen, GREY, (x, y, *size), 2)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    def draw_desk(self):
        """A wooden desk gives papers a background without revealing the teacher."""
        self.screen.fill(DESK_COLOUR)
        for y in range(TOP_BAR, self.height, DESK_LINE_SPACING):
            pygame.draw.line(self.screen, DESK_LINE_COLOUR, (0, y), (self.width, y))

    def blur_paper(self, rect, clarity):
        """Blur only the neighbour paper, leaving the webcam and HUD readable."""
        if clarity >= 1.0:
            return
        # pygame arrays use (width, height, RGB); OpenCV expects (height, width, RGB).
        pixels = pygame.surfarray.array3d(self.screen.subsurface(rect)).swapaxes(0, 1)
        sigma = PAPER_BLUR_SIGMA * (1.0 - max(0.0, clarity))
        if sigma <= 0:
            return
        # Large Gaussian kernels are expensive. Blur a smaller image with the
        # same apparent radius, and use full resolution near the sharp endpoint.
        scale = min(1.0, PAPER_BLUR_WORK_SIGMA / sigma)
        if scale < 1.0:
            pixels = cv2.resize(pixels, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        blurred = cv2.GaussianBlur(pixels, (0, 0), sigmaX=sigma * scale,
                                   borderType=cv2.BORDER_REPLICATE)
        if scale < 1.0:
            blurred = cv2.resize(blurred, rect.size, interpolation=cv2.INTER_LINEAR)
        self.screen.blit(pygame.surfarray.make_surface(blurred.swapaxes(0, 1)), rect)

    def draw_exam_paper(self, game, direction):
        """Draw question lines and A..E bubbles directly; no extra image is needed."""
        neighbour = direction in (LEFT, RIGHT)
        rect = pygame.Rect(NEIGHBOUR_PAPER_RECT if neighbour else PAPER_RECT)
        marks = game.neighbour_answers[direction] if neighbour else game.player_answers
        title = ("SOL KOMŞUNUN KÂĞIDI" if direction == LEFT else "SAĞ KOMŞUNUN KÂĞIDI"
                 if neighbour else "SINAV KÂĞIDIN")
        header, footer = PAPER_HEADER_HEIGHT, PAPER_FOOTER_HEIGHT
        font, radius = self.paper_font, PAPER_OPTION_RADIUS
        left, right = rect.left + PAPER_PADDING, rect.right - PAPER_PADDING

        pygame.draw.rect(self.screen, DARK_GREY,
                         rect.move(PAPER_SHADOW_OFFSET, PAPER_SHADOW_OFFSET),
                         border_radius=PAPER_CORNER_RADIUS)
        pygame.draw.rect(self.screen, PAPER_COLOUR, rect, border_radius=PAPER_CORNER_RADIUS)
        pygame.draw.rect(self.screen, PAPER_LINE, rect, PAPER_BORDER_WIDTH,
                         border_radius=PAPER_CORNER_RADIUS)
        self.text(title, self.paper_font, PAPER_INK,
                  (left, rect.top + header // 4))
        self.text(f"Soru {game.active_question + 1} / {ANSWERS_NEEDED}",
                  self.paper_small, PAPER_MARK_COLOUR,
                  (right - PAPER_PADDING * 7, rect.top + header // 4))
        subtitle = "İşaretli şıkkı hatırla, sonra kendi kâğıdına dön." if neighbour else (
            "A, B, C, D, E ile cevapla. Ok tuşlarıyla soruyu değiştir.")
        self.text(subtitle, self.paper_small, PAPER_INK, (left, rect.top + header * 2 // 3))

        # Longer exams get pages; the selected question is always on the visible page.
        if neighbour:
            # Read just the current question: first Q1, then the next blank
            # question after writing. Revisiting a row shows that same row here.
            first, last = game.active_question, game.active_question + 1
            row_height = NEIGHBOUR_QUESTION_HEIGHT
            row_top = rect.top + header + (rect.height - header - footer - row_height) // 2
        else:
            first = game.active_question // PAPER_QUESTIONS_PER_PAGE * PAPER_QUESTIONS_PER_PAGE
            last = min(first + PAPER_QUESTIONS_PER_PAGE, ANSWERS_NEEDED)
            row_height = (rect.height - header - footer) // (last - first)
            row_top = rect.top + header
        option_step = (right - left) // len(ANSWER_CHOICES)
        for row, question in enumerate(range(first, last)):
            y = row_top + row * row_height
            if question == game.active_question:
                pygame.draw.rect(self.screen, PAPER_ACTIVE_COLOUR,
                                 (left, y, right - left, row_height),
                                 border_radius=PAPER_CORNER_RADIUS)
            self.text(f"{question + 1}. soru", font, PAPER_INK,
                      (left + PAPER_PADDING // 2, y))
            # Placeholder question text is just a printed line.
            line_y = y + font.get_height() // 2
            pygame.draw.line(self.screen, PAPER_LINE,
                             (left + PAPER_PADDING * 6, line_y), (right - PAPER_PADDING, line_y))
            choice_y = y + row_height * 3 // 4
            for column, choice in enumerate(ANSWER_CHOICES):
                x = left + PAPER_PADDING + column * option_step
                selected = marks[question] == choice
                pygame.draw.circle(self.screen, PAPER_MARK_COLOUR if selected else PAPER_LINE,
                                   (x, choice_y), radius, 0 if selected else PAPER_BORDER_WIDTH)
                self.text(choice, font, PAPER_MARK_COLOUR if selected else PAPER_INK,
                          (x + radius * 2, choice_y - font.get_height() // 2))

        hint = ("Kendi kâğıdına dönerek cevapla." if neighbour else
                "A B C D E: cevapla    ↑ ↓: soru seç    F2: kalibrasyon    F3: test")
        self.text(hint, self.paper_small, PAPER_INK,
                  (left, rect.bottom - footer + footer // 4))
        if neighbour:
            self.blur_paper(rect, game.paper_clarity)

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

        self.text("A B C D E = answer    Up / Down = question    "
                  "F2 = recalibrate    F3 = teacher test    Q = quit",
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

        # Forward shows the teacher without a paper. Down shows your own
        # paper; sideways shows the neighbour's current question through blur.
        if game.state == PLAYING and direction != SCREEN:
            self.draw_desk()
            self.draw_exam_paper(game, direction)
        elif view > 0:
            self.screen.blit(self.classroom[teacher.image_name()], (0, 0))
            if view < 1:
                self.darken(int(255 * (1 - view)))   # fading in from black
        else:
            self.screen.fill(BLACK)

        # Top strip: answers, warnings, exam clock, tracking numbers.
        self.darken(170, (0, 0, self.width, TOP_BAR))
        self.text("Answers", self.small, WHITE, (16, 20))
        for i in range(ANSWERS_NEEDED):
            box = (96 + i * 30, 16, 22, 22)
            if game.player_answers[i] is not None:
                pygame.draw.rect(self.screen, GREEN, box, border_radius=4)
            else:
                pygame.draw.rect(self.screen, GREY, box, 2, border_radius=4)

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

        # Testing aid (F3 key): name the teacher's state without hiding papers.
        if show_teacher_state:
            self.text(f"teacher: {teacher.state} at the {teacher.place}", self.medium,
                      YELLOW, (16, TOP_BAR + 12))

        # Bottom strip: writing instructions and the suspicion bar.
        top = self.height - BOTTOM_BAR
        self.darken(170, (0, top, self.width, BOTTOM_BAR))
        bar_x, bar_width = 120, self.width - 120 - 20
        if direction in (LEFT, RIGHT):
            instruction = f"Question {game.active_question + 1}: keep looking as the paper becomes clear."
        elif direction == SCREEN:
            instruction = "Looking at the teacher. Look down to see your own paper."
        else:
            instruction = (f"Question {game.active_question + 1}:  A B C D E = answer    "
                           "Up / Down = select question")
        self.text(instruction, self.small, WHITE, (16, top + 14))

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

    def draw_camera_wait(self, message):
        """The window stays responsive while camera startup/recovery runs elsewhere."""
        self.screen.fill(BACKGROUND)
        cx, cy = self.width // 2, self.height // 2
        self.text("Waiting for camera", self.big, YELLOW, (cx, cy - 70), center=True)
        # Driver errors can be much wider than the window; keep the status readable.
        words = message.split()
        line, y = "", cy - 15
        for word in words:
            candidate = (line + " " + word).strip()
            if line and self.small.size(candidate)[0] > self.width - 60:
                self.text(line, self.small, WHITE, (cx, y), center=True)
                y += self.small.get_linesize()
                line = word
            else:
                line = candidate
        self.text(line, self.small, WHITE, (cx, y), center=True)
        self.text("The exam is paused. Reconnecting automatically.", self.medium, GREY,
                  (cx, cy + 100), center=True)
        self.text("Close other camera apps or check CAMERA_INDEX in settings.py.",
                  self.small, GREY, (cx, cy + 145), center=True)
        self.text("Q / Esc = quit", self.medium, WHITE, (cx, self.height - 45), center=True)

    def draw_end(self, game):
        """Drawn on top of the last game screen when the game is over."""
        self.darken(200)
        cx, cy = self.width // 2, self.height // 2
        if game.state == WON:
            self.text("All answers correct!", self.huge, GREEN, (cx, cy - 50), center=True)
            self.text("You win", self.big, WHITE, (cx, cy + 10), center=True)
        else:
            self.text(END_TEXTS[game.lose_reason], self.huge, RED, (cx, cy - 50), center=True)
            self.text("Game over", self.big, WHITE, (cx, cy + 10), center=True)
        self.text(f"Correct answers: {game.correct_answers}/{ANSWERS_NEEDED}",
                  self.medium, WHITE, (cx, cy + 60), center=True)
        self.text("R = play again    Q = quit", self.medium, GREY, (cx, cy + 105), center=True)
