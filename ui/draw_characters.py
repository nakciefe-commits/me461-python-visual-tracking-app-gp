"""
Drawing the character screen ("WHO ARE YOU?") before a run. Part of
Renderer (see render.py).

Like choosing a mask in Hotline Miami: the characters stand in a row that
slides sideways. The chosen one is in the middle, big, in a glowing frame,
thumping on every beat of the character music; the others get smaller and
darker the further they are, and the row slides smoothly when the choice
changes (main.py moves `slide` towards the chosen one). The head works
sideways here: turn left / right to move, look down to choose, up to go back. When the screen
opens (on the music's drop) the row slides in from the right with a white
flash. Under it: the name, a one-line story, and what he gets (+, green)
and what it costs (-, red). The portraits are drawn in code: a head and
shoulders, with what makes him him (a cap, glasses, a can, an apple for the
teacher, a grey beard, a wrench held the wrong way, a hand in the air...).
The numbers behind it are in CHARACTERS in settings.py;
logic/character.py uses them.
"""

import math

import pygame

from logic.run_intro import since_beat, since_bar
from settings import CHARACTERS
from ui.draw_menus import INDICATOR_WIDTH, INDICATOR_HEIGHT
from ui.style import (WHITE, BLACK, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED,
                      SHADOW, HUD_PURPLE, FOOTER_HEIGHT, mix)

CHARACTER_TITLE_Y = 46             # pixels, the middle of "WHO ARE YOU?"
PORTRAIT = 170                     # pixels, the size a portrait is drawn at (then scaled)
CAROUSEL_Y = 215                   # pixels, the middle of the row of portraits
CAROUSEL_GAP = 230                 # pixels from the middle one to its neighbours
CAROUSEL_FAR_GAP = 150             # pixels further for each one after that
CHOSEN_SCALE = 1.1                 # the chosen portrait is drawn this much bigger
SIDE_SCALE = 0.62                  # its neighbours this big ...
FAR_SCALE = 0.15                   # ... and each one further this much smaller again
SIDE_DARKEN = 160                  # 0-255, how much darker the neighbours are
BEAT_THUMP = 0.07                  # how much bigger the chosen one is right on a beat
ENTER_TIME = 0.45                  # seconds the row takes to slide in when the screen opens
NAME_Y = 360                       # pixels, the middle of the chosen one's name
TAGLINE_Y = 392                    # pixels, the top of the story line
LINES_TOP = 450                    # pixels, the top of the first + / - line
LINES_LEFT = 80                    # pixels, where the + / - lines start
LINES_WIDTH = 640                  # pixels they may be wide (they stay clear of the HEAD CONTROL box)
CARD_LINE = 24                     # pixels between the + and - lines
CARD_SIGN = 22                     # pixels from the + / - to its text
CHARACTER_HINT = ("HEAD: turn left/right = previous / next   look DOWN = play as him   look UP = back"
                  "     KEYS: arrows, Enter, Esc")
SKIN = (60, 20, 80)                # the dark purple of the heads (they are drawn in neon lines)
GREY_BAG = (110, 115, 125)         # the edge of the laptop bag
CAP_NAVY = (20, 25, 70)            # the New Era cap
GOLD_STICKER = (230, 190, 60)      # the sticker on its brim
MUG_BROWN = (120, 70, 40)          # the 7th-year legend's old coffee mug
GREY_HAIR = (200, 200, 210)        # ... and his grey hair and beard
WRENCH_STEEL = (170, 180, 195)     # the not-ME student's wrench
SWEAT = (150, 210, 255)            # ... and the drop of sweat on his forehead
QUIFF = (25, 8, 35)                # the funny guy's big quiff (almost black)
JACKET = (20, 20, 30)              # ... and his leather jacket's popped collar


class CharacterDrawing:
    def draw_characters(self, keys, selected, slide, t, since_enter, select_progress,
                        back_progress, head_pause):
        """
        The whole character screen. keys: the characters in order (keys of
        CHARACTERS); selected: the index of the chosen one; slide: where the
        row is (a float index, moving towards `selected`); t: seconds into
        the character music (for the beats); since_enter: seconds since the
        screen opened. Remembers where each portrait is (self.menu_rects),
        for the mouse.
        """
        self.menu_background()
        self.menu_title("WHO ARE YOU?", CHARACTER_TITLE_Y)
        self.carousel(keys, selected, slide, t, since_enter, select_progress)
        self.character_info(keys[selected])
        self.head_indicator(head_pause, self.width - INDICATOR_WIDTH - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10, INDICATOR_WIDTH)
        self.footer(CHARACTER_HINT, back_progress)
        # The drop: the screen opens with a white flash.
        flash = max(0.0, 1 - since_enter / ENTER_TIME)
        if flash > 0:
            self.darken(int(230 * flash ** 2), colour=WHITE)

    def carousel(self, keys, selected, slide, t, since_enter, select_progress):
        """The row of portraits, the far ones first so the near ones cover them."""
        count = len(keys)
        cx = self.width // 2
        # Opening: the whole row slides in from the right, slowing down.
        enter = min(1.0, since_enter / ENTER_TIME)
        cx += int(self.width * (1 - enter) ** 3)
        thump = BEAT_THUMP * max(0.0, 1 - since_beat(t) / 0.18)
        placed = []
        for i, key in enumerate(keys):
            # How far from the middle, in places: -1 = just left, +2 = two right.
            # The row goes round, so the shorter way is taken.
            d = (i - slide + count / 2) % count - count / 2
            near, far = min(abs(d), 1.0), max(0.0, abs(d) - 1)
            x = cx + math.copysign(near * CAROUSEL_GAP + far * CAROUSEL_FAR_GAP, d)
            scale = CHOSEN_SCALE - (CHOSEN_SCALE - SIDE_SCALE) * near - FAR_SCALE * far
            placed.append((abs(d), i, key, x, max(0.2, scale)))
        self.menu_rects = [pygame.Rect(0, 0, 0, 0)] * count
        for distance, i, key, x, scale in sorted(placed, reverse=True):
            if distance > 2.6:
                continue   # off to the sides
            chosen = i == selected and distance < 0.5
            size = int(PORTRAIT * (scale + (thump if chosen else 0)))
            image = pygame.transform.smoothscale(self.portrait_image(key), (size, size))
            rect = image.get_rect(center=(int(x), CAROUSEL_Y))
            if chosen:
                self.chosen_glow(rect, t)
            self.screen.blit(image, rect)
            if not chosen:
                self.darken(int(SIDE_DARKEN * min(1.0, distance)), rect, HUD_PURPLE)
            pygame.draw.rect(self.screen, NEON_YELLOW if chosen else NEON_CYAN, rect, 4 if chosen else 2)
            self.menu_rects[i] = rect
            if chosen and select_progress > 0:
                bar = pygame.Rect(rect.x, rect.bottom + 8, int(rect.width * select_progress), 7)
                pygame.draw.rect(self.screen, NEON_CYAN, bar)

    def chosen_glow(self, rect, t):
        """A neon halo behind the chosen portrait, flaring on every bar's strong hit."""
        flare = max(0.0, 1 - since_bar(t) / 0.5)
        colour = mix(NEON_PINK, NEON_YELLOW, flare)
        for k in range(4, 0, -1):
            halo = rect.inflate(k * 10 + int(20 * flare), k * 10 + int(20 * flare))
            self.darken(30 + int(25 * flare), halo, colour)

    def portrait_image(self, key):
        """
        The portrait as a picture of its own (PORTRAIT x PORTRAIT), so it can
        be scaled for the row. Made each frame: the portraits move (bobbing,
        laughter, glowing laptops).
        """
        image = pygame.Surface((PORTRAIT, PORTRAIT))
        screen, self.screen = self.screen, image   # the portrait code draws on self.screen
        try:
            self.portrait(key, image.get_rect())
        finally:
            self.screen = screen
        return image

    def character_info(self, key):
        """The chosen one's name (big), his story, and the + and - lines under the row."""
        entry = CHARACTERS[key]
        cx = self.width // 2
        self.shout(entry["name"], self.hud_huge if self.hud_huge.size(entry["name"])[0] < 860 else self.hud_big,
                   NEON_YELLOW, (cx, NAME_Y), wobble=2, pulse=0.03)
        y = TAGLINE_Y
        for line in self.wrap(entry["tagline"], self.medium, 860)[:2]:
            self.shadow_text(line, self.medium, WHITE, (cx, y + self.medium.get_height() // 2), center=True)
            y += self.medium.get_height()
        y = max(LINES_TOP, y + 10)
        for lines, sign, colour in ((entry["plus"], "+", NEON_GREEN), (entry["minus"], "-", NEON_RED)):
            for line in lines:
                self.shadow_text(sign, self.hud_small, colour, (LINES_LEFT, y))
                for part in self.wrap(line, self.hud_small, LINES_WIDTH - CARD_SIGN):
                    self.shadow_text(part, self.hud_small, colour, (LINES_LEFT + CARD_SIGN, y))
                    y += CARD_LINE

    # ------------------------------------------------------------------
    # The portraits, drawn in code
    # ------------------------------------------------------------------
    def portrait(self, key, frame):
        """
        A neon head and shoulders in `frame`, bobbing a little, with the
        character's things on him. Every portrait is the same face; what he
        wears tells them apart.
        """
        self.screen.set_clip(frame)
        cx = frame.centerx
        bob = 3 * math.sin(self.t * 2.5)
        head = (cx, int(frame.y + frame.height * 0.42 + bob))
        radius = frame.width // 4
        # Shoulders: a big rounded shape coming up from the bottom.
        shoulders = pygame.Rect(0, 0, int(frame.width * 0.85), frame.height // 2)
        shoulders.midtop = (cx, int(head[1] + radius * 0.9))
        pygame.draw.ellipse(self.screen, SKIN, shoulders)
        pygame.draw.ellipse(self.screen, NEON_PINK, shoulders, 3)
        pygame.draw.circle(self.screen, SKIN, head, radius)
        pygame.draw.circle(self.screen, NEON_CYAN, head, radius, 3)
        drawer = getattr(self, f"portrait_{key}", None)
        if key != "lazy":   # the funny guy draws his own face (shades and a smirk)
            self.face(head, radius, sleepy=key in ("energy", "veteran"))
        if drawer is not None:
            drawer(head, radius, shoulders)
        self.screen.set_clip(None)

    def face(self, head, radius, sleepy=False):
        """Eyes (half shut when sleepy) and a smiling mouth."""
        hx, hy = head
        for side in (-1, 1):
            eye = (hx + side * radius // 2.6, hy - radius // 6)
            if sleepy:
                pygame.draw.line(self.screen, WHITE, (eye[0] - 7, eye[1]), (eye[0] + 7, eye[1]), 3)
            else:
                pygame.draw.circle(self.screen, WHITE, eye, 5)
        mouth = pygame.Rect(0, 0, radius, radius // 3)
        mouth.center = (hx, hy + radius // 2.4)
        pygame.draw.arc(self.screen, WHITE, mouth, math.pi, 2 * math.pi, 3)

    def portrait_npc(self, head, radius, shoulders):
        """A laptop bag on a strap, with a gaming laptop peeking out (RGB glow and "MONSTER" on it)."""
        bag = pygame.Rect(0, 0, int(radius * 2.0), int(radius * 1.1))
        bag.center = (shoulders.centerx + int(radius * 0.9), shoulders.y + int(radius * 1.0))
        pygame.draw.line(self.screen, BLACK, (shoulders.centerx - radius // 2, shoulders.y + 6),
                         (bag.right - 8, bag.y + 4), 6)   # the strap over his shoulder
        # The laptop sticking out of the top, its edge glowing in rainbow colours.
        laptop = pygame.Rect(bag.x + 6, bag.y - 12, bag.width - 12, 20)
        pygame.draw.rect(self.screen, (30, 30, 40), laptop, border_radius=3)
        glow = [NEON_PINK, NEON_CYAN, NEON_GREEN, NEON_YELLOW]
        colour = glow[int(self.t * 4) % len(glow)]   # RGB on, obviously
        pygame.draw.rect(self.screen, colour, laptop, 2, border_radius=3)
        pygame.draw.rect(self.screen, BLACK, bag, border_radius=8)
        pygame.draw.rect(self.screen, GREY_BAG, bag, 2, border_radius=8)
        label = self.small.render("MONSTER", True, colour)
        self.screen.blit(label, label.get_rect(center=bag.center))

    def portrait_cap(self, head, radius, shoulders):
        """
        A New Era style cap: a tall, stiff crown, a dead-flat brim seen from
        the front, the gold sticker still on it. The brim's shadow hides the eyes.
        """
        hx, hy = head
        brim_y = hy - radius // 4   # the cap sits just above the eyes
        self.darken(210, (hx - radius, brim_y, radius * 2, radius // 3), SHADOW)
        # The crown: tall and straight-sided, a little narrower at the top.
        top_y = brim_y - int(radius * 1.15)
        crown = [(hx - radius - 2, brim_y), (hx - radius + 8, top_y + 8), (hx - radius + 22, top_y),
                 (hx + radius - 22, top_y), (hx + radius - 8, top_y + 8), (hx + radius + 2, brim_y)]
        pygame.draw.polygon(self.screen, CAP_NAVY, crown)
        pygame.draw.polygon(self.screen, NEON_CYAN, crown, 2)
        self.text("NY", self.hud, WHITE, (hx, (brim_y + top_y) // 2 + 2), center=True)   # the logo
        # The brim: completely flat, so from the front it is a thin straight band.
        brim = pygame.Rect(0, 0, int(radius * 2.6), 8)
        brim.midtop = (hx, brim_y - 2)
        pygame.draw.rect(self.screen, CAP_NAVY, brim)
        pygame.draw.rect(self.screen, NEON_CYAN, brim, 1)
        # The round gold sticker, never peeled off.
        pygame.draw.circle(self.screen, GOLD_STICKER, (brim.right - 22, brim.centery), 7)
        pygame.draw.circle(self.screen, WHITE, (brim.right - 22, brim.centery), 7, 1)

    def portrait_glasses(self, head, radius, shoulders):
        """Big round glasses with shiny lenses."""
        self.round_glasses(head, radius, NEON_YELLOW, square=False)

    def portrait_nerd(self, head, radius, shoulders):
        """Square glasses with tape in the middle, a bow tie, and a joker card."""
        self.round_glasses(head, radius, WHITE, square=True)
        hx, hy = head
        pygame.draw.rect(self.screen, WHITE, (hx - 5, hy - radius // 6 - 6, 10, 12))   # the tape
        tie_y = shoulders.y + 10
        pygame.draw.polygon(self.screen, NEON_PINK, [(hx, tie_y), (hx - 18, tie_y - 10), (hx - 18, tie_y + 10)])
        pygame.draw.polygon(self.screen, NEON_PINK, [(hx, tie_y), (hx + 18, tie_y - 10), (hx + 18, tie_y + 10)])
        card = pygame.Rect(0, 0, 34, 48)
        card.center = (shoulders.right - radius * 0.7, shoulders.centery)
        pygame.draw.rect(self.screen, WHITE, card, border_radius=4)
        pygame.draw.rect(self.screen, NEON_RED, card, 2, border_radius=4)
        self.text("J", self.hud, NEON_RED, card.center, center=True)

    def portrait_energy(self, head, radius, shoulders):
        """A can with a lightning bolt, and shaky lines round the head."""
        hx, hy = head
        can = pygame.Rect(0, 0, radius * 0.7, radius * 1.2)
        can.midbottom = (shoulders.right - radius * 0.8, shoulders.centery + 10)
        pygame.draw.rect(self.screen, NEON_CYAN, can, border_radius=6)
        pygame.draw.rect(self.screen, WHITE, can, 2, border_radius=6)
        bolt = [(can.centerx + 4, can.y + 6), (can.centerx - 6, can.centery + 2),
                (can.centerx + 1, can.centery + 2), (can.centerx - 4, can.bottom - 6),
                (can.centerx + 7, can.centery - 4), (can.centerx, can.centery - 4)]
        pygame.draw.polygon(self.screen, NEON_YELLOW, bolt)
        jitter = 2 * math.sin(self.t * 40)   # he is shaking from the caffeine
        for side in (-1, 1):
            x = hx + side * (radius + 10) + jitter
            pygame.draw.line(self.screen, NEON_YELLOW, (x, hy - 14), (x + side * 8, hy - 4), 2)
            pygame.draw.line(self.screen, NEON_YELLOW, (x, hy + 2), (x + side * 8, hy + 12), 2)

    def portrait_frontrow(self, head, radius, shoulders):
        """An apple for the teacher, with a little heart above it."""
        apple = (int(shoulders.right - radius * 0.8), int(shoulders.centery))
        pygame.draw.circle(self.screen, NEON_RED, apple, radius // 2)
        pygame.draw.circle(self.screen, WHITE, (apple[0] - 6, apple[1] - 6), 4)
        pygame.draw.line(self.screen, (120, 70, 30), (apple[0], apple[1] - radius // 2),
                         (apple[0] + 3, apple[1] - radius // 2 - 10), 4)
        pygame.draw.ellipse(self.screen, NEON_GREEN, (apple[0] + 4, apple[1] - radius // 2 - 14, 14, 8))
        heart_y = apple[1] - radius - 4 + 3 * math.sin(self.t * 4)
        for side in (-1, 1):
            pygame.draw.circle(self.screen, NEON_PINK, (apple[0] + side * 5, heart_y), 6)
        pygame.draw.polygon(self.screen, NEON_PINK, [(apple[0] - 11, heart_y + 2), (apple[0] + 11, heart_y + 2),
                                                     (apple[0], heart_y + 14)])

    def portrait_veteran(self, head, radius, shoulders):
        """Grey hair at the sides (none on top any more), a grey beard, and a "#7" coffee mug, steaming."""
        hx, hy = head
        for side in (-1, 1):   # tufts of grey hair over the ears
            for k in range(3):
                tuft = (hx + side * (radius - 2), hy - radius // 3 + k * 9)
                pygame.draw.circle(self.screen, GREY_HAIR, tuft, 7)
        pygame.draw.arc(self.screen, WHITE, (hx - radius // 2, hy - radius + 6, radius, radius // 2),
                        math.pi * 0.2, math.pi * 0.8, 2)   # the shine of the bald top
        # The beard: grey dots round the chin, under the mouth.
        for k in range(14):
            angle = math.pi * (0.2 + 0.6 * k / 13)   # along the bottom of the face
            for depth in (0.72, 0.86):
                dot = (hx + radius * depth * math.cos(angle), hy + radius * depth * math.sin(angle))
                pygame.draw.circle(self.screen, GREY_HAIR, dot, 2)
        mug = pygame.Rect(0, 0, int(radius * 0.8), int(radius * 0.9))
        mug.midbottom = (shoulders.right - radius * 0.8, shoulders.centery + 14)
        pygame.draw.circle(self.screen, WHITE, (mug.right, mug.centery), mug.height // 3, 3)   # the handle
        pygame.draw.rect(self.screen, MUG_BROWN, mug, border_radius=5)
        pygame.draw.rect(self.screen, WHITE, mug, 2, border_radius=5)
        self.text("#7", self.small, NEON_YELLOW, mug.center, center=True)
        # Steam: two wavy lines rising out of the mug.
        for k, dx in enumerate((-6, 6)):
            points = [(mug.centerx + dx + 4 * math.sin(self.t * 3 + y / 5 + k), mug.y - 4 - y)
                      for y in range(0, 26, 4)]
            pygame.draw.lines(self.screen, WHITE, False, points, 2)

    def portrait_notme(self, head, radius, shoulders):
        """A drop of sweat running down his forehead, and a wrench held by the wrong end."""
        hx, hy = head
        drop_y = hy - radius // 2 + (self.t * 12) % 14   # it slides down, again and again
        drop = (hx + radius // 2 + 6, drop_y)
        pygame.draw.circle(self.screen, SWEAT, drop, 5)
        pygame.draw.polygon(self.screen, SWEAT, [(drop[0] - 5, drop[1] - 1), (drop[0] + 5, drop[1] - 1),
                                                 (drop[0], drop[1] - 12)])
        # The wrench, slanted, its open jaw down in his hand (the wrong way round).
        top = (shoulders.x + radius * 1.6, shoulders.y + radius * 0.45)
        jaw = (shoulders.x + radius * 0.45, shoulders.centery + 12)
        pygame.draw.line(self.screen, WRENCH_STEEL, top, jaw, 10)
        pygame.draw.circle(self.screen, WRENCH_STEEL, top, 9)                       # the closed ring end, up
        pygame.draw.circle(self.screen, SKIN, top, 4)
        pygame.draw.circle(self.screen, WRENCH_STEEL, jaw, 14)                      # the open jaw, down
        pygame.draw.circle(self.screen, SKIN, (jaw[0] - 4, jaw[1] + 9), 7)          # the gap in the jaw
        pygame.draw.circle(self.screen, SKIN, (int(jaw[0] + 4), int(jaw[1] - 6)), 9)  # his hand, round the jaw
        pygame.draw.circle(self.screen, NEON_PINK, (int(jaw[0] + 4), int(jaw[1] - 6)), 9, 2)

    def portrait_asker(self, head, radius, shoulders):
        """A hand up in the air (again), waving a little, and a "?" bubble."""
        hx, hy = head
        wave = 4 * math.sin(self.t * 6)   # "hocam! hocam!"
        shoulder = (shoulders.right - radius * 0.5, shoulders.y + radius * 0.4)
        hand = (shoulders.right - radius * 0.65 + wave, hy - radius * 0.6)
        # The arm: a thick band with a neon edge, like the shoulders.
        pygame.draw.line(self.screen, NEON_PINK, shoulder, hand, 22)
        pygame.draw.line(self.screen, SKIN, shoulder, hand, 16)
        # The open hand: a palm and four fingers up, the thumb out to the side.
        palm = pygame.Rect(0, 0, 26, 24)
        palm.center = hand
        for k in range(4):
            finger = pygame.Rect(palm.x + 1 + k * 6, palm.y - 14, 6, 20)
            pygame.draw.rect(self.screen, SKIN, finger, border_radius=3)
            pygame.draw.rect(self.screen, NEON_PINK, finger, 2, border_radius=3)
        pygame.draw.line(self.screen, NEON_PINK, (palm.x + 2, palm.centery), (palm.x - 10, palm.y + 2), 8)
        pygame.draw.line(self.screen, SKIN, (palm.x + 2, palm.centery), (palm.x - 9, palm.y + 3), 4)
        pygame.draw.ellipse(self.screen, SKIN, palm)
        pygame.draw.ellipse(self.screen, NEON_PINK, palm, 2)
        bubble = pygame.Rect(0, 0, 34, 30)
        bubble.center = (hx - radius - 10, hy - radius + 3 * math.sin(self.t * 3))
        pygame.draw.ellipse(self.screen, WHITE, bubble)
        pygame.draw.polygon(self.screen, WHITE, [(bubble.right - 10, bubble.bottom - 6),
                                                 (bubble.right + 2, bubble.bottom + 8),
                                                 (bubble.right - 2, bubble.bottom - 10)])
        self.text("?", self.hud, NEON_RED, bubble.center, center=True)

    def portrait_lazy(self, head, radius, shoulders):
        """
        Charisma 100: a big pompadour, aviator shades with a glint sweeping
        across, a one-sided smirk, a popped collar, a stand-up comedian's
        microphone, and sparkles round him.
        """
        hx, hy = head
        r = radius
        # The popped collar: two thin points standing up beside the neck.
        for side in (-1, 1):
            collar = [(hx + side * r * 0.4, shoulders.y + 6), (hx + side * r * 0.95, shoulders.y - r * 0.3),
                      (hx + side * r * 0.85, shoulders.y + r * 0.35)]
            pygame.draw.polygon(self.screen, JACKET, collar)
            pygame.draw.polygon(self.screen, NEON_CYAN, collar, 2)
        # The pompadour: a few round shapes on top of the head, swept up and
        # forward. Drawn twice: first all of them a bit bigger in pink (the
        # outline of the whole), then all of them dark on top.
        blobs = [((hx, hy - r * 0.55), r * 0.95, r * 0.55),            # the hair on top of the head
                 ((hx + r * 0.1, hy - r * 1.05), r * 0.85, r * 0.5),    # the big wave
                 ((hx + r * 0.65, hy - r * 1.1), r * 0.4, r * 0.38)]    # its curl at the front
        for outline in (True, False):
            for (bx, by), half_w, half_h in blobs:
                grow = 3 if outline else 0
                rect = pygame.Rect(0, 0, (half_w + grow) * 2, (half_h + grow) * 2)
                rect.center = (int(bx), int(by))
                pygame.draw.ellipse(self.screen, NEON_PINK if outline else QUIFF, rect)
        pygame.draw.arc(self.screen, NEON_PINK, (hx - r * 0.6, hy - r * 1.4, r * 1.3, r * 0.7),
                        math.pi * 0.25, math.pi * 0.9, 2)   # a shine on the wave
        # Aviator shades: two drops of dark glass, a gold rim, a glint every two seconds.
        eye_y = hy - r // 6
        glint = (self.t % 2.0) / 0.5   # 0..1 while the glint crosses, then it waits
        for side in (-1, 1):
            cx = hx + side * r * 0.42
            lens = [(cx - r * 0.33, eye_y - r * 0.18), (cx + r * 0.33, eye_y - r * 0.18),
                    (cx + r * 0.28, eye_y + r * 0.12), (cx, eye_y + r * 0.3), (cx - r * 0.28, eye_y + r * 0.12)]
            pygame.draw.polygon(self.screen, SHADOW, lens)
            pygame.draw.polygon(self.screen, NEON_YELLOW, lens, 2)
            if glint < 1:
                gx = cx - r * 0.3 + glint * r * 0.6
                pygame.draw.line(self.screen, WHITE, (gx, eye_y + r * 0.15), (gx + r * 0.15, eye_y - r * 0.15), 3)
        pygame.draw.line(self.screen, NEON_YELLOW, (hx - r * 0.12, eye_y - r * 0.12), (hx + r * 0.12, eye_y - r * 0.12), 2)
        # The smirk: flat on one side, up on the other.
        pygame.draw.lines(self.screen, WHITE, False, [(hx - r * 0.35, hy + r * 0.42), (hx, hy + r * 0.47),
                                                      (hx + r * 0.3, hy + r * 0.38), (hx + r * 0.42, hy + r * 0.26)], 3)
        # The microphone: a black handle in his hand, a grey mesh ball on top.
        hand = (int(shoulders.right - r * 0.75), int(shoulders.centery + 8))
        ball = (hand[0] - int(r * 0.25), hand[1] - int(r * 0.85))
        pygame.draw.line(self.screen, BLACK, hand, ball, 9)
        pygame.draw.line(self.screen, NEON_CYAN, (hand[0] + 5, hand[1]), (ball[0] + 5, ball[1]), 1)
        pygame.draw.circle(self.screen, GREY_BAG, ball, 11)
        for k in (-5, 0, 5):   # the mesh
            pygame.draw.line(self.screen, BLACK, (ball[0] + k, ball[1] - 9), (ball[0] + k, ball[1] + 9), 1)
            pygame.draw.line(self.screen, BLACK, (ball[0] - 9, ball[1] + k), (ball[0] + 9, ball[1] + k), 1)
        pygame.draw.circle(self.screen, WHITE, ball, 11, 2)
        pygame.draw.circle(self.screen, SKIN, hand, 11)
        pygame.draw.circle(self.screen, NEON_PINK, hand, 11, 2)
        # Sparkles twinkling round him.
        for k, (dx, dy) in enumerate(((-1.35, -1.1), (1.45, -0.45), (-1.5, 0.35))):
            size = 7 * max(0.0, math.sin(self.t * 3 + k * 2.1))
            if size > 1:
                self.sparkle((hx + dx * r, hy + dy * r), size, WHITE)

    def sparkle(self, centre, size, colour):
        """A four-pointed star (a twinkle)."""
        x, y = centre
        thin = size / 4
        pygame.draw.polygon(self.screen, colour, [(x, y - size), (x + thin, y - thin), (x + size, y), (x + thin, y + thin),
                                                  (x, y + size), (x - thin, y + thin), (x - size, y), (x - thin, y - thin)])

    def round_glasses(self, head, radius, colour, square):
        """Two lenses and a bridge over the eyes; square=True for the nerd's frames."""
        hx, hy = head
        eye_y = hy - radius // 6
        for side in (-1, 1):
            centre = (hx + side * radius // 2.6, eye_y)
            if square:
                lens = pygame.Rect(0, 0, 26, 22)
                lens.center = centre
                pygame.draw.rect(self.screen, colour, lens, 3)
            else:
                pygame.draw.circle(self.screen, colour, centre, 14, 3)
                pygame.draw.line(self.screen, WHITE, (centre[0] - 6, centre[1] - 7),
                                 (centre[0] - 2, centre[1] - 9), 2)   # a shine on the lens
        pygame.draw.line(self.screen, colour, (hx - 5, eye_y), (hx + 5, eye_y), 3)
