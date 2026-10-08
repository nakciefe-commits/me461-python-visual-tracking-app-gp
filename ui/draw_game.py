"""
Drawing the game screen: the classroom picture (or what you look at while
looking away) with see-through strips on top: answers, warnings and the exam
clock at the top, the suspicion bar at the bottom. Also the popup band and
the "face not found" pause. Part of Renderer (see render.py). No webcam
picture: the player does not see their own face in the game.

The classroom with the teacher is only shown while the player looks at the
screen. Looking away shows their own paper, or a neighbour's paper, with no
teacher in it, so the teacher can only be checked by really looking (and
heard, through the sounds).

The player's character shows too: a badge under the top strip (its name,
the nerd's jokers and deadline, the energy drink's sugar rush or crash),
the classroom blurry at first for glasses, and eyelids closing during the
energy drink addict's sleepy spells.
"""

import math

import pygame

from logic.exam_paper import UNKNOWN, BLANK, CORRECT, WRONG, EMPTY
from tracking.head_tracker import DOWN, LEFT, RIGHT
from settings import MAX_WARNINGS, CHARACTERS, DEFAULT_CHARACTER
from logic.character import RUSH
from ui.style import (BLACK, WHITE, GREY, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED,
                   SHADOW, HUD_PURPLE,
                   HUD_ALPHA, HUD_LINE, TEXT_WOBBLE)
from logic.suspicion import GRACE_PART

TOP_BAR = 56                   # height of the strip at the top, pixels
BOTTOM_BAR = 46                # height of the strip at the bottom (the suspicion bar), pixels
CLOCK_RED_BELOW = 15           # seconds; the exam clock turns red under this
CLOCK_PULSE = 0.25             # how much bigger the clock thumps each second at the end
# The colour of each graded answer on the end screen.
RESULT_COLOURS = {CORRECT: NEON_GREEN, WRONG: NEON_RED, EMPTY: GREY}
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
# Blurring the neighbour's view until it is sharp (neighbours.clarity()): the
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

BADGE_TOP = TOP_BAR + 8       # pixels, the top of the character badge (under the top strip)
BADGE_WIDTH = 300              # pixels
EYELID_CLOSED = 0.3           # 0..1 of the screen's height each eyelid covers at most while sleepy
EYELID_BLINK = 1.8             # radians per second: how fast the sleepy eyes close and open

# Which neighbour, for the look-away text ("Copying answer 2 from the left")
LOOK_AWAY = {
    LEFT: "from the left",
    RIGHT: "from the right",
}


class GameDrawing:
    def answer_boxes(self, game, x, y, graded=False):
        """
        One box per question with what you wrote ("-" = left blank).
        graded=True (end screen) colours them by RESULT_COLOURS.
        """
        written = game.paper.written
        results = game.paper.results()
        for i in range(game.paper.size()):
            box = pygame.Rect(x + i * 30, y, 22, 22)
            if i < len(written):
                if graded:
                    colour = RESULT_COLOURS[results[i]]
                else:
                    colour = GREY if written[i] == BLANK else NEON_CYAN
                pygame.draw.rect(self.screen, colour, box)
                self.text(written[i], self.hud_small, SHADOW, box.center, center=True)
            else:
                pygame.draw.rect(self.screen, NEON_PINK, box, 2)

    def neighbour_picture(self, game, side):
        """
        The picture of a neighbour with what is on their paper (the letter
        circled, or "?"). It is shown from the start of a look, but blurred
        until game.neighbours.clarity() reaches 1, so it cannot be read early.
        None if that picture is missing (then the plain one and a note).
        """
        says = game.paper.says(side)
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
        q = game.paper.question() + 1
        if direction == DOWN:
            if game.knows_answer():
                first = f"Press A-D to write answer {q}   (S = blank)"
            elif game.jokers > 0:
                first = f"Answer {q}: J = joker, A-D = guess"
            else:
                first = f"Answer {q}: guess with A-D, or S = blank"
            # Looking at the paper you hear nothing either (see teacher.sounds()).
            return first, "Wrong -0.5, blank 0.  You can't see or hear the teacher"
        shown = game.paper_shows(direction)
        if shown is None:
            first = f"Reading answer {q} {LOOK_AWAY[direction]} - keep looking"
        elif shown == UNKNOWN:
            first = "They don't know this one - try the other side"
        else:
            first = "Remember it, then look at your paper and write it"
        return first, "You can't see the teacher - listen!"

    def draw_game(self, game, teacher, direction, view, yaw, pitch, fps,
                  tracking_note, show_teacher_state, clarity=1.0):
        """
        view: how visible the classroom is, 0 = black (looking away) to
        1 = fully shown. main.py raises it over FADE_TIME after the player
        looks at the screen. clarity: how sharp the classroom is, 0..1
        (glasses see it blurry at first, logic/character.py).
        """
        cx = self.width // 2

        # The classroom, or what you look at while looking away.
        if view > 0:
            self.screen.blit(self.blurred(self.picture(teacher.image_name()), clarity), (0, 0))
            if view < 1:
                self.darken(int(255 * (1 - view)))   # fading in from black
            if game.is_sleepy():
                self.eyelids()
        elif direction in LOOK_AWAY_IMAGES:
            if direction == DOWN:
                self.screen.blit(self.picture(LOOK_AWAY_IMAGES[DOWN]), (0, 0))
                # Your answers so far, "handwritten" on the answer lines.
                for i, letter in enumerate(game.paper.written):
                    self.text(letter, self.big, PENCIL, (OWN_ANSWER_X, OWN_ANSWER_Y[i]),
                              center=True)
                strip_top = TOP_BAR   # at the top: lines 4 and 5 are at the bottom
                text_x = cx
            else:
                picture = self.neighbour_picture(game, direction)
                clarity = game.neighbours.clarity(direction)
                if picture is not None:
                    self.screen.blit(self.blurred(self.picture(picture), clarity), (0, 0))
                else:
                    # No picture with that letter: the plain one, and a note once read.
                    plain = self.picture(LOOK_AWAY_IMAGES[direction])
                    self.screen.blit(self.blurred(plain, clarity), (0, 0))
                    if game.paper_shows(direction) is not None:
                        self.neighbour_note(direction, game.paper_shows(direction))
                # Just above the bars, so it does not cover the neighbour's paper.
                strip_top = self.height - BOTTOM_BAR - LOOK_AWAY_STRIP
                text_x = cx
            if game.is_sleepy():
                self.eyelids()   # under the text strip, so the hint stays readable
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
                                 (label.right + 12 + game.paper.size() * 30 + 20, 16))
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

        # Looking down, the text strip is at the top: the badge goes under it.
        self.character_badge(game, BADGE_TOP + (LOOK_AWAY_STRIP if direction == DOWN and view == 0 else 0))

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
        suspicion = game.suspicion.level
        danger = suspicion >= GRACE_PART or game.suspicion.seen_copying
        self.bar(bar_x, top + 12, bar_width, 24, suspicion, NEON_PINK if danger else NEON_YELLOW)
        marker_x = bar_x + bar_width * GRACE_PART
        pygame.draw.line(self.screen, WHITE, (marker_x, top + 8), (marker_x, top + 40), 3)

    def eyelids(self):
        """The energy drink addict is sleepy: dark eyelids slowly close and open from top and bottom."""
        closed = EYELID_CLOSED * (0.6 + 0.4 * math.sin(self.t * EYELID_BLINK))   # never fully shut
        lid = int(self.height * closed)
        self.darken(245, (0, 0, self.width, lid), SHADOW)
        self.darken(245, (0, self.height - lid, self.width, lid), SHADOW)
        self.shout("Z z z", self.hud_big, NEON_CYAN, (self.width // 2, lid + 30), wobble=6)

    def character_badge(self, game, top):
        """
        A small box under the top strip, left: who you are, and what your
        character has going on (jokers left, the nerd's deadline, a sugar
        rush or a crash). Not for the plain character.
        """
        if game.character == DEFAULT_CHARACTER:
            return
        notes = []
        if game.rules["jokers"]:
            notes.append(f"JOKER x{game.jokers}  (J)")
        if game.deadline() > 0:
            left = max(0, int(game.time_left - game.deadline() + 0.999))   # seconds until the deadline
            notes.append("TOO LATE!" if game.missed_deadline else f"HAND IN WITHIN {left // 60}:{left % 60:02d}")
        if game.energy is not None:
            if game.energy.day == RUSH:
                notes.append("SUGAR RUSH")
            else:
                notes.append("ZZZ... SLEEPY" if game.is_sleepy() else "CRASH DAY")
        height = 26 + 20 * len(notes)
        box = pygame.Rect(12, top, BADGE_WIDTH, height)
        self.darken(HUD_ALPHA, box, HUD_PURPLE)
        pygame.draw.rect(self.screen, NEON_PINK, box, 2)
        self.shadow_text(CHARACTERS[game.character]["name"], self.hud_small, NEON_YELLOW,
                         (box.x + 10, box.y + 4))
        for i, note in enumerate(notes):
            colour = NEON_RED if note == "TOO LATE!" else NEON_CYAN
            self.shadow_text(note, self.hud_small, colour, (box.x + 10, box.y + 24 + i * 20))

    def draw_popup(self, message):
        """A dark band across the screen with the message, drawn on top of the game."""
        band = pygame.Rect(0, self.height // 2 - 105, self.width, 90)
        self.darken(210, band, HUD_PURPLE)
        self.screen.fill(NEON_PINK, (0, band.top, self.width, HUD_LINE))
        self.screen.fill(NEON_PINK, (0, band.bottom - HUD_LINE, self.width, HUD_LINE))
        self.shout(message.upper(), self.hud, NEON_YELLOW, band.center, wobble=2)
    def draw_paused(self):
        """Drawn on top of the game screen while no face is seen."""
        self.darken(190, colour=HUD_PURPLE)
        cx, cy = self.width // 2, self.height // 2
        self.shout("FACE NOT FOUND", self.hud_huge, NEON_PINK, (cx, cy - 30))
        self.shadow_text("Game paused - look at the camera to continue", self.medium, WHITE,
                         (cx, cy + 40), center=True)
