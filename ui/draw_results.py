"""
Drawing the results: after each exam, and after the whole run. Part of
Renderer (see render.py).

- After an exam that was handed in (or collected when time ran out): the
  score is counted up one part at a time, like in Balatro (draw_tally()).
  Each question's card pops in with its points, then the bonuses come, while
  the big score counts up and thumps. The timing is in logic/tally.py.
- After a failed exam (caught, too many warnings): the game over chat of
  the two logos (draw_scenes.py), with the menu under it.
- After the run (three exams): each exam's score, the total counted up, and
  the top scores with the new one lit up. A new top score gets a big
  "NEW HIGH SCORE!" with confetti, and the player types a three-letter
  name for it (name_boxes()) before the menu appears. A moment after the
  count, the semester's letter grade (logic/grade.py) is stamped on
  (grade_stamp()). After a single exam there is no letter, like at school:
  the score and the class average.
"""

import math
import random

import pygame

from logic.exam_paper import CORRECT, WRONG, EMPTY
from logic.game import WON
from logic.tally import parts_shown, appear_time, running_score, is_done, done_time
from settings import GAME_OVER_TIME, TOP_SCORES_KEPT, GRADE_STAMP_DELAY
from ui.draw_game import RESULT_COLOURS
from ui.draw_menus import MENU_HINT, MENU_PREVIEW_SIZE, INDICATOR_HEIGHT
from ui.draw_scenes import END_TEXTS, CHAT_MENU_TOP, CHAT_MENU_GAP
from ui.style import (WHITE, GREY, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED,
                      SHADOW, HUD_PURPLE, FOOTER_HEIGHT, mix)

# The score count after an exam (see logic/tally.py for its timing).
TALLY_TITLE_Y = 55             # pixels, the middle of "EXAM HANDED IN!"
TALLY_CARDS_TOP = 124          # pixels, the top of the question cards
TALLY_CARD = 56                # pixels, the size of a question card
TALLY_CARD_GAP = 92            # pixels from one card to the next (room for "+1000" over each)
TALLY_POP = 0.5                # how much bigger a card is when it pops in (0.5 = 50 %)
TALLY_POP_TIME = 0.2           # seconds a card takes to settle to its size
TALLY_BONUS_Y = 252            # pixels, the (first) row with the bonus points
TALLY_BONUS_ROW = 24           # pixels down to the second row of bonuses (more than three)
TALLY_BONUS_GAP = 305          # pixels between those (room for "EARLY BONUS +1000")
TALLY_SCORE_Y = 326            # pixels, the middle of the big score
TALLY_RUN_Y = 374              # pixels, the run's total so far, under the score
TALLY_THUMP = 0.25             # how much bigger the score thumps when a part arrives
TALLY_THUMP_TIME = 0.25        # seconds that thump takes to calm down
END_MENU_TOP = 428             # pixels, the first item of the menu after a handed-in exam
END_MENU_GAP = 52              # pixels between those items

# The run's results.
RUN_TITLE_Y = 52                   # pixels, the middle of "SEMESTER OVER"
RUN_PANEL = (40, 100, 540, 150)    # x, y, width, height of the box with the three exams, pixels
RUN_ROW = 42                       # pixels between the exams in it
RUN_OUTCOME_X = 380                # pixels from the box's left edge to the middle of the grade ("2.5/3")
RUN_TOTAL_Y = 292                  # pixels, the middle of the big total (under the exams' box)
RUN_TOP_PANEL = (610, 100, 310, 235)  # x, y, width, height of the top scores box, pixels
NEW_TOP_Y = 362                    # pixels, the middle of "NEW HIGH SCORE!" (while typing the name)
RUN_MENU_TOP = 412                 # pixels, the first item of the menu after the run
RUN_MENU_GAP = 56                  # pixels between those items (the selected one is bigger: they must not touch)
TOP_ROW = 34                       # pixels between the rows of a top scores list
# The columns of a top scores row, as parts of the box's width from its left edge.
TOP_NAME_X = 0.15                  # where the name starts
TOP_SCORE_X = 0.70                 # where the score ends
NO_NAME = "---"                    # shown for a score without a name (yet, or from an old file)
# Typing the name of a new top score.
NAME_TITLE_Y = 412                 # pixels, the middle of "ENTER YOUR NAME"
NAME_BOX_Y = 485                   # pixels, the middle of the letter boxes
NAME_BOX = (62, 74)                # pixels, width and height of a letter box
NAME_BOX_GAP = 34                  # pixels between the letter boxes (room for the "next" bar)
NAME_ARROW = 12                    # pixels, the size of the up/down arrows at the chosen letter
# The semester grade's stamp.
STAMP_CENTRE = (822, 425)          # pixels, its middle: under the top scores, right of the menu
STAMP_SIZE = (200, 128)            # pixels, width and height
STAMP_ANGLE = -8                   # degrees it is turned, like a rubber stamp put down quickly
STAMP_DROP = 1.5                   # how much bigger it starts (1.5 = 150 % bigger), then lands
STAMP_DROP_TIME = 0.15             # seconds it takes to land
ORANGE = (255, 150, 40)
GRADE_COLOURS = {"AA": NEON_GREEN, "BA": NEON_CYAN, "BB": NEON_CYAN, "CB": NEON_YELLOW,
                 "CC": NEON_YELLOW, "DC": ORANGE, "DD": ORANGE, "FD": NEON_RED, "FF": NEON_RED}
NAME_HINT = ("HEAD: tilt up/down = letter   turn right = next   turn left = back"
             "        KEYS: type it, Enter")
CONFETTI_COUNT = 60                # pieces of confetti for a new top score
CONFETTI_FALL = 140                # pixels per second the confetti falls
CONFETTI_COLOURS = [NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN]
OUTCOME_TEXTS = {"caught": "CAUGHT", "warnings": "3 WARNINGS"}   # a failed exam, in the run's list


class ResultsDrawing:
    # ------------------------------------------------------------------
    # After one exam
    # ------------------------------------------------------------------
    def draw_end(self, game, run, chat, labels, selected, select_progress, back_progress,
                 head_pause, elapsed, class_average=None):
        """
        Drawn when an exam is over, with a small menu (next exam / main menu,
        or see the run's results after the last one). A handed-in exam gets
        the score count (draw_tally()); elapsed = seconds since this screen
        opened. A failed one is the game over chat (finished, both logos
        laughing) with the menu under it, so the screen does not change when
        the chat ends. chat: the conversation the game over scene showed.
        class_average: the average of the earlier plays of this exam, or
        None (the first time).
        """
        total = f"RUN TOTAL  {run.total()}"
        if game.state != WON:
            subtitle = f"{END_TEXTS[game.lose_reason]}    EXAM 0    {total}"
            self.chat_screen(chat, GAME_OVER_TIME, subtitle)
            self.menu_items(labels, selected, CHAT_MENU_TOP, select_progress, CHAT_MENU_GAP)
            self.corner_indicator(head_pause)
            self.footer(MENU_HINT, back_progress)
            return
        self.darken(215, colour=HUD_PURPLE)
        self.screen.blit(self.scanlines, (0, 0))
        done = self.draw_tally(game, elapsed)
        if done:
            if class_average is not None:
                total += f"      CLASS AVERAGE  {class_average}"
            self.shadow_text(total, self.hud, NEON_CYAN, (self.width // 2, TALLY_RUN_Y),
                             center=True)
        self.menu_items(labels, selected, END_MENU_TOP, select_progress, END_MENU_GAP)
        self.corner_indicator(head_pause)
        self.footer(MENU_HINT if done else "Space = skip the count", back_progress)

    def corner_indicator(self, head_pause):
        """The "HEAD CONTROL" / "KEYBOARD" box at the bottom right of the results."""
        self.head_indicator(head_pause, self.width - MENU_PREVIEW_SIZE[0] - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10,
                            MENU_PREVIEW_SIZE[0])

    def thumped(self, message, font, colour, centre, parts, elapsed):
        """Neon text that thumps bigger each time a part of the count arrives."""
        shown = parts_shown(parts, elapsed)
        thump = 0.0
        if shown:
            thump = max(0.0, 1 - (elapsed - appear_time(shown - 1)) / TALLY_THUMP_TIME)
        self.blit_turned(self.neon_text(message, font, colour), centre, 0, 1 + TALLY_THUMP * thump)

    def draw_tally(self, game, elapsed):
        """
        The handed-in exam, counted up like in Balatro: each question's card
        pops up in its colour with its points over it, then the bonuses
        appear, while the big score counts up and thumps on every part.
        Returns True when the count is over.
        """
        cx = self.width // 2
        title = "TIME'S UP - PAPER COLLECTED" if game.time_ran_out else "EXAM HANDED IN!"
        self.shout(title, self.hud_huge, NEON_GREEN, (cx, TALLY_TITLE_Y))
        parts = game.score_parts()
        shown = parts_shown(parts, elapsed)
        results = game.paper.results()
        questions = len(results)

        # One card per question: an outline until its turn, then it pops in.
        left = cx - (questions * TALLY_CARD_GAP - (TALLY_CARD_GAP - TALLY_CARD)) // 2
        for i, written in enumerate(game.paper.written):
            card = pygame.Rect(left + i * TALLY_CARD_GAP, TALLY_CARDS_TOP, TALLY_CARD, TALLY_CARD)
            if i >= shown:
                pygame.draw.rect(self.screen, NEON_PINK, card, 2)
                self.text(written, self.hud_big, GREY, card.center, center=True)
                continue
            since = elapsed - appear_time(i)
            colour = RESULT_COLOURS[results[i]]
            face = pygame.Surface(card.size, pygame.SRCALPHA)
            face.fill(colour)
            pygame.draw.rect(face, WHITE, face.get_rect(), 3)
            letter = self.hud_big.render(written, True, SHADOW)
            face.blit(letter, letter.get_rect(center=face.get_rect().center))
            pop = 1 + TALLY_POP * max(0.0, 1 - since / TALLY_POP_TIME)   # big at first, then settles
            self.blit_turned(face, card.center, 0, pop)
            points = parts[i][1]
            rise = 10 * min(1.0, since / TALLY_POP_TIME)   # the points float up a little
            self.shadow_text(f"{points:+d}" if points else "0", self.hud_small, colour,
                             (card.centerx, card.top - 12 - rise), center=True)

        # The grade, once every question is counted.
        if shown >= questions:
            grade = f"GRADE  {game.paper.points():g} / {questions}"
            self.shadow_text(grade, self.hud, WHITE, (cx, TALLY_CARDS_TOP + TALLY_CARD + 22),
                             center=True)
            counts = (f"{game.paper.count(CORRECT)} right   {game.paper.count(WRONG)} wrong   "
                      f"{game.paper.count(EMPTY)} blank")
            self.shadow_text(counts, self.small, WHITE, (cx, TALLY_CARDS_TOP + TALLY_CARD + 48),
                             center=True)

        # The bonuses, side by side, each when its turn comes: up to three
        # in a row; more go on a second row, in smaller letters.
        bonuses = parts[questions:]
        font = self.hud if len(bonuses) <= 3 else self.hud_small
        for j, (name, points) in enumerate(bonuses):
            if questions + j >= shown:
                break
            row, column = divmod(j, 3)
            in_row = min(3, len(bonuses) - row * 3)   # how many share this row
            x = cx + (column - (in_row - 1) / 2) * TALLY_BONUS_GAP
            colour = NEON_CYAN if points >= 0 else NEON_RED
            self.shadow_text(f"{name} {points:+d}", font, colour,
                             (x, TALLY_BONUS_Y + row * TALLY_BONUS_ROW), center=True)

        self.thumped(f"SCORE  {running_score(parts, elapsed)}", self.hud_huge, NEON_YELLOW,
                     (cx, TALLY_SCORE_Y), parts, elapsed)
        return is_done(parts, elapsed)

    # ------------------------------------------------------------------
    # After the run
    # ------------------------------------------------------------------
    def draw_run_end(self, run, top, new_place, labels, selected, select_progress,
                     back_progress, head_pause, elapsed, name_entry=None, semester=None):
        """
        The run is over: each exam's result appears in turn while the total
        counts up (the same count as after an exam), next to the top
        scores. new_place: where this run got in the top scores (0 = first),
        or None. A new top score: its row lights up and, once the count is
        over, "NEW HIGH SCORE!" with confetti. name_entry: its name being
        typed (NameEntry); until it is done, the letter boxes instead of the
        menu. semester: the run's grade {"letter", "average", "curved"}
        (main.py's record_run()), stamped on after the count.
        """
        self.menu_background()
        self.menu_title("SEMESTER OVER", RUN_TITLE_Y)
        parts = run.score_parts()
        shown = parts_shown(parts, elapsed)
        done = is_done(parts, elapsed)

        # The exams, one row each, appearing in turn.
        self.panel(RUN_PANEL)
        x, y, width, _ = RUN_PANEL
        for i, result in enumerate(run.results):
            row_y = y + 32 + i * RUN_ROW
            self.shadow_text(f"{i + 1}. {result['title']}", self.hud, WHITE, (x + 18, row_y - 14))
            if i >= shown:
                continue
            if result["handed_in"]:
                outcome = f"{result['points']:g}/{result['questions']}"   # the grade
                colour = NEON_GREEN
            else:
                outcome, colour = OUTCOME_TEXTS[result["lose_reason"]], NEON_RED
            self.shadow_text(outcome, self.hud_small, colour, (x + RUN_OUTCOME_X, row_y), center=True)
            score = self.hud.render(f"{result['score']}", True, NEON_YELLOW)
            self.screen.blit(score, score.get_rect(midright=(x + width - 18, row_y)))

        self.thumped(f"TOTAL  {running_score(parts, elapsed)}", self.hud_huge, NEON_YELLOW,
                     (x + width // 2, RUN_TOTAL_Y), parts, elapsed)

        # The top scores; the new one only shows once the count is over,
        # with the name as it is being typed.
        typing = name_entry is not None and not name_entry.done
        self.top_scores(top, RUN_TOP_PANEL, new_place if done else None, hide=None if done else new_place,
                        typed_name=name_entry.name() if typing else None)
        if done and new_place is not None:
            self.confetti(elapsed - appear_time(len(parts) - 1))

        stamp_time = elapsed - done_time(parts) - GRADE_STAMP_DELAY
        if semester is not None and stamp_time >= 0:
            self.grade_stamp(semester, stamp_time)

        self.corner_indicator(head_pause)
        if typing:
            self.menu_rects = []   # nothing to click until the name is typed
            if done:
                # Only now: once the name is typed, the menu needs the room
                # (the lit-up row in the top scores still shows it).
                self.shout(f"NEW HIGH SCORE!  #{new_place + 1}", self.hud_big, NEON_YELLOW,
                           (self.width // 2, NEW_TOP_Y), wobble=3, pulse=0.08)
                self.name_boxes(name_entry, select_progress)
                self.footer(NAME_HINT, back_progress)
            else:
                self.footer("Space = skip the count")
            return
        self.menu_items(labels, selected, RUN_MENU_TOP, select_progress, RUN_MENU_GAP)
        self.footer(MENU_HINT if done else "Space = skip the count", back_progress)

    def grade_stamp(self, semester, since):
        """
        The semester's letter grade as a rubber stamp in its colour, landing
        from bigger (`since`: seconds since it was put down). Under the
        letter: the class average it was curved on, or that there is no
        class yet (the first runs are graded without a curve).
        """
        letter = semester["letter"]
        colour = GRADE_COLOURS.get(letter, WHITE)
        stamp = pygame.Surface(STAMP_SIZE, pygame.SRCALPHA)
        rect = stamp.get_rect()
        pygame.draw.rect(stamp, (*HUD_PURPLE, 225), rect, border_radius=14)
        pygame.draw.rect(stamp, colour, rect, 5, border_radius=14)
        caption = self.small.render("SEMESTER GRADE", True, colour)
        stamp.blit(caption, caption.get_rect(midtop=(rect.centerx, 12)))
        big = self.neon_text(letter, self.hud_huge, colour)
        stamp.blit(big, big.get_rect(center=(rect.centerx, rect.centery + 4)))
        if semester["curved"]:
            note = f"CLASS AVG {semester['average']}"
        else:
            note = "NO CLASS CURVE YET"
        note_image = self.small.render(note, True, WHITE)
        stamp.blit(note_image, note_image.get_rect(midbottom=(rect.centerx, rect.bottom - 8)))
        landing = max(0.0, 1 - since / STAMP_DROP_TIME)   # 1 = just put down, 0 = landed
        self.blit_turned(stamp, STAMP_CENTRE, STAMP_ANGLE, 1 + STAMP_DROP * landing)

    def name_boxes(self, name_entry, select_progress):
        """
        "ENTER YOUR NAME" and one box per letter. The chosen box glows, with
        arrows above and below (tilt up/down) and a bar under it while the
        head is turned right (on to the next letter).
        """
        cx = self.width // 2
        self.shadow_text("ENTER YOUR NAME", self.hud, NEON_CYAN, (cx, NAME_TITLE_Y), center=True)
        count = len(name_entry.letters)
        box_w, box_h = NAME_BOX
        left = cx - (count * box_w + (count - 1) * NAME_BOX_GAP) // 2
        glow = (math.sin(self.t * 8) + 1) / 2   # 0..1, the chosen box pulses
        for i, letter in enumerate(name_entry.letters):
            box = pygame.Rect(left + i * (box_w + NAME_BOX_GAP), 0, box_w, box_h)
            box.centery = NAME_BOX_Y
            chosen = i == name_entry.slot
            self.darken(200, box, HUD_PURPLE)
            colour = mix(NEON_PINK, NEON_YELLOW, glow) if chosen else NEON_CYAN
            pygame.draw.rect(self.screen, colour, box, 4 if chosen else 2, border_radius=6)
            self.shadow_text(letter, self.hud_huge, NEON_YELLOW if chosen else WHITE, box.center,
                             center=True)
            if chosen:
                a = NAME_ARROW
                top_tip, bottom_tip = box.top - 6 - a, box.bottom + 6 + a
                pygame.draw.polygon(self.screen, colour, [(box.centerx - a, box.top - 6),
                                                          (box.centerx + a, box.top - 6),
                                                          (box.centerx, top_tip)])
                pygame.draw.polygon(self.screen, colour, [(box.centerx - a, box.bottom + 6),
                                                          (box.centerx + a, box.bottom + 6),
                                                          (box.centerx, bottom_tip)])
                if select_progress > 0:
                    bar = pygame.Rect(box.right + 10, box.top, 8, box.height)
                    pygame.draw.rect(self.screen, SHADOW, bar)
                    filled = int(bar.height * select_progress)
                    pygame.draw.rect(self.screen, NEON_CYAN, (bar.x, bar.bottom - filled, bar.width, filled))

    def top_scores(self, top, rect, highlight=None, hide=None, typed_name=None):
        """
        The top scores in a box: "1.  EFE  5230   7 OCT" per row, best first.
        highlight: the row of a new top score (lit up and pulsing).
        hide: a row not to show yet (the new score while it is still counting).
        typed_name: the highlighted row's name while it is being typed.
        """
        self.panel(rect)
        x, y, width, _ = rect
        self.shadow_text("TOP SCORES", self.hud, NEON_CYAN, (x + width // 2, y + 22), center=True)
        rows = [entry for i, entry in enumerate(top) if i != hide]
        if not rows:
            self.shadow_text("No runs yet - be the first!", self.small, WHITE,
                             (x + width // 2, y + 70), center=True)
            return
        for i, entry in enumerate(rows[:TOP_SCORES_KEPT]):
            row_y = y + 58 + i * TOP_ROW
            colour = WHITE
            if i == highlight:
                # The new one: a pulsing neon bar behind it.
                glow = (math.sin(self.t * 8) + 1) / 2
                self.darken(int(120 + 100 * glow), (x + 6, row_y - 15, width - 12, 30), NEON_PINK)
                colour = mix(NEON_YELLOW, WHITE, glow)
            self.shadow_text(f"{i + 1}.", self.hud_small, colour, (x + 14, row_y - 10))
            name = typed_name if i == highlight and typed_name is not None else entry["name"]
            self.shadow_text(name or NO_NAME, self.hud_small, colour if name else GREY,
                             (x + width * TOP_NAME_X, row_y - 10))
            score = self.hud.render(str(entry["score"]), True, colour)
            self.screen.blit(score, score.get_rect(midright=(x + width * TOP_SCORE_X, row_y)))
            date = self.small.render(entry["date"], True, colour if i == highlight else GREY)
            self.screen.blit(date, date.get_rect(midright=(x + width - 14, row_y)))

    def confetti(self, since):
        """
        Confetti raining down for a new top score: each piece has its own
        place, speed, swing and colour (always the same, from a fixed seed),
        and falls from the top, wrapping round to the top again.
        """
        pieces = random.Random(7)
        for _ in range(CONFETTI_COUNT):
            x0 = pieces.uniform(0, self.width)
            speed = CONFETTI_FALL * pieces.uniform(0.6, 1.4)
            swing = pieces.uniform(10, 30)
            colour = pieces.choice(CONFETTI_COLOURS)
            start = pieces.uniform(0, self.height)
            y = (start + speed * since) % (self.height + 20) - 20
            x = x0 + swing * math.sin(since * 3 + x0)
            angle = since * 200 + x0   # tumbling
            piece = pygame.Surface((10, 5), pygame.SRCALPHA)
            piece.fill(colour)
            self.blit_turned(piece, (x, y), angle)
