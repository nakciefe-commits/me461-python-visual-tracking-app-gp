"""
Drawing the guide (the "How to play" screen): Gemini and Claude teach the
game while the player tries it. The picture behind them is what the player
would see in the game: the classroom with the teacher when looking at the
screen, the paper when looking down, a neighbour's paper (blurry, getting
sharper) when looking to the side. A banner says what to do; the chat runs
along the bottom. When the guide is over, main.py goes back to the main menu.
Part of Renderer (see render.py); logic/guide.py says what happens.
"""

import pygame

from logic.guide import GUIDE_PAPERS
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from ui.draw_game import (LOOK_AWAY_IMAGES, SIDE_NAMES, TOP_BAR, OWN_ANSWER_X, OWN_ANSWER_Y,
                          PENCIL)
from ui.style import (NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_PINK, SHADOW, HUD_PURPLE,
                      FOOTER_HEIGHT)

# The classroom picture for what the teacher is doing in a step.
GUIDE_CLASSROOM = {"busy": "classroom_board_busy", "watching": "classroom_board_watching"}
# The banner telling the player what to do, for each task.
TASK_TEXTS = {
    ("look", DOWN): "LOOK DOWN",
    ("look", SCREEN): "LOOK AT THE SCREEN",
    ("read", LEFT): "TURN LEFT AND KEEP LOOKING",
    ("read", RIGHT): "TURN RIGHT AND KEEP LOOKING",
    ("write", None): "LOOK DOWN + PRESS A, B, C, D OR S",
}
TASK_DONE_TEXT = "NICE!"
BANNER_Y = 105                 # pixels, the middle of the task banner
BANNER_BAR = (260, 10)         # pixels, width and height of the task's progress bar
BANNER_MARGIN = 80             # pixels the banner's text keeps free at its sides (else a smaller font)
GUIDE_CHAT_ROWS = (395, 505)   # pixels, the middle of the older and the newer chat line
CHAT_SHADE_TOP = 330           # pixels; the bottom is darkened from here, so the chat is readable
# Looking down or to the side, the papers are in the bottom half: then only
# the newest line is shown, up here under the banner.
GUIDE_CHAT_HIGH_ROW = 220      # pixels, the middle of that line
GUIDE_HINT = "Space = next   Esc = back to the menu"


class GuideDrawing:
    def draw_guide(self, guide, direction):
        """One frame of the guide (not finished). direction: where the player looks."""
        self.guide_view(guide, direction)

        # The chat: the last two lines said, newest at the bottom; or only the
        # newest, higher up, so it does not cover the papers.
        papers = direction != SCREEN
        if papers:
            said, rows = guide.said[-1:], (GUIDE_CHAT_HIGH_ROW,)
        else:
            self.darken(150, (0, CHAT_SHADE_TOP, self.width, self.height - CHAT_SHADE_TOP))
            said = guide.said[-2:]
            rows = GUIDE_CHAT_ROWS[-len(said):]
        for i, ((who, text), y) in enumerate(zip(said, rows)):
            newest = i == len(said) - 1
            letters = guide.letters() if newest else len(text)
            self.chat_line(who, text, letters, y, laughing=False)

        # The top strip: the title and how far along the guide is.
        self.hud_strip(0, TOP_BAR, line_at_top=False)
        title = self.shadow_text("HOW TO PLAY", self.hud_big, NEON_YELLOW, (16, 8))
        self.shadow_text(f"STEP {guide.step + 1} / {len(guide.steps)}", self.hud_small, NEON_CYAN,
                         (title.right + 24, 20))

        self.task_banner(guide)
        self.footer(GUIDE_HINT)
        self.screen.blit(self.scanlines, (0, 0))

    def guide_view(self, guide, direction):
        """What the player sees where they look, like in the game."""
        if direction == DOWN:
            self.screen.blit(self.classroom[LOOK_AWAY_IMAGES[DOWN]], (0, 0))
            for i, letter in enumerate(guide.written):
                self.text(letter, self.big, PENCIL, (OWN_ANSWER_X, OWN_ANSWER_Y[i]), center=True)
        elif direction in (LEFT, RIGHT):
            shown = GUIDE_PAPERS[direction]
            name = f"{SIDE_NAMES[direction]}_{shown}"
            clarity = guide.clarity(direction)
            if name in self.classroom:
                self.screen.blit(self.blurred(self.classroom[name], clarity), (0, 0))
            else:
                # No picture with that letter: the plain one, and a note once read.
                self.screen.blit(self.blurred(self.classroom[LOOK_AWAY_IMAGES[direction]], clarity),
                                 (0, 0))
                if clarity >= 1:
                    self.neighbour_note(direction, "?" if shown == "unknown" else shown)
        else:
            self.screen.blit(self.classroom[GUIDE_CLASSROOM[guide.teacher()]], (0, 0))

    def task_banner(self, guide):
        """What to do now, with a bar for how far it is; "NICE!" once it is done."""
        x = self.width // 2
        task = guide.task()
        if task is None or not guide.last_line() or not guide.typed():
            return
        if guide.task_done:
            self.shout(TASK_DONE_TEXT, self.hud_huge, NEON_GREEN, (x, BANNER_Y))
            return
        kind, what = task
        text = TASK_TEXTS.get(task, f"LOOK DOWN + PRESS {what}")
        # A long text gets the smaller font, so it keeps clear of the edges.
        font = self.hud_big if self.hud_big.size(text)[0] <= 2 * x - BANNER_MARGIN else self.hud
        band = pygame.Rect(0, 0, font.size(text)[0] + 60, 80)
        band.center = (x, BANNER_Y + 8)
        self.darken(170, band, HUD_PURPLE)
        pygame.draw.rect(self.screen, NEON_PINK, band, 2)
        self.shout(text, font, NEON_YELLOW, (x, BANNER_Y), wobble=2)
        if kind in ("look", "read"):
            bar = pygame.Rect(0, 0, *BANNER_BAR)
            bar.midtop = (x, BANNER_Y + 26)
            pygame.draw.rect(self.screen, SHADOW, bar)
            bar.width = int(bar.width * guide.progress())
            pygame.draw.rect(self.screen, NEON_CYAN, bar)
