"""
Drawing the hallway gossip screen before each exam. Part of Renderer (see
render.py).

First a slot machine, the "MOOD-O-MATIC": a gold cabinet with blinking
bulbs, a reel window in which the exam's moods (their gossip lines) roll
past, and a lever. Turning the head right pulls the lever down; when it is
pulled, the reel spins, slows down, goes a little too far and settles on
today's mood (logic/slot.py moves the reel; run.py picked the mood). Then
the story of what happened to the teacher, and what it means: green "+"
lines and red "-" lines. Under the box: "SPIN", then "I'M READY", chosen
like any menu item (turn right and hold).
"""

import math

import pygame

from logic.slot import reel_position, reel_speed, mood_in_middle, has_stopped
from settings import QUIZZES, SLOT_SPIN_TIME, SLOT_LEVER_TIME
from ui.draw_menus import MENU_PREVIEW_SIZE, INDICATOR_HEIGHT
from ui.style import (WHITE, BLACK, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN,
                      NEON_RED, FOOTER_HEIGHT, mix)

BRIEFING_CHAPTER_Y = 30          # pixels, the middle of "ME461 - CHAPTER 1/3: THE QUIZ"
BRIEFING_TITLE_Y = 86            # pixels, the middle of "HALLWAY GOSSIP"
BRIEFING_PANEL = (50, 132, 860, 300)   # x, y, width, height of the box, pixels
REEL_WINDOW = (110, 158, 700, 80)      # x, y, width, height of the reel's window, pixels
REEL_ROW = 58                    # pixels from one mood to the next on the reel
FRAME = 12                       # pixels, the width of the gold frame around the window
BULB_GAP = 34                    # pixels between the bulbs on the frame
BULB_RADIUS = 4                  # pixels
STORY_TOP = 142                  # pixels from the box's top to the first story line
LINE_GAP = 28                    # pixels between the lines of the story and of the +/- list
EFFECTS_TOP = 234                # pixels from the box's top to the first +/- line
BRIEFING_ITEM_Y = 476            # pixels, the middle of "SPIN" / "I'M READY"
NORMAL_DAY = "No surprises: a normal exam."   # a mood with no + and no - lines
GOLD_DARK, GOLD, GOLD_LIGHT = (120, 80, 20), (215, 165, 50), (255, 235, 150)
BULB_OFF = (90, 60, 30)
LEVER_LENGTH = 74                # pixels, from the pivot to the ball
LEVER_SWING = 150                # degrees the lever turns when pulled all the way
BLUR_SPEED = 6                   # moods per second; faster than this, the reel blurs
WIN_FLASH_TIME = 1.2             # seconds the bulbs flash after the reel stops
MARQUEE = "MOOD-O-MATIC"


class BriefingDrawing:
    def draw_briefing(self, number, title, pool, chosen, spin_time, labels, selected,
                      select_progress, back_progress, head_pause):
        """
        number: 0 = the first exam of the run. pool: the exam's moods (their
        entries in MOODS), chosen: the index of today's. spin_time: seconds
        since the lever was pulled, None before. labels: ["SPIN"], [] while
        spinning, or ["I'M READY"] once it has stopped; the story is shown
        only then. select_progress also pulls the lever (the head turning
        right is the hand on the lever).
        """
        self.menu_background()
        cx = self.width // 2
        self.shadow_text(f"ME461 - CHAPTER {number + 1}/{len(QUIZZES)}:  {title}", self.hud,
                         NEON_CYAN, (cx, BRIEFING_CHAPTER_Y), center=True)
        self.menu_title("HALLWAY GOSSIP", BRIEFING_TITLE_Y)
        self.panel(BRIEFING_PANEL)

        window = pygame.Rect(REEL_WINDOW)
        stopped = spin_time is not None and has_stopped(spin_time)
        self.slot_cabinet(window, spin_time, stopped)
        if spin_time is None:
            self.darken(235, window, BLACK)
            self.shout("?   ?   ?", self.hud_big, NEON_YELLOW, window.center, wobble=2)
            self.shadow_text("What happened to him today? Pull the lever to find out.",
                             self.medium, WHITE, (cx, BRIEFING_PANEL[1] + STORY_TOP + 20),
                             center=True)
            pull = select_progress   # the head turning right pulls the lever
        else:
            reel = reel_position(chosen, len(pool), spin_time)
            speed = reel_speed(chosen, len(pool), spin_time)
            self.slot_reel(window, pool, reel, speed, stopped)
            pull = max(0.0, 1 - spin_time / SLOT_LEVER_TIME)   # springs back up
        self.slot_lever(window, pull)
        if stopped:
            self.mood_story(pool[chosen], BRIEFING_PANEL[1])

        self.menu_items(labels, selected, BRIEFING_ITEM_Y, select_progress)
        self.head_indicator(head_pause, self.width - MENU_PREVIEW_SIZE[0] - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10,
                            MENU_PREVIEW_SIZE[0])
        if stopped:
            hint = "Ready? Turn your head RIGHT and hold (or Enter)    LEFT = back to the menu"
        elif spin_time is None:
            hint = "Turn your head RIGHT and hold to pull the lever (or Enter)    LEFT = back"
        else:
            hint = "Spinning..."
        self.footer(hint, back_progress)

    # ------------------------------------------------------------------
    # The machine
    # ------------------------------------------------------------------
    def slot_cabinet(self, window, spin_time, stopped):
        """
        The gold frame around the window, with bulbs on it and the
        machine's name on top. The bulbs blink slowly while waiting, chase
        round while spinning, and all flash together when it stops.
        """
        outer = window.inflate(2 * FRAME, 2 * FRAME)
        # Gold: a dark edge, the gold, a light line on top (looks like metal).
        pygame.draw.rect(self.screen, GOLD_DARK, outer.inflate(6, 6), border_radius=16)
        pygame.draw.rect(self.screen, GOLD, outer, border_radius=14)
        pygame.draw.rect(self.screen, GOLD_LIGHT, outer, 2, border_radius=14)
        pygame.draw.rect(self.screen, GOLD_DARK, window.inflate(4, 4), border_radius=6)

        # The bulbs: along the frame, in order round it (top, right, bottom, left).
        bulbs = self.bulb_spots(window.inflate(FRAME, FRAME))
        step = int(self.t * 12)          # moves the chase on 12 times a second
        for i, spot in enumerate(bulbs):
            if spin_time is None:
                lit = (i + int(self.t * 2)) % 2 == 0                   # slow blinking
            elif not stopped:
                lit = (i + step) % 4 == 0                              # chasing round
            elif spin_time - SLOT_SPIN_TIME < WIN_FLASH_TIME:
                lit = int(self.t * 8) % 2 == 0                         # all flash: a win!
            else:
                lit = True
            colour = NEON_YELLOW if lit else BULB_OFF
            if lit:
                pygame.draw.circle(self.screen, mix(NEON_YELLOW, WHITE, 0.6), spot, BULB_RADIUS + 3, 1)
            pygame.draw.circle(self.screen, colour, spot, BULB_RADIUS)

        # The name, on a small sign on the top edge.
        sign = self.hud_small.render(MARQUEE, True, NEON_PINK)
        plate = sign.get_rect(center=(outer.centerx, outer.top)).inflate(24, 6)
        pygame.draw.rect(self.screen, BLACK, plate, border_radius=8)
        pygame.draw.rect(self.screen, NEON_PINK, plate, 2, border_radius=8)
        self.screen.blit(sign, sign.get_rect(center=plate.center))

    def bulb_spots(self, rect):
        """Points every BULB_GAP pixels round a rectangle, in order (clockwise)."""
        spots = []
        corners = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
        for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
            length = math.hypot(x2 - x1, y2 - y1)
            for k in range(int(length // BULB_GAP)):
                f = k * BULB_GAP / length
                spots.append((int(x1 + (x2 - x1) * f), int(y1 + (y2 - y1) * f)))
        return spots

    def slot_reel(self, window, pool, reel, speed, stopped):
        """
        The moods rolling past in the window, like on a drum: the one in the
        middle big and bright, the ones above and below smaller and darker,
        and dark shading at the top and bottom edges. Spinning fast, each
        line also leaves see-through copies above it (motion blur).
        """
        self.darken(255, window, (245, 240, 225))   # the reel's paper-white drum
        count = len(pool)
        first = math.floor(reel)
        offset = reel - first   # 0..1, how far the reel has moved past `first`
        blur = speed > BLUR_SPEED
        self.screen.set_clip(window)   # draw only inside the window
        for k in (-1, 0, 1, 2):
            index = (first + k) % count
            distance = k - offset                # in rows from the middle
            centre_y = window.centery + distance * REEL_ROW
            middle = index == mood_in_middle(reel, count) and abs(distance) < 0.5
            colour = NEON_RED if middle and stopped else (40, 30, 60)
            line = self.hud_big.render(pool[index]["gossip"].upper(), True, colour)
            # Further from the middle = turned away on the drum: smaller.
            fit = min(1.0, (window.width - 40) / line.get_width())
            scale = fit * (1 - 0.25 * min(1.0, abs(distance)))
            if blur:
                for ghost in (1, 2):
                    copy = line.copy()
                    copy.set_alpha(70 // ghost)
                    self.blit_turned(copy, (window.centerx, centre_y - ghost * REEL_ROW * 0.3), 0, scale)
            self.blit_turned(line, (window.centerx, centre_y), 0, scale)
        self.screen.set_clip(None)
        self.screen.blit(self.drum_shade(window.size), window.topleft)

    def drum_shade(self, size):
        """
        Made once: a see-through layer that is dark at the top and bottom and
        clear in the middle, so the flat window looks like a turning drum.
        """
        key = ("drum", size)
        if key not in self.neon_cache:
            width, height = size
            shade = pygame.Surface(size, pygame.SRCALPHA)
            for y in range(height):
                edge = abs(y - height / 2) / (height / 2)   # 0 middle, 1 edge
                shade.fill((20, 10, 30, int(220 * edge ** 2)), (0, y, width, 1))
            self.neon_cache[key] = shade
        return self.neon_cache[key]

    def slot_lever(self, window, pull):
        """
        The lever on the right of the machine: a stick with a red ball,
        standing up at rest (pull 0) and swung down when pulled (pull 1).
        """
        pivot = (window.right + FRAME + 30, window.centery + 12)
        pygame.draw.rect(self.screen, GOLD_DARK, (pivot[0] - 10, pivot[1] - 22, 20, 44), border_radius=6)
        pygame.draw.rect(self.screen, GOLD, (pivot[0] - 10, pivot[1] - 22, 20, 44), 2, border_radius=6)
        angle = math.radians(LEVER_SWING * min(1.0, pull))   # 0 = straight up
        tip = (pivot[0] + LEVER_LENGTH * math.sin(angle) * 0.35,
               pivot[1] - LEVER_LENGTH * math.cos(angle))
        pygame.draw.line(self.screen, (200, 200, 210), pivot, tip, 7)
        pygame.draw.circle(self.screen, NEON_RED, tip, 14)
        pygame.draw.circle(self.screen, (255, 170, 170), (tip[0] - 4, tip[1] - 4), 5)   # shine

    def mood_story(self, mood, top):
        """The story of today's mood, then its + lines (green) and - lines (red)."""
        cx = self.width // 2
        for i, line in enumerate(mood["story"]):
            self.shadow_text(line, self.medium, WHITE, (cx, top + STORY_TOP + i * LINE_GAP),
                             center=True)
        effects = [("+  " + text, NEON_GREEN) for text in mood["good"]]
        effects += [("-  " + text, NEON_RED) for text in mood["bad"]]
        if not effects:
            effects = [(NORMAL_DAY, NEON_CYAN)]
        for i, (text, colour) in enumerate(effects):
            self.shadow_text(text, self.hud, colour, (cx, top + EFFECTS_TOP + i * LINE_GAP),
                             center=True)
