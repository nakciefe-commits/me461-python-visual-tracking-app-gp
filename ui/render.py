"""
Drawing: everything the player sees.

The drawing code is split over a few files, one per kind of screen:
    style.py        colours, fonts, small helpers (text, bars, neon text)
    draw_notice.py  the opening notice on the desk
    draw_menus.py   start, loading, camera wait, menus
    draw_briefing.py the hallway gossip before each exam (with the slot machine)
    draw_game.py    the classroom, your paper, the neighbours, the strips
    draw_scenes.py  warning, caught and game over scenes
    draw_guide.py   how to play: Gemini and Claude teach the game
    draw_results.py the score count after an exam, the run's results, top scores

Each of those files has one class with some of the drawing methods, and
Renderer below inherits from all of them ("mixins"). So there is still one
`renderer` object, and every method can call every other one with `self.`,
whichever file it is in. This file only loads what all of them need once:
fonts, pictures and a few see-through layers.

Each draw_... method paints one whole screen onto the pygame window. They
only read the game's state; they never change it. `self.t` (seconds since
the program started, set by main.py every frame) makes things move.
"""

import os

import cv2
import pygame

from ui.draw_briefing import BriefingDrawing
from ui.draw_guide import GuideDrawing
from ui.draw_game import GameDrawing, LOOK_AWAY_IMAGES, PAPER_IMAGES
from ui.draw_menus import MenuDrawing, BUTTON_TEXT, BUTTON_HEIGHT, BUTTON_PADDING
from ui.draw_notice import NoticeDrawing
from ui.draw_results import ResultsDrawing
from ui.draw_scenes import SceneDrawing, SCENE_PICTURE_TOP, GEMINI, CLAUDE, LOGO_GLOW
from settings import CLASSROOM_TOP, MOODS
from ui.style import NeonStyle, PREVIEW_SIZE, SCANLINE_GAP, SCANLINE_ALPHA, menu_font, mono_font

IMAGE_FOLDER = os.path.join("assets", "images")
IMAGE_TYPES = (".jpeg", ".jpg", ".png")   # a picture may be saved as any of these
CLASSROOM_IMAGES = ["classroom_board_busy", "classroom_board_watching",
                    "classroom_desk_busy", "classroom_desk_watching"]


def camera_to_surface(frame, size=PREVIEW_SIZE):
    """Turn an OpenCV webcam frame into a smaller, mirrored pygame image."""
    small = cv2.resize(cv2.flip(frame, 1), size)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)   # OpenCV is BGR, pygame wants RGB
    return pygame.image.frombuffer(rgb.tobytes(), size, "RGB")


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


class Renderer(NeonStyle, NoticeDrawing, MenuDrawing, BriefingDrawing, GameDrawing, SceneDrawing,
               ResultsDrawing, GuideDrawing):
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.t = 0.0   # seconds since the program started; main.py sets it every frame
        self.mood = None   # today's teacher mood; main.py sets it before each exam (see picture())
        self.load_fonts()
        self.load_pictures()

        # Made once, because making them is slow.
        self.exclaim = self.make_exclaim()   # the Metal Gear "!"
        self.desk = self.make_desk()         # the wooden desk behind the notice
        self.stamp = self.make_stamp()
        self.logos = {GEMINI: self.make_gemini_logo(), CLAUDE: self.make_claude_logo()}
        self.glows = {who: self.make_glow(colour) for who, colour in LOGO_GLOW.items()}
        self.scanlines = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, SCANLINE_GAP):
            pygame.draw.line(self.scanlines, (0, 0, 0, SCANLINE_ALPHA), (0, y), (self.width, y))
        self.make_menu_layers()
        self.neon_cache = {}   # (text, colour) -> neon picture, so titles are made once

        # Where each menu item was drawn last frame; main.py checks mouse clicks on them.
        self.menu_rects = []
        # The "Calibrate" button on the start screen; main.py checks clicks on it.
        # Sized from its text, so the text never touches the slanted edges
        # whatever font this computer has.
        text_width = self.hud.size(BUTTON_TEXT)[0]
        self.button_rect = pygame.Rect(0, 0, text_width + 2 * BUTTON_PADDING, BUTTON_HEIGHT)
        self.button_rect.center = (self.width // 2, 500)

    def load_fonts(self):
        # None = pygame's built-in font.
        self.giant = pygame.font.SysFont(None, 96)
        self.huge = pygame.font.SysFont(None, 72)
        self.big = pygame.font.SysFont(None, 52)
        self.medium = pygame.font.SysFont(None, 34)
        self.small = pygame.font.SysFont(None, 24)
        # Slanted bold fonts for the neon style (see style.menu_font()).
        self.menu_title_font = menu_font(84)
        self.menu_item_font = menu_font(48)
        self.hud_huge = menu_font(60)
        self.hud_big = menu_font(38)
        self.hud = menu_font(26)
        self.hud_small = menu_font(18)
        # Typewriter fonts for the notice.
        self.type_font = mono_font(19)
        self.type_title_font = mono_font(34)

    def load_pictures(self):
        """Loaded once at the start, not every frame: loading and scaling are slow."""
        self.classroom = {name: load_classroom(name, self.width, self.height)
                          for name in CLASSROOM_IMAGES + list(LOOK_AWAY_IMAGES.values())}
        # The paper pictures are optional: a missing one falls back to a note.
        for name in PAPER_IMAGES:
            if image_file(name):
                self.classroom[name] = load_classroom(name, self.width, self.height)
        # So are the scene pictures (see draw_scenes.py).
        for name, top in SCENE_PICTURE_TOP.items():
            if image_file(name):
                self.classroom[name] = load_classroom(name, self.width, self.height, top)
        # Optional pictures for a mood: "classroom_board_busy_birthday" is
        # shown instead of "classroom_board_busy" on his birthday (see picture()).
        for name in list(self.classroom):
            top = SCENE_PICTURE_TOP.get(name, CLASSROOM_TOP)
            for mood in MOODS:
                if image_file(f"{name}_{mood}"):
                    self.classroom[f"{name}_{mood}"] = load_classroom(f"{name}_{mood}", self.width,
                                                                      self.height, top)

    def picture(self, name):
        """Picture `name`, or today's mood's own version of it if there is one (e.g. "_birthday")."""
        return self.classroom.get(f"{name}_{self.mood}", self.classroom[name])
