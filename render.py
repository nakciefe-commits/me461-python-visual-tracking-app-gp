"""
Drawing: everything the player sees.

The game screen is the classroom picture (assets/images/classroom_*.jpeg;
.jpg and .png work too),
with see-through strips on top: answers, warnings and the exam clock at the
top, the two bars at the bottom, the webcam preview on the right.

The classroom with the teacher is only shown while the player looks at the
screen. Looking away shows what the player looks at instead (their own paper,
or a neighbour's paper) with no teacher in it, so the teacher can only be
checked by really looking (and heard, through the sounds).

Everything is drawn in a neon 80s style, a bit like the game Hotline Miami.
The menus, the start and the loading screens have a pulsing pink/purple
background with turning light rays. Big texts are slanted, wobble, thump on
a "beat" and have pink and cyan "ghost" copies next to them. In the game the
strips are dark purple with a neon pink edge, and the bars are slanted. All
of that is just a few pictures redrawn a little differently every frame,
using the time `self.t` that main.py sets every frame.

Each draw_... function paints one whole screen onto the pygame window. They
only read the game's state; they never change it.
"""

import math
import os
import random
import time

import cv2
import numpy as np
import pygame

from head_tracker import DOWN, SCREEN, LEFT, RIGHT
from game import WON, GRACE_PART, UNKNOWN, WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE
from teacher import BOARD, DESK
from settings import (CALIBRATION_TIME, ANSWERS_NEEDED, MAX_WARNINGS, CLASSROOM_TOP,
                      WARNING_SCENE_TIME, TEACHER_APPROACH_TIME, CAUGHT_SCENE_TIME,
                      CAUGHT_EXCLAIM_TIME, GAME_OVER_TIME)

# Colours are (Red, Green, Blue) in pygame, not (Blue, Green, Red) as in OpenCV!
BLACK = (0, 0, 0)
WHITE = (240, 240, 240)
GREY = (110, 115, 125)
YELLOW = (240, 200, 60)

PREVIEW_SIZE = (240, 180)      # webcam preview in the game, pixels
BIG_PREVIEW_SIZE = (480, 360)  # webcam preview on the start screen, pixels
TOP_BAR = 56                   # height of the strip at the top, pixels
BOTTOM_BAR = 46                # height of the strip at the bottom (the suspicion bar), pixels
CLOCK_RED_BELOW = 15           # seconds; the exam clock turns red under this

IMAGE_FOLDER = os.path.join("assets", "images")
IMAGE_TYPES = (".jpeg", ".jpg", ".png")   # a picture may be saved as any of these
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
# The scenes (see game.py). Their pictures are optional: without them the
# warning scene only zooms in on the teacher, and the caught scene stays on
# the "!".
POINTING_IMAGE = "classroom_warning"   # the teacher points at you (warning)
CAUGHT_IMAGE = "classroom_caught"      # the teacher tears up your exam (caught)
# Pixels cut off the top of each of those pictures: less than CLASSROOM_TOP,
# because the teacher's head is high in them and the text strip covers the
# top. Measured on each picture, so his face stays under the strip.
SCENE_PICTURE_TOP = {POINTING_IMAGE: 120, CAUGHT_IMAGE: 60}
# Where the teacher's face is in each "watching" picture (window pixels): the
# scene zooms in on it, as if the teacher walks towards you.
TEACHER_FACE = {BOARD: (555, 190), DESK: (300, 185)}
APPROACH_ZOOM = 3.5            # how far the scene zooms in on the teacher (3.5 = so big, about as in the pointing picture)
FLASH_TIME = 0.25              # seconds of the white flash when the teacher arrives (hides the cut)
SHAKE_PIXELS = 14              # how far the screen shakes when the teacher arrives
SHAKE_TIME = 0.6               # seconds the shaking takes to calm down
SCENE_STRIP = 100              # pixels, height of the text strips at the top and bottom of a scene
ALERT_RED = (235, 30, 30)      # the Metal Gear "!"
EXCLAIM_ABOVE = 85             # pixels from the teacher's face up to the middle of the "!"
EXCLAIM_POP_TIME = 0.15        # seconds the "!" takes to pop from big to its size
CAUGHT_TEXTS = ("CAUGHT COPYING!", "YOUR EXAM: 0/5 - SEE YOU NEXT SEMESTER")
# What the teacher yells in the warning scene: one line per warning, in order
# (the last one is the warning that ends the game).
WARNING_LINES = [
    "\"DO NOT STARE AT ME! LOOK AT YOUR DAMN PAPER!\"",
    "\"YOU WANNA FAIL, YOU LITTLE RACCOON?\"",
    "\"IT IS OVER FOR YOU, YOU CHEATING NOODLE!\"",
]

# The game over screen: two logos with faces make fun of you, one line
# each, typed out like a chat app. One conversation per way of losing; each
# line is (who, text). When both lines are typed, both logos laugh.
GEMINI, CLAUDE = "GEMINI", "CLAUDE"   # Gemini drew the pictures, Claude wrote the code
GAME_OVER_CHAT = {
    "caught": [
        (GEMINI, "Copying from your neighbour? With HIM watching? Bold move."),
        (CLAUDE, "Maybe next semester you can study instead of copying."),
    ],
    "warnings": [
        (CLAUDE, "Man, you stared at the teacher like it was a Netflix show."),
        (GEMINI, "Maybe try looking at the teacher during class, not during the quiz."),
    ],
    "time": [
        (GEMINI, "Five questions, a whole quiz... and the paper is still empty."),
        (CLAUDE, "We made this entire game faster than you copied one answer."),
    ],
}
CHAT_START = 1.2               # seconds of "GAME OVER" alone before the chat starts
CHAT_LINE_TIME = 2.6           # seconds between the two chat lines
CHAT_TYPE_SPEED = 40           # letters per second the lines are typed
CHAT_TOP = 182                 # pixels, the middle of the first chat line
CHAT_ROW = 108                 # pixels between the chat lines
CHAT_MENU_TOP = 395            # pixels; after the chat, the end menu appears under it from here
CHAT_MENU_GAP = 64             # pixels between those menu items (a little tighter than in the other menus)
CHAT_LOGO_X = 105              # pixels from the side of the window to the middle of a logo
BUBBLE_MAX_WIDTH = 560         # pixels; longer lines wrap onto the next line
LOGO_RADIUS = 58               # pixels, the size of the logos
CLAUDE_ORANGE = (217, 119, 87)   # also the colour of Claude's speech bubble
GEMINI_BLUE = (70, 130, 240)     # also the colour of Gemini's speech bubble
# Gemini's star: these colours go round it (like the new Gemini logo), and
# the middle is lighter.
GEMINI_COLOURS = [(66, 133, 244), (52, 199, 120), (251, 200, 30), (240, 70, 80)]
# Claude's burst: the rays take these warm colours in turn; the middle goes
# from the first one to the last one.
CLAUDE_COLOURS = [(217, 119, 87), (245, 160, 80), (250, 120, 120), (255, 205, 140)]
OUTLINE = (60, 20, 40)           # dark outline around the logos, like a cartoon
CHEEKS = (255, 120, 160)         # rosy cheeks on the faces
LOGO_GLOW = {GEMINI: (110, 150, 255), CLAUDE: (255, 150, 80)}   # the glow behind each logo
GLOW_ALPHA = 170                 # 0-255, how bright the middle of the glow is
# The Claude logo's rays: (angle in degrees, length as a part of LOGO_RADIUS).
# Slightly uneven on purpose, like the real one.
CLAUDE_RAYS = [(0, 1.0), (31, 0.85), (58, 1.0), (92, 0.9), (121, 1.0), (149, 0.8),
               (180, 1.0), (211, 0.9), (238, 1.0), (272, 0.85), (301, 1.0), (329, 0.9)]
BLINK_EVERY = 3.2              # seconds between blinks
BLINK_TIME = 0.15              # seconds a blink takes
# Blurring the neighbour's view until it is sharp (game.paper_clarity()): the
# picture is shrunk, softened and stretched back. At clarity 0 it is shrunk to
# this part of its size, which makes it very blurry; at 1 it is not shrunk.
BLUR_SMALLEST = 0.03
BLUR_SOFTEN = 2                # pixels of extra softening on the shrunk picture
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
MONO_FONTS = [("couriernew", True), ("courier", True), ("nimbusmonops", True), ("dejavusansmono", True),
              ("liberationmono", True)]   # typewriter-looking fonts, first one found
# The "How to play" screen: (text, colour).
HELP_LINES = [
    ("You are in an exam. Copy all 5 answers without getting caught.", WHITE),
    ("Turn your head LEFT or RIGHT: their paper gets sharper as you keep looking.", WHITE),
    ("One neighbour knows the letter (A-D), the other one shows \"?\".", WHITE),
    ("Look DOWN at your paper and press A, B, C or D to write it.", WHITE),
    ("Look at the SCREEN to see the teacher. Busy teacher = safe to copy.", WHITE),
    ("Listen! \"Hmm\" means the teacher is about to look up.", YELLOW),
    ("Seen copying = caught. Staring while they watch = a warning (3 = out).", WHITE),
    ("Finish before the exam clock runs out.", WHITE),
    ("Keys: K recalibrate   T show the teacher   F11 fullscreen   Q quit", GREY),
]

# The screen before each game (a "chapter" screen) and its funny loading
# lines; each time one of them, at random.
LOADING_CHAPTER = "ME461 - CHAPTER 1"
LOADING_TITLE = "THE QUIZ"
LOADING_TIPS = [
    "Sharpening pencils...",
    "Finding a seat between two smart students...",
    "The teacher is making coffee...",
    "Hiding the phone under the desk...",
    "Practising an innocent face...",
    "Forgetting everything you studied...",
    "Counting the exits...",
]

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
CLOCK_PULSE = 0.25             # how much bigger the clock thumps each second at the end
BUTTON_TEXT = "CALIBRATE  (SPACE)"
BUTTON_HEIGHT = 60             # pixels, the Calibrate button on the start screen
BUTTON_PADDING = 45            # pixels between its text and its slanted ends (each side)
# (top, middle, bottom) colours the menu background slowly moves between:
# sunset tones, a little soft, with many tones in between.
MENU_PALETTES = [((255, 120, 175), (185, 55, 150), (40, 10, 75)),    # pink sunset
                 ((100, 175, 255), (125, 70, 200), (35, 12, 80)),    # blue to violet
                 ((255, 165, 100), (220, 80, 125), (60, 12, 72))]    # orange sunset
# Font files to try for the menus, in order: (name, bold). Impact looks most
# like the game; DejaVu Sans Bold comes with most Linux systems.
MENU_FONTS = [("impact", False), ("arialblack", False), ("dejavusans", True)]
COLOUR_CYCLE_TIME = 4.0        # seconds to move from one background palette to the next
RAY_COUNT = 12                 # light rays turning behind the title
RAY_SPEED = 0.15               # radians per second the rays turn
RAY_ALPHA = 60                 # 0-255, how visible the rays are in the middle (they fade outwards)
RAY_LENGTH = 1200              # pixels, long enough to reach past the corners
SCANLINE_GAP = 3               # pixels between the dark "old TV" lines
SCANLINE_ALPHA = 20            # 0-255, how dark those lines are
VIGNETTE_ALPHA = 150           # 0-255, how dark the corners of the menus get
GRAIN_ALPHA = 10               # 0-255, a very light film grain that hides colour steps
GLOW_BLUR = 10                 # pixels; how soft the glow behind the menu texts is
GHOST_ALPHA = 150              # 0-255, how strong the pink and cyan copies of the text are
GHOST_OFFSET = 4               # pixels the pink and cyan copies of the text are moved
SHADOW_OFFSET = 6              # pixels the shadow is moved down-right
BEAT_TIME = 0.5                # seconds per "beat": the title thumps bigger on each one
TITLE_PULSE = 0.06             # how much bigger the title is on a beat (0.06 = 6 %)
TITLE_WOBBLE = 4               # degrees the title rocks left and right
TITLE_WOBBLE_SPEED = 1.3       # radians per second of that rocking
ITEM_WOBBLE = 5                # degrees the selected menu item rocks
ITEM_WOBBLE_SPEED = 4.0        # radians per second of that rocking
SELECTED_SCALE = 1.2           # the selected item is drawn this much bigger
MENU_ITEM_GAP = 68             # pixels between menu items
TITLE_MAX_WIDTH = 800          # pixels; a longer title is shrunk to fit, wobble included
MENU_PREVIEW_SIZE = (192, 144) # webcam preview in the menus, pixels
INDICATOR_HEIGHT = 28          # pixels, the "HEAD CONTROL" / "KEYBOARD" box in the menus
MENU_HINT = ("HEAD: tilt up/down = choose   turn right = select   turn left = back"
             "        KEYS: arrows, Enter, Esc")

END_TEXTS = {   # lose_reason -> big text on the end screen
    "caught": "CAUGHT COPYING!",
    "warnings": "TOO MANY WARNINGS",
    "time": "TIME'S UP",
}


def camera_to_surface(frame, size=PREVIEW_SIZE):
    """Turn an OpenCV webcam frame into a smaller, mirrored pygame image."""
    small = cv2.resize(cv2.flip(frame, 1), size)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(rgb.tobytes(), size, "RGB")


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


def image_file(name):
    """The path of picture `name` in IMAGE_FOLDER (.jpeg, .jpg or .png), or None if missing."""
    for ending in IMAGE_TYPES:
        path = os.path.join(IMAGE_FOLDER, name + ending)
        if os.path.exists(path):
            return path
    return None


def load_classroom(name, width, height, top=CLASSROOM_TOP):
    """
    Load one classroom picture and fit it to the window: scale it to the
    window's width, then cut `top` pixels off the top (mostly ceiling)
    and whatever doesn't fit off the bottom.
    """
    image = pygame.image.load(image_file(name)).convert()
    scaled_height = image.get_height() * width // image.get_width()
    image = pygame.transform.smoothscale(image, (width, scaled_height))
    return image.subsurface((0, top, width, height)).copy()


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
        # Slanted bold fonts for the neon style (see menu_font()).
        self.menu_title_font = menu_font(84)
        self.menu_item_font = menu_font(48)
        self.hud_huge = menu_font(60)
        self.hud_big = menu_font(38)
        self.hud = menu_font(26)
        self.hud_small = menu_font(18)
        self.t = 0.0   # seconds since the program started; main.py sets it every frame
        self.exclaim = self.make_exclaim()   # the Metal Gear "!", made once
        self.type_font = mono_font(19)
        self.type_title_font = mono_font(34)
        self.desk = self.make_desk()          # the wooden desk behind the notice
        self.stamp = self.make_stamp()
        self.logos = {GEMINI: self.make_gemini_logo(), CLAUDE: self.make_claude_logo()}
        self.glows = {who: self.make_glow(colour) for who, colour in LOGO_GLOW.items()}
        # Where each menu item was drawn last frame; main.py checks mouse clicks on them.
        self.menu_rects = []
        # Made once: the see-through layers drawn on top of the menu background.
        self.rays = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.scanlines = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, SCANLINE_GAP):
            pygame.draw.line(self.scanlines, (0, 0, 0, SCANLINE_ALPHA), (0, y), (self.width, y))
        self.make_menu_layers()
        self.neon_cache = {}   # (text, colour) -> neon picture, so titles are made once
        # The "Calibrate" button on the start screen. main.py checks clicks on it.
        # Sized from its text, so the text never touches the slanted edges
        # whatever font this computer has.
        text_width = self.hud.size(BUTTON_TEXT)[0]
        self.button_rect = pygame.Rect(0, 0, text_width + 2 * BUTTON_PADDING, BUTTON_HEIGHT)
        self.button_rect.center = (self.width // 2, 500)
        # Loaded once at the start, not every frame: loading and scaling are slow.
        self.classroom = {name: load_classroom(name, self.width, self.height)
                          for name in CLASSROOM_IMAGES + list(LOOK_AWAY_IMAGES.values())}
        # The paper pictures are optional: a missing one falls back to the note.
        for name in PAPER_IMAGES:
            if image_file(name):
                self.classroom[name] = load_classroom(name, self.width, self.height)
        for name, top in SCENE_PICTURE_TOP.items():
            if image_file(name):
                self.classroom[name] = load_classroom(name, self.width, self.height, top)

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
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

    def answer_boxes(self, game, x, y, graded=False):
        """
        One box per question with the letter you wrote. graded=True (end
        screen) colours them: green = right, red = wrong.
        """
        for i in range(ANSWERS_NEEDED):
            box = pygame.Rect(x + i * 30, y, 22, 22)
            if i < game.answers:
                right = game.written[i] == game.right_letters[i]
                colour = (NEON_GREEN if right else NEON_RED) if graded else NEON_CYAN
                pygame.draw.rect(self.screen, colour, box)
                self.text(game.written[i], self.hud_small, SHADOW, box.center, center=True)
            else:
                pygame.draw.rect(self.screen, NEON_PINK, box, 2)

    def neighbour_picture(self, game, side):
        """
        The picture of a neighbour with what is on their paper (the letter
        circled, or "?"). It is shown from the start of a look, but blurred
        until game.paper_clarity() reaches 1, so it cannot be read early.
        None if that picture is missing (then the plain one and a note).
        """
        says = game.paper_says(side)
        if says is None:
            return LOOK_AWAY_IMAGES[side]   # after the last question
        name = f"{SIDE_NAMES[side]}_{'unknown' if says == UNKNOWN else says}"
        return name if name in self.classroom else None

    def blurred(self, picture, clarity):
        """
        The picture blurred: clarity 0 = very blurry, 1 = sharp. Shrinking it
        and stretching it back loses the details (the smaller, the blurrier);
        a small blur on the shrunk picture hides its blocks. Quick enough to
        do every frame. The curve (clarity²) keeps it unreadable for a while,
        then it sharpens fast at the end.
        """
        if clarity >= 1:
            return picture
        part = BLUR_SMALLEST + (1 - BLUR_SMALLEST) * clarity ** 2
        small_size = (max(2, int(self.width * part)), max(2, int(self.height * part)))
        small = pygame.transform.smoothscale(picture, small_size)
        small = pygame.transform.gaussian_blur(small, BLUR_SOFTEN)
        return pygame.transform.smoothscale(small, (self.width, self.height))

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
            first = f"Reading answer {q} {LOOK_AWAY[direction]} - keep looking"
        elif shown == UNKNOWN:
            first = "They don't know this one - try the other side"
        else:
            first = "Remember it, then look at your paper and write it"
        return first, "You can't see the teacher - listen!"

    # ------------------------------------------------------------------
    # Neon style helpers (menus, and the big texts in the game)
    # ------------------------------------------------------------------
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

    def preview(self, camera_surface, x, y, size=PREVIEW_SIZE):
        """The webcam picture with a neon frame."""
        if camera_surface is not None:
            self.screen.blit(camera_surface, (x, y))
        pygame.draw.rect(self.screen, NEON_CYAN, (x, y, *size), 3)

    # ------------------------------------------------------------------
    # Screens
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # The disclaimer: an official notice
    # ------------------------------------------------------------------
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

    def draw_loading(self, progress, tip_number):
        """
        The short screen before each game, like a chapter screen in Hotline
        Miami: the exam's name and date, a funny loading line and a bar.
        progress: 0..1 (main.py makes it fill unevenly, like a real one).
        tip_number: which line of LOADING_TIPS to show.
        """
        self.menu_background()
        cx = self.width // 2
        self.shadow_text(LOADING_CHAPTER, self.hud, NEON_CYAN, (cx, 150), center=True)
        self.menu_title(LOADING_TITLE, 235)
        # Today's date, e.g. "7 OCTOBER 2026".
        date = time.strftime("%d %B %Y").lstrip("0").upper()
        self.shadow_text(date, self.hud, WHITE, (cx, 320), center=True)

        self.shadow_text(LOADING_TIPS[tip_number], self.medium, NEON_YELLOW, (cx, 410),
                         center=True)
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
                # Centred left of the webcam preview, which is at the top right too.
                text_x = (self.width - PREVIEW_SIZE[0] - 12) // 2
            else:
                picture = self.neighbour_picture(game, direction)
                clarity = game.paper_clarity(direction)
                if picture is not None:
                    self.screen.blit(self.blurred(self.classroom[picture], clarity), (0, 0))
                else:
                    # No picture with that letter: the plain one, and a note once read.
                    plain = self.classroom[LOOK_AWAY_IMAGES[direction]]
                    self.screen.blit(self.blurred(plain, clarity), (0, 0))
                    if game.paper_shows(direction) is not None:
                        self.neighbour_note(direction, game.paper_shows(direction))
                # Just above the bars, so it does not cover the neighbour's paper.
                strip_top = self.height - BOTTOM_BAR - LOOK_AWAY_STRIP
                text_x = cx
            first, hint = self.look_away_texts(game, direction)
            self.darken(HUD_ALPHA, (0, strip_top, self.width, LOOK_AWAY_STRIP), HUD_PURPLE)
            self.shadow_text(first, self.hud, WHITE, (text_x, strip_top + 24), center=True)
            self.shadow_text(hint, self.hud_small, NEON_CYAN, (text_x, strip_top + 52),
                             center=True)
        else:
            # Just turned back to the screen: black before the fade-in starts.
            self.screen.fill(BLACK)

        # Top strip: answers, warnings, exam clock, tracking numbers.
        self.hud_strip(0, TOP_BAR, line_at_top=False)
        # Each label is measured, so the boxes after it never overlap it
        # whichever font this computer has.
        label = self.shadow_text("ANSWERS", self.hud_small, NEON_CYAN, (16, 16))
        self.answer_boxes(game, label.right + 12, 16)
        label = self.shadow_text("WARNINGS", self.hud_small, NEON_CYAN,
                                 (label.right + 12 + ANSWERS_NEEDED * 30 + 20, 16))
        circles_x = label.right + 24
        for i in range(MAX_WARNINGS):
            centre = (circles_x + i * 30, 27)
            if i < game.warnings:
                pygame.draw.circle(self.screen, NEON_PINK, centre, 10)
            pygame.draw.circle(self.screen, WHITE, centre, 10, 2)

        # The clock: calm yellow, then pink and thumping on every second when
        # time is running out.
        seconds = int(game.time_left + 0.999)   # round up: "0:00" only when time is up
        clock = f"{seconds // 60}:{seconds % 60:02d}"
        clock_spot = (circles_x + MAX_WARNINGS * 30 + 70, TOP_BAR // 2)   # after the circles
        if game.time_left < CLOCK_RED_BELOW:
            thump = 1 - (game.time_left % 1)   # 0 right at each new second, growing
            scale = 1 + CLOCK_PULSE * (1 - thump) ** 3
            self.blit_turned(self.neon_text(clock, self.hud_big, NEON_PINK), clock_spot,
                             TEXT_WOBBLE * math.sin(self.t * 8), scale)
        else:
            self.blit_turned(self.neon_text(clock, self.hud_big, NEON_YELLOW), clock_spot)

        self.text(f"yaw {yaw:+.0f}  pitch {pitch:+.0f}  {fps:.0f} fps", self.small, GREY,
                  (self.width - 250, 12))
        # e.g. "face lost..." or "head down": the face is not tracked right
        # now, and the game is guessing the direction.
        self.text(tracking_note, self.small, NEON_YELLOW, (self.width - 250, 32))

        # Right: webcam preview, under the top strip.
        self.preview(camera_surface, self.width - PREVIEW_SIZE[0] - 12, TOP_BAR + 8)

        # Testing aid (T key): name the teacher's state.
        if show_teacher_state:
            self.shadow_text(f"teacher: {teacher.state} at the {teacher.place}", self.hud,
                             NEON_YELLOW, (16, TOP_BAR + 12))

        # Bottom strip: the two bars.
        top = self.height - BOTTOM_BAR
        self.hud_strip(top, BOTTOM_BAR, line_at_top=True)
        bar_x, bar_width = 140, self.width - 140 - 30
        # (No bar for reading a neighbour's paper: the blur itself shows it.)
        # Suspicion: yellow during the free staring time, pink after it, and pink
        # once the teacher has seen you copying (then it fills fast). The white
        # line marks where the free staring time ends.
        self.shadow_text("SUSPICION", self.hud_small, WHITE, (16, top + 13))
        suspicion = game.suspicion()
        danger = suspicion >= GRACE_PART or game.seen_copying
        self.bar(bar_x, top + 12, bar_width, 24, suspicion, NEON_PINK if danger else NEON_YELLOW)
        marker_x = bar_x + bar_width * GRACE_PART
        pygame.draw.line(self.screen, WHITE, (marker_x, top + 8), (marker_x, top + 40), 3)

    def zoomed(self, picture, centre, zoom):
        """
        The part of a window-sized picture around `centre`, `zoom` times
        bigger, as a new window-sized picture. Near the edges the cut-out
        part slides inwards so it never goes outside the picture.
        """
        width, height = int(self.width / zoom), int(self.height / zoom)
        part = pygame.Rect(0, 0, width, height)
        part.center = centre
        part.clamp_ip(picture.get_rect())   # keep it inside the picture
        return pygame.transform.smoothscale(picture.subsurface(part), (self.width, self.height))

    def draw_warning_scene(self, game, teacher):
        """
        The warning scene, over the whole screen: the teacher walks up to
        your desk (a zoom into their picture that speeds up), then points at
        you angrily (POINTING_IMAGE, if it exists) and the screen shakes.
        """
        elapsed = WARNING_SCENE_TIME - game.scene_time
        walk = min(1.0, elapsed / TEACHER_APPROACH_TIME)   # 0..1 of the walk
        arrived = elapsed - TEACHER_APPROACH_TIME          # seconds since arriving (< 0 = walking)

        # Shaking, once the teacher is at your desk.
        offset = self.scene_shake(arrived)

        # The walk: zoom into the teacher. walk² starts slow and speeds up.
        watching = self.classroom[f"classroom_{teacher.place.lower()}_watching"]
        zoom = 1 + (APPROACH_ZOOM - 1) * walk * walk
        self.screen.fill(BLACK)
        self.screen.blit(self.zoomed(watching, TEACHER_FACE[teacher.place], zoom), offset)

        if arrived < 0:
            return
        # Arrived: the pointing picture, at once. The white flash below hides
        # the cut from the zoomed picture.
        if POINTING_IMAGE in self.classroom:
            self.screen.blit(self.classroom[POINTING_IMAGE], offset)
        # One line per warning; if MAX_WARNINGS is raised, the last line repeats.
        line = WARNING_LINES[min(game.warnings, len(WARNING_LINES)) - 1]
        self.scene_texts(f"WARNING {game.warnings}/{MAX_WARNINGS}", line, arrived)

    def scene_texts(self, top_text, bottom_text, since_cut):
        """
        The end of a scene, on top of its picture: a pulsing red light, the
        two texts in strips, and a white flash just after the cut.
        since_cut: seconds since the picture changed.
        """
        cx = self.width // 2
        self.darken(int(50 + 40 * math.sin(self.t * 12)), colour=NEON_RED)
        self.screen.blit(self.scanlines, (0, 0))
        self.hud_strip(0, SCENE_STRIP, line_at_top=False)
        self.shout(top_text, self.hud_huge, NEON_RED, (cx, SCENE_STRIP // 2))
        bottom = self.height - SCENE_STRIP
        self.hud_strip(bottom, SCENE_STRIP, line_at_top=True)
        # Shrunk to fit if it is long.
        font = self.hud_big if self.hud_big.size(bottom_text)[0] < self.width - 80 else self.hud
        self.shout(bottom_text, font, NEON_YELLOW, (cx, bottom + SCENE_STRIP // 2), wobble=2)
        # A white flash on top, fading out: a hard cut like in Hotline Miami,
        # so the two pictures are never seen mixed.
        if since_cut < FLASH_TIME:
            self.darken(int(255 * (1 - since_cut / FLASH_TIME)), colour=WHITE)

    def scene_shake(self, since):
        """How far to move the picture this frame: shaking that calms down over SHAKE_TIME."""
        shake = SHAKE_PIXELS * max(0.0, 1 - since / SHAKE_TIME) if since >= 0 else 0
        return int(shake * math.sin(self.t * 55)), int(shake * math.cos(self.t * 47))

    def draw_scene(self, game, teacher):
        """Whichever scene game.scene says is playing."""
        if game.scene == WARNING_SCENE:
            self.draw_warning_scene(game, teacher)
        elif game.scene == CAUGHT_SCENE:
            self.draw_caught_scene(game, teacher)
        elif game.scene == GAME_OVER_SCENE:
            self.draw_game_over(game)

    # ------------------------------------------------------------------
    # The caught scene
    # ------------------------------------------------------------------
    def make_exclaim(self):
        """The red "!" with a thick black outline, like in Metal Gear Solid."""
        font = menu_font(115)
        font.italic = False   # the real one stands straight
        black = font.render("!", True, BLACK)
        red = font.render("!", True, ALERT_RED)
        border = 5
        sheet = pygame.Surface((red.get_width() + 2 * border, red.get_height() + 2 * border),
                               pygame.SRCALPHA)
        # The outline: the black "!" drawn moved in every direction, the red one on top.
        for dx in (-border, 0, border):
            for dy in (-border, 0, border):
                sheet.blit(black, (border + dx, border + dy))
        sheet.blit(red, (border, border))
        return sheet

    def draw_caught_scene(self, game, teacher):
        """
        Caught: the teacher frozen with a red "!" over his head (the Metal
        Gear alert sound plays), then a white flash and he tears up your
        exam (CAUGHT_IMAGE, if it exists).
        """
        elapsed = CAUGHT_SCENE_TIME - game.scene_time
        since_cut = elapsed - CAUGHT_EXCLAIM_TIME
        if since_cut >= 0 and CAUGHT_IMAGE in self.classroom:
            self.screen.fill(BLACK)
            self.screen.blit(self.classroom[CAUGHT_IMAGE], self.scene_shake(since_cut))
        else:
            # The moment you are seen: the teacher, and the "!" popping up big.
            self.screen.blit(self.classroom[f"classroom_{teacher.place.lower()}_watching"], (0, 0))
            face_x, face_y = TEACHER_FACE[teacher.place]
            pop = min(1.0, elapsed / EXCLAIM_POP_TIME)
            self.blit_turned(self.exclaim, (face_x, face_y - EXCLAIM_ABOVE), 0, 1 + 0.5 * (1 - pop))
        if since_cut >= 0:
            self.scene_texts(*CAUGHT_TEXTS, since_cut)

    # ------------------------------------------------------------------
    # The game over screen: two logos with faces
    # ------------------------------------------------------------------
    def make_gemini_logo(self):
        """
        Gemini's four-pointed sparkle in many colours. The shape: a
        "superellipse" |x|^p + |y|^p = r^p with p < 1, whose sides curve
        inwards. The colours go round the middle (GEMINI_COLOURS), and get
        lighter towards it. Made once, as a picture.
        """
        r = LOGO_RADIUS
        size = 2 * r + 8
        mid = size / 2
        exponent = 2 / 0.7   # p = 0.7: how pinched the sides are
        corners = []
        for i in range(160):
            a = 2 * math.pi * i / 160
            c, s_ = math.cos(a), math.sin(a)
            corners.append((mid + r * math.copysign(abs(c) ** exponent, c),
                            mid + r * math.copysign(abs(s_) ** exponent, s_)))
        # The colours: for each pixel, its angle around the middle picks
        # where it is between two of the colours.
        picture = pygame.Surface((size, size), pygame.SRCALPHA)
        count = len(GEMINI_COLOURS)
        for py in range(size):
            for px in range(size):
                dx, dy = px - mid, py - mid
                turn = (math.atan2(dy, dx) / (2 * math.pi)) % 1 * count   # 0..count around
                i = int(turn)
                colour = mix(GEMINI_COLOURS[i], GEMINI_COLOURS[(i + 1) % count], turn - i)
                closeness = max(0.0, 1 - math.hypot(dx, dy) / (r * 0.6))
                picture.set_at((px, py), mix(colour, WHITE, 0.5 * closeness))
        # Keep only the star: multiply by a white star on a see-through sheet.
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), corners)
        picture.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pygame.draw.polygon(picture, OUTLINE, corners, 3)
        return picture

    def make_claude_logo(self):
        """
        Claude's burst: thick rounded rays in warm colours (CLAUDE_COLOURS in
        turn), each with a dark outline, around a round middle that gets
        lighter inwards. Made once, as a picture.
        """
        r = LOGO_RADIUS
        size = int(2 * r * 1.25)
        mid = (size // 2, size // 2)
        picture = pygame.Surface((size, size), pygame.SRCALPHA)
        width = int(r * 0.3)
        ends = []
        for angle, length in CLAUDE_RAYS:
            a = math.radians(angle)
            ends.append((mid[0] + r * length * math.cos(a), mid[1] + r * length * math.sin(a)))
        # First every ray a bit thicker in the outline colour, then the rays
        # on top: that leaves a dark border around the whole burst.
        for end in ends:
            pygame.draw.line(picture, OUTLINE, mid, end, width + 6)
            pygame.draw.circle(picture, OUTLINE, end, width // 2 + 3)
        for i, end in enumerate(ends):
            colour = CLAUDE_COLOURS[i % len(CLAUDE_COLOURS)]
            pygame.draw.line(picture, colour, mid, end, width)
            pygame.draw.circle(picture, colour, end, width // 2)   # round tip
        # The middle: circles from big to small, from the first colour to the last.
        middle = int(r * 0.62)
        pygame.draw.circle(picture, OUTLINE, mid, middle + 3)
        for k in range(middle, 0, -2):
            pygame.draw.circle(picture, mix(CLAUDE_COLOURS[-1], CLAUDE_COLOURS[0], k / middle), mid, k)
        return picture

    def make_glow(self, colour):
        """
        A soft round glow: circles from big to small, each a bit less
        see-through, so it is brightest in the middle and fades out.
        """
        radius = int(LOGO_RADIUS * 1.7)
        glow = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        for k in range(radius, 0, -2):
            # Drawing replaces the pixels, so each smaller circle sets its own,
            # stronger see-through value: (1 - k/radius)² grows towards the middle.
            alpha = int(GLOW_ALPHA * (1 - k / radius) ** 2)
            pygame.draw.circle(glow, (*colour, alpha), (radius, radius), k)
        return glow

    def logo_face(self, centre, mood):
        """
        A cartoon face on a logo. mood: "talk" (mouth opening and closing),
        "laugh" (^ ^ eyes, big open mouth) or "smile". The eyes blink now and then.
        """
        x, y = centre
        r = LOGO_RADIUS
        # Rosy cheeks, under the eyes.
        for cheek_x in (x - r * 0.42, x + r * 0.42):
            cheek = pygame.Rect(0, 0, r * 0.22, r * 0.12)
            cheek.center = (cheek_x, y + r * 0.1)
            pygame.draw.ellipse(self.screen, CHEEKS, cheek)
        eye_y = y - r * 0.15
        for eye_x in (x - r * 0.25, x + r * 0.25):
            if mood == "laugh":
                # ^ shaped, squeezed shut from laughing
                pygame.draw.lines(self.screen, BLACK, False,
                                  [(eye_x - r * 0.12, eye_y + r * 0.05), (eye_x, eye_y - r * 0.08),
                                   (eye_x + r * 0.12, eye_y + r * 0.05)], max(3, r // 12))
            elif self.t % BLINK_EVERY < BLINK_TIME:
                pygame.draw.line(self.screen, BLACK, (eye_x - r * 0.1, eye_y),
                                 (eye_x + r * 0.1, eye_y), max(3, r // 12))
            else:
                eye = pygame.Rect(0, 0, r * 0.26, r * 0.36)
                eye.center = (eye_x, eye_y)
                pygame.draw.ellipse(self.screen, WHITE, eye)
                pygame.draw.ellipse(self.screen, OUTLINE, eye, 2)
                pygame.draw.circle(self.screen, BLACK, (eye_x, eye_y + r * 0.04), r * 0.09)
                # A small white shine, which makes the eyes look alive.
                pygame.draw.circle(self.screen, WHITE, (eye_x - r * 0.03, eye_y), r * 0.035)
        mouth_y = y + r * 0.25
        if mood == "laugh":
            # A wide D-shaped open mouth: half a circle, flat side up.
            half = [(x + r * 0.22 * math.cos(a), mouth_y + r * 0.22 * math.sin(a))
                    for a in [math.pi * i / 12 for i in range(13)]]
            pygame.draw.polygon(self.screen, BLACK, half)
            tongue = pygame.Rect(0, 0, r * 0.22, r * 0.1)
            tongue.center = (x, mouth_y + r * 0.15)
            pygame.draw.ellipse(self.screen, CHEEKS, tongue)
        elif mood == "talk":
            # Opens and closes ten times a second while the line is typed.
            open_mouth = int(self.t * 10) % 2 == 0
            mouth = pygame.Rect(0, 0, r * 0.3, r * (0.24 if open_mouth else 0.07))
            mouth.center = (x, mouth_y)
            pygame.draw.ellipse(self.screen, BLACK, mouth)
        else:
            smile = pygame.Rect(0, 0, r * 0.4, r * 0.3)
            smile.center = (x, mouth_y - r * 0.08)
            pygame.draw.arc(self.screen, BLACK, smile, math.pi * 1.15, math.pi * 1.85, max(3, r // 12))

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

    def chat_line(self, who, message, letters, y, laughing):
        """
        One chat line: the speaker's logo with a face (Gemini left, Claude
        right) and a speech bubble with the first `letters` letters typed.
        laughing: the chat is over and they laugh at you.
        """
        talking = letters < len(message)
        mood = "laugh" if laughing else ("talk" if talking else "smile")
        # The one talking (or laughing) bounces.
        bounce = -abs(math.sin(self.t * 12)) * 8 if talking or laughing else 0
        left = who == GEMINI
        logo_x = CHAT_LOGO_X if left else self.width - CHAT_LOGO_X
        centre = (logo_x, y + bounce)
        # The glow behind, slowly pulsing, then the logo and its face.
        glow = self.glows[who]
        glow.set_alpha(int(180 + 75 * math.sin(self.t * 4)))
        self.screen.blit(glow, glow.get_rect(center=centre))
        self.screen.blit(self.logos[who], self.logos[who].get_rect(center=centre))
        self.logo_face(centre, mood)

        # The bubble is sized for the whole message, so it does not grow
        # while typing; the message is wrapped first, then typed line by line.
        lines = self.wrap(message, self.medium, BUBBLE_MAX_WIDTH)
        line_height = self.medium.get_linesize() + 4
        width = max(self.medium.size(line)[0] for line in lines) + 40
        bubble = pygame.Rect(0, 0, width, len(lines) * line_height + 26)
        if left:
            bubble.midleft = (logo_x + LOGO_RADIUS + 26, y)
        else:
            bubble.midright = (logo_x - LOGO_RADIUS - 26, y)
        colour = GEMINI_BLUE if left else CLAUDE_ORANGE
        pygame.draw.rect(self.screen, mix(BLACK, colour, 0.25), bubble, border_radius=18)
        pygame.draw.rect(self.screen, colour, bubble, 3, border_radius=18)
        # The little tail of the bubble, pointing at the speaker.
        tip_x = bubble.left - 14 if left else bubble.right + 14
        side_x = bubble.left + 1 if left else bubble.right - 1
        pygame.draw.polygon(self.screen, colour, [(side_x, y - 10), (side_x, y + 10), (tip_x, y)])
        left_over = letters
        for i, line in enumerate(lines):
            self.text(line[:max(0, left_over)], self.medium, WHITE,
                      (bubble.x + 20, bubble.y + 13 + i * line_height))
            left_over -= len(line) + 1   # +1: the space between the lines

    def draw_game_over(self, game):
        """
        The game over scene: black, "GAME OVER" in big letters, then the
        Gemini and Claude logos chat about how you lost (GAME_OVER_CHAT).
        When it ends, draw_end() keeps this screen and adds the menu under it.
        """
        self.chat_screen(game, GAME_OVER_TIME - game.scene_time, END_TEXTS[game.lose_reason])
        self.footer("Space = skip")

    def chat_screen(self, game, elapsed, subtitle):
        """
        "GAME OVER", a line of text under it, and the chat as it is `elapsed`
        seconds after it started (long after = all typed, both laughing).
        """
        cx = self.width // 2
        self.screen.fill(BLACK)
        self.shout("GAME OVER", self.menu_title_font, NEON_RED, (cx, 62))
        # Plain (narrower) font, so it stays clear of the logos at the sides.
        self.shadow_text(subtitle, self.medium, WHITE, (cx, 116), center=True)
        chat = GAME_OVER_CHAT[game.lose_reason]
        # The chat is over when the last line has been typed: then both laugh.
        last_start = CHAT_START + (len(chat) - 1) * CHAT_LINE_TIME
        laughing = elapsed >= last_start + len(chat[-1][1]) / CHAT_TYPE_SPEED
        for i, (who, message) in enumerate(chat):
            start = CHAT_START + i * CHAT_LINE_TIME
            if elapsed < start:
                break   # not said yet
            letters = int((elapsed - start) * CHAT_TYPE_SPEED)
            self.chat_line(who, message, letters, CHAT_TOP + i * CHAT_ROW, laughing)
        self.screen.blit(self.scanlines, (0, 0))

    def draw_popup(self, message):
        """A dark band across the screen with the message, drawn on top of the game."""
        band = pygame.Rect(0, self.height // 2 - 105, self.width, 90)
        self.darken(210, band, HUD_PURPLE)
        self.screen.fill(NEON_PINK, (0, band.top, self.width, HUD_LINE))
        self.screen.fill(NEON_PINK, (0, band.bottom - HUD_LINE, self.width, HUD_LINE))
        self.shout(message.upper(), self.hud, NEON_YELLOW, band.center, wobble=2)

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

    def draw_paused(self):
        """Drawn on top of the game screen while no face is seen."""
        self.darken(190, colour=HUD_PURPLE)
        cx, cy = self.width // 2, self.height // 2
        self.shout("FACE NOT FOUND", self.hud_huge, NEON_PINK, (cx, cy - 30))
        self.shadow_text("Game paused - look at the camera to continue", self.medium, WHITE,
                         (cx, cy + 40), center=True)

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
                  camera_surface, lines=None, head_pause=0.0, best=0):
        """
        A whole menu screen in the neon style: main menu, settings, or how to
        play (with `lines`, a list of (text, colour) shown in a dark box).
        select_progress / back_progress (0..1): how long the head has been
        turned right / left, drawn as bars. camera_surface None = no
        webcam preview (the how-to-play text needs the room). head_pause:
        see head_indicator(). best: the best score, shown under the title if
        above 0 (main menu).
        """
        self.menu_background()
        if lines is None:
            # Short menus (the main menu) get a big title; longer ones move up.
            if len(labels) <= 4:
                self.menu_title(title, 120)
                if best > 0:
                    self.shadow_text(f"BEST SCORE  {best}", self.hud, NEON_CYAN,
                                     (self.width // 2, 205), center=True)
                top = 270
            else:
                self.menu_title(title, 75)
                top = 195
        else:
            self.menu_title(title, 60)
            box_top = 110
            self.darken(170, (60, box_top, self.width - 120, len(lines) * 36 + 24))
            for i, (message, colour) in enumerate(lines):
                self.text(message, self.medium, colour, (84, box_top + 14 + i * 36))
            top = box_top + len(lines) * 36 + 75
        self.menu_items(labels, selected, top, select_progress)

        # The webcam, so the player can see the head is being tracked, and
        # above it who is in control (the head or the keys).
        x = self.width - MENU_PREVIEW_SIZE[0] - 16
        y = self.height - MENU_PREVIEW_SIZE[1] - 50
        if camera_surface is not None:
            self.preview(camera_surface, x, y, MENU_PREVIEW_SIZE)
        self.head_indicator(head_pause, x, y - INDICATOR_HEIGHT - 6, MENU_PREVIEW_SIZE[0])
        self.footer(MENU_HINT, back_progress)

    def draw_end(self, game, labels, selected, select_progress, back_progress, head_pause=0.0,
                 best=0, new_best=False):
        """
        Drawn on top of the last game screen when the game is over: the
        result and the score (with how it was made, and the best score), then
        a small neon menu (play again, main menu, quit). After losing, it is
        the game over chat (finished, both logos laughing) with the menu
        under it, so the screen does not change when the chat ends.
        """
        if game.state != WON:
            subtitle = f"{END_TEXTS[game.lose_reason]}    SCORE 0"
            if best > 0:
                subtitle += f"    BEST {best}"
            self.chat_screen(game, GAME_OVER_TIME, subtitle)
            self.menu_items(labels, selected, CHAT_MENU_TOP, select_progress, CHAT_MENU_GAP)
            self.head_indicator(head_pause, self.width - MENU_PREVIEW_SIZE[0] - 16,
                                self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10,
                                MENU_PREVIEW_SIZE[0])
            self.footer(MENU_HINT, back_progress)
            return
        self.darken(200, colour=HUD_PURPLE)
        self.screen.blit(self.scanlines, (0, 0))
        cx = self.width // 2
        if game.state == WON:
            self.shout("EXAM HANDED IN!", self.hud_huge, NEON_GREEN, (cx, 80))
            self.shadow_text(f"{game.correct_count()}/{ANSWERS_NEEDED} CORRECT", self.hud,
                             WHITE, (cx, 135), center=True)
            # Which ones were right (green) and wrong (red).
            self.answer_boxes(game, cx - (ANSWERS_NEEDED * 30 - 8) // 2, 157, graded=True)
            # The score, how it was made, and the best one.
            self.shout(f"SCORE  {game.score()}", self.hud_big, NEON_YELLOW, (cx, 215), wobble=1)
            parts = "    ".join(f"{name} {points:+d}" for name, points in game.score_parts())
            self.shadow_text(parts, self.small, WHITE, (cx, 252), center=True)
            if new_best:
                self.shout("NEW BEST!", self.hud_big, NEON_PINK, (cx, 290), wobble=4)
            else:
                self.shadow_text(f"BEST  {best}", self.hud, NEON_CYAN, (cx, 290), center=True)
        self.menu_items(labels, selected, 355, select_progress)
        self.head_indicator(head_pause, self.width - MENU_PREVIEW_SIZE[0] - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10, MENU_PREVIEW_SIZE[0])
        self.footer(MENU_HINT, back_progress)
