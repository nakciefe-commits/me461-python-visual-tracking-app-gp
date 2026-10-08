"""
Drawing the hallway gossip screen before each exam. Part of Renderer (see
render.py).

In the middle a real arcade slot machine, the "MOOD-O-MATIC", drawn in code:
a cabinet with a domed top and small yellow bulbs all round its edge
(every other one lit, swapping, like a casino sign), its name in neon on
the dome, a glass window with a gold frame in which the exam's
moods (their gossip lines) roll past, decorative buttons, and a lever on
its side. Turning the head right pulls the lever down; then the reel
spins, slows down, goes a little too far and settles on today's mood
(logic/slot.py moves the reel; run.py picked the mood).

Under the reel, built into the machine, a glowing screen (like the pay
table on a real slot machine): once the reel has stopped, the story of
what happened to the teacher lights up on it, and what it means for you
(green "+" lines, red "-" lines). Before that it blinks "PULL THE LEVER".
On the machine's base: "SPIN", then "I'M READY", chosen like any menu item
(turn right and hold).
"""

import math

import pygame

from logic.slot import reel_position, reel_speed, mood_in_middle, has_stopped
from settings import SLOT_SPIN_TIME, SLOT_LEVER_TIME
from ui.draw_menus import INDICATOR_WIDTH, INDICATOR_HEIGHT
from ui.style import (WHITE, BLACK, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED,
                      SHADOW, FOOTER_HEIGHT, mix)

BRIEFING_CHAPTER_Y = 18          # pixels, the middle of "ME461 - CHAPTER 1/3: THE QUIZ"
BRIEFING_TITLE_Y = 52            # pixels, the middle of "HALLWAY GOSSIP"
CABINET = (140, 86, 680, 440)   # x, y, width, height of the slot machine, pixels
DOME = 84                        # pixels, the height of its rounded top
CABINET_TOP, CABINET_BOTTOM = (70, 25, 110), (18, 4, 34)   # its colours, top to bottom
REEL_WINDOW = (180, 184, 600, 80)   # x, y, width, height of the reel's window, pixels
REEL_ROW = 62                    # pixels from one mood to the next on the reel
FRAME = 10                       # pixels, the width of the gold frame around the window
BULB_GAP = 30                    # pixels between the bulbs on the frame
BULB_RADIUS = 4                  # pixels
EDGE_BULB_GAP = 24               # pixels between the bulbs along the machine's edge
EDGE_BULB_SWAP = 0.35            # seconds; the edge bulbs swap (lit, dark, lit... then the other way round)
INFO_SCREEN = (180, 286, 600, 156)  # x, y, width, height of the glowing screen under the reel, pixels
INFO_PAD = 14                    # pixels between that screen's edge and its text
INFO_LINE = 22                   # pixels between its lines
INFO_LIGHT_TIME = 0.5            # seconds the screen takes to light up after the reel stops
BRIEFING_ITEM_Y = 488            # pixels, the middle of "SPIN" / "I'M READY" (on the machine's base)
NORMAL_DAY = "No surprises: a normal exam."   # a mood with no + and no - lines
GOLD_DARK, GOLD, GOLD_LIGHT = (120, 80, 20), (215, 165, 50), (255, 235, 150)
BULB_OFF = (90, 60, 30)
LEVER_LENGTH = 80                # pixels, from the pivot to the ball
LEVER_SWING = 150                # degrees the lever turns when pulled all the way
BLUR_SPEED = 6                   # moods per second; faster than this, the reel blurs
WIN_FLASH_TIME = 1.2             # seconds the bulbs flash after the reel stops
MARQUEE = "MOOD-O-MATIC"


class BriefingDrawing:
    def draw_briefing(self, number, title, pool, chosen, spin_time, labels, selected,
                      select_progress, back_progress, head_pause, chapter=None):
        """
        number: 0 = the first exam of the run. pool: the exam's moods (their
        entries in MOODS), chosen: the index of today's. spin_time: seconds
        since the lever was pulled, None before. labels: ["SPIN"], [] while
        spinning, or ["I'M READY"] once it has stopped; the story lights up
        only then on the machine's screen. select_progress also pulls the lever (the head turning
        right is the hand on the lever). chapter: e.g. "CHAPTER 1/3".
        """
        self.menu_background()
        cx = self.width // 2
        chapter = chapter or f"CHAPTER {number + 1}"
        self.shadow_text(f"ME461  //  {chapter}:  {title}", self.hud_small, NEON_CYAN,
                         (cx, BRIEFING_CHAPTER_Y), center=True)
        self.shout("HALLWAY GOSSIP", self.hud_big, NEON_YELLOW, (cx, BRIEFING_TITLE_Y), wobble=2)

        stopped = spin_time is not None and has_stopped(spin_time)
        flashing = stopped and spin_time - SLOT_SPIN_TIME < WIN_FLASH_TIME
        self.cabinet(spin_time, stopped, flashing)

        window = pygame.Rect(REEL_WINDOW)
        self.reel_frame_gold(window, spin_time, stopped, flashing)
        if spin_time is None:
            self.darken(255, window, (12, 6, 20))
            self.shout("?   ?   ?", self.hud_big, NEON_YELLOW, window.center, wobble=2)
            pull = select_progress   # the head turning right pulls the lever
        else:
            reel = reel_position(chosen, len(pool), spin_time)
            speed = reel_speed(chosen, len(pool), spin_time)
            self.slot_reel(window, pool, reel, speed, stopped)
            pull = max(0.0, 1 - spin_time / SLOT_LEVER_TIME)   # springs back up
        self.glass(window)
        self.slot_lever(pull)

        lit = min(1.0, (spin_time - SLOT_SPIN_TIME) / INFO_LIGHT_TIME) if stopped else 0.0
        self.info_screen(pool[chosen] if stopped else None, lit)

        self.menu_items(labels, selected, BRIEFING_ITEM_Y, select_progress,
                        cx=CABINET[0] + CABINET[2] // 2)
        self.head_indicator(head_pause, self.width - INDICATOR_WIDTH - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10, INDICATOR_WIDTH)
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
    def cabinet_shape(self):
        """
        Made once: the machine's body (a dome on top of a box with rounded
        bottom corners), filled with a purple gradient, and the points of
        its outline (for the neon edge).
        """
        if "cabinet" not in self.neon_cache:
            width, height = CABINET[2], CABINET[3]
            mask = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.ellipse(mask, WHITE, (0, 0, width, 2 * DOME))
            pygame.draw.rect(mask, WHITE, (0, DOME, width, height - DOME), border_bottom_left_radius=28,
                             border_bottom_right_radius=28)
            body = pygame.Surface((width, height), pygame.SRCALPHA)
            for y in range(height):
                body.fill((*mix(CABINET_TOP, CABINET_BOTTOM, y / height), 255), (0, y, width, 1))
            # Keep the gradient only where the shape is (multiplying by the white shape).
            body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            outline = pygame.mask.from_surface(mask).outline(2)
            self.neon_cache["cabinet"] = (body, outline)
        return self.neon_cache["cabinet"]

    def cabinet(self, spin_time, stopped, flashing):
        """The body with a shadow, a neon edge with bulbs on it, and the name on the dome."""
        x, y, width, height = CABINET
        body, outline = self.cabinet_shape()
        shadow = body.copy()
        shadow.fill((0, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MIN)
        self.screen.blit(shadow, (x + 10, y + 12))
        self.screen.blit(body, (x, y))
        points = [(x + px, y + py) for px, py in outline]
        pygame.draw.lines(self.screen, NEON_PINK, True, points, 4)
        self.edge_bulbs(spin_time is not None and not stopped)
        # A chrome band where the dome meets the box.
        pygame.draw.rect(self.screen, GOLD, (x + 6, y + DOME - 6, width - 12, 10), border_radius=4)
        pygame.draw.line(self.screen, GOLD_LIGHT, (x + 10, y + DOME - 5), (x + width - 10, y + DOME - 5), 2)

        cx = x + width / 2
        sign = self.marquee_image()
        self.blit_turned(sign, (cx, y + DOME * 0.62), 0, 0.9 + 0.03 * self.beat() ** 3)

    def edge_bulb_spots(self):
        """
        Made once: spots every EDGE_BULB_GAP pixels along the machine's edge
        (walking along its outline and dropping a bulb each time that far
        has been walked).
        """
        if "edge_bulbs" not in self.neon_cache:
            x, y = CABINET[0], CABINET[1]
            _, outline = self.cabinet_shape()
            spots, walked = [], 0.0
            for (x1, y1), (x2, y2) in zip(outline, outline[1:] + outline[:1]):
                walked += math.hypot(x2 - x1, y2 - y1)
                if walked >= EDGE_BULB_GAP:
                    spots.append((x + x2, y + y2))
                    walked = 0.0
            self.neon_cache["edge_bulbs"] = spots
        return self.neon_cache["edge_bulbs"]

    def edge_bulbs(self, spinning):
        """
        Small yellow bulbs all round the machine's edge, like a casino sign:
        every other one is lit, and every EDGE_BULB_SWAP seconds they swap,
        so the light seems to jump along (three times as fast while spinning).
        """
        swap = int(self.t / (EDGE_BULB_SWAP / 3 if spinning else EDGE_BULB_SWAP)) % 2
        for i, spot in enumerate(self.edge_bulb_spots()):
            if i % 2 == swap:
                pygame.draw.circle(self.screen, mix(NEON_YELLOW, WHITE, 0.5), spot, 6, 1)   # a glow
                pygame.draw.circle(self.screen, NEON_YELLOW, spot, 4)
                pygame.draw.circle(self.screen, WHITE, (spot[0] - 1, spot[1] - 1), 1)   # a shine
            else:
                pygame.draw.circle(self.screen, BULB_OFF, spot, 4)
                pygame.draw.circle(self.screen, GOLD_DARK, spot, 4, 1)

    def marquee_image(self):
        """The machine's name in neon, made once."""
        key = ("marquee", MARQUEE)
        if key not in self.neon_cache:
            self.neon_cache[key] = self.neon_text(MARQUEE, self.hud_big, NEON_PINK, glow=True)
        return self.neon_cache[key]

    def reel_frame_gold(self, window, spin_time, stopped, flashing):
        """The gold frame round the reel's window, with bulbs on it (like the dome's)."""
        outer = window.inflate(2 * FRAME, 2 * FRAME)
        pygame.draw.rect(self.screen, GOLD_DARK, outer.inflate(6, 6), border_radius=18)
        pygame.draw.rect(self.screen, GOLD, outer, border_radius=16)
        pygame.draw.rect(self.screen, GOLD_LIGHT, outer, 2, border_radius=16)
        step = int(self.t * 12)
        for i, spot in enumerate(self.bulb_spots(window.inflate(FRAME, FRAME))):
            if spin_time is None:
                lit = (i + int(self.t * 2)) % 2 == 1
            elif not stopped:
                lit = (i + step) % 4 == 0
            elif flashing:
                lit = int(self.t * 8) % 2 == 1
            else:
                lit = True
            pygame.draw.circle(self.screen, NEON_YELLOW if lit else BULB_OFF, spot, BULB_RADIUS - 1)

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

    def reel_line(self, text, colour):
        """A mood's gossip as it is printed on the reel: up to two lines, made once per colour."""
        key = ("reel", text, colour)
        if key not in self.neon_cache:
            lines = self.wrap(text.upper(), self.hud, REEL_WINDOW[2] - 30)[:2]
            images = [self.hud.render(line, True, colour) for line in lines]
            height = sum(image.get_height() for image in images)
            sheet = pygame.Surface((max(image.get_width() for image in images), height), pygame.SRCALPHA)
            y = 0
            for image in images:
                sheet.blit(image, image.get_rect(midtop=(sheet.get_width() // 2, y)))
                y += image.get_height()
            self.neon_cache[key] = sheet
        return self.neon_cache[key]

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
            line = self.reel_line(pool[index]["gossip"], colour)
            # Further from the middle = turned away on the drum: smaller.
            scale = 1 - 0.25 * min(1.0, abs(distance))
            if blur:
                for ghost in (1, 2):
                    copy = line.copy()
                    copy.set_alpha(70 // ghost)
                    self.blit_turned(copy, (window.centerx, centre_y - ghost * REEL_ROW * 0.3), 0, scale)
            self.blit_turned(line, (window.centerx, centre_y), 0, scale)
        self.screen.set_clip(None)
        self.screen.blit(self.drum_shade(window.size), window.topleft)

    def glass(self, window):
        """A diagonal gleam over the window, so it looks like glass."""
        key = ("glass", window.size)
        if key not in self.neon_cache:
            width, height = window.size
            sheet = pygame.Surface((width, height), pygame.SRCALPHA)
            pygame.draw.polygon(sheet, (255, 255, 255, 38), [(width * 0.12, 0), (width * 0.3, 0),
                                                             (width * 0.18, height), (0, height)])
            pygame.draw.polygon(sheet, (255, 255, 255, 22), [(width * 0.34, 0), (width * 0.4, 0),
                                                             (width * 0.28, height), (width * 0.22, height)])
            self.neon_cache[key] = sheet
        self.screen.blit(self.neon_cache[key], window.topleft)

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

    def slot_lever(self, pull):
        """
        The lever on the machine's right side: a chrome stick with a red ball,
        standing up at rest (pull 0) and swung down when pulled (pull 1).
        """
        x, y, width, _ = CABINET
        pivot = (x + width + 6, REEL_WINDOW[1] + REEL_WINDOW[3] // 2 + 10)
        mount = pygame.Rect(0, 0, 22, 54)
        mount.center = (pivot[0] - 4, pivot[1])
        pygame.draw.rect(self.screen, GOLD_DARK, mount, border_radius=8)
        pygame.draw.rect(self.screen, GOLD, mount, 2, border_radius=8)
        angle = math.radians(LEVER_SWING * min(1.0, pull))   # 0 = straight up
        tip = (pivot[0] + 12 + LEVER_LENGTH * math.sin(angle) * 0.35,
               pivot[1] - LEVER_LENGTH * math.cos(angle))
        pygame.draw.line(self.screen, (120, 120, 135), (pivot[0] + 2, pivot[1] + 2), (tip[0] + 2, tip[1] + 2), 8)
        pygame.draw.line(self.screen, (215, 215, 225), pivot, tip, 7)
        pygame.draw.circle(self.screen, NEON_RED, tip, 15)
        pygame.draw.circle(self.screen, (255, 170, 170), (tip[0] - 5, tip[1] - 5), 5)   # shine

    # ------------------------------------------------------------------
    # The machine's screen
    # ------------------------------------------------------------------
    def info_screen(self, mood, lit):
        """
        The glowing screen under the reel. Before the spin (mood None) it
        blinks "PULL THE LEVER"; after it, today's story and its + and -
        lines light up (lit: 0..1, how far it has lit up).
        """
        screen = pygame.Rect(INFO_SCREEN)
        pygame.draw.rect(self.screen, GOLD_DARK, screen.inflate(10, 10), border_radius=14)
        pygame.draw.rect(self.screen, (8, 4, 16), screen, border_radius=10)
        pygame.draw.rect(self.screen, NEON_CYAN, screen, 2, border_radius=10)
        cx = screen.centerx
        if mood is None:
            if int(self.t * 2) % 2 == 0:
                self.shout("PULL THE LEVER", self.hud_big, NEON_YELLOW, (cx, screen.centery - 14), wobble=2)
            self.shadow_text("What happened to him today?", self.medium, NEON_CYAN,
                             (cx, screen.centery + 34), center=True)
        else:
            self.screen.set_clip(screen)
            # The story as one paragraph: its lines were written for a wider box.
            story = self.wrap(" ".join(mood["story"]), self.small, screen.width - 2 * INFO_PAD)
            effects = [("+  " + text, NEON_GREEN) for text in mood["good"]]
            effects += [("-  " + text, NEON_RED) for text in mood["bad"]]
            if not effects:
                effects = [(NORMAL_DAY, NEON_CYAN)]
            # Everything together, in the middle of the screen.
            y = screen.centery - ((len(story) + len(effects)) * INFO_LINE + 8) // 2
            for line in story:
                self.shadow_text(line, self.small, WHITE, (cx, y + INFO_LINE // 2), center=True)
                y += INFO_LINE
            y += 8
            pygame.draw.line(self.screen, NEON_PINK, (screen.x + 40, y - 4), (screen.right - 40, y - 4), 1)
            for text, colour in effects:
                self.shadow_text(text, self.hud_small, colour, (cx, y + INFO_LINE // 2), center=True)
                y += INFO_LINE
            self.screen.set_clip(None)
            if lit < 1:
                self.darken(int(255 * (1 - lit)), screen, (8, 4, 16))   # the screen warming up
        self.screen.blit(self.scanlines.subsurface(screen), screen.topleft)
        self.glass(screen)
