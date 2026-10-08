"""
Drawing the results: after each exam, and after the whole run. Part of
Renderer (see render.py).

- After an exam that was handed in (or collected when time ran out): the
  score is counted up one part at a time, like in Balatro (draw_tally()),
  in two tables: the questions on the left (what you wrote, the answer key,
  right/wrong/blank, the points), the bonuses on the right. Each row lights
  up in its colour when its turn comes, while the big score rolls up like
  the reels of a slot machine (slot_score()): the bigger the score, the
  more it shakes, sparks and flashes. The timing is in logic/tally.py.
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
from logic.tally import (parts_shown, appear_time, running_value, is_done, done_time, is_counting,
                         strength, jackpot)
from settings import (GAME_OVER_TIME, TOP_SCORES_KEPT, GRADE_STAMP_DELAY, TALLY_SHAKE, TALLY_SPARKS,
                      QUIZZES)
from ui.draw_briefing import GOLD_DARK, GOLD, GOLD_LIGHT, BULB_OFF
from ui.draw_game import RESULT_COLOURS
from ui.draw_menus import MENU_HINT, INDICATOR_WIDTH, INDICATOR_HEIGHT
from ui.draw_scenes import END_TEXTS, CHAT_MENU_TOP, CHAT_MENU_GAP
from ui.style import (WHITE, GREY, NEON_PINK, NEON_CYAN, NEON_YELLOW, NEON_GREEN, NEON_RED,
                      SHADOW, HUD_PURPLE, FOOTER_HEIGHT, mix)

# The score count after an exam (see logic/tally.py for its timing).
TALLY_TITLE_Y = 42             # pixels, the middle of "EXAM HANDED IN!"
# The two tables: (x, y, width, height) in pixels. The questions on the
# left, the bonuses on the right; tall enough for 5 questions + the grade
# and for 7 bonuses.
QUESTION_TABLE = (40, 82, 450, 228)
BONUS_TABLE = (510, 82, 410, 228)
TABLE_HEADER = 30              # pixels, the header row of a table
TABLE_ROW = 26                 # pixels, each row under it
# The question table's columns, as pixels from the table's left edge
# (the middle of the column; the points end at the last one).
QUESTION_COLUMNS = {"Q": 30, "YOU": 105, "KEY": 180, "RESULT": 270, "POINTS": 430}
RESULT_NAMES = {CORRECT: "RIGHT", WRONG: "WRONG", EMPTY: "BLANK"}
ROW_FLASH_TIME = 0.35          # seconds a row glows in its colour after its turn comes
ROW_POP = 0.5                  # how much bigger its points are when they appear (0.5 = 50 %)
TALLY_SCORE_Y = 356            # pixels, the middle of the big score
TALLY_RUN_Y = 412              # pixels, the run's total so far, under the score
TALLY_THUMP = 0.25             # how much bigger the score thumps when a part arrives
TALLY_THUMP_TIME = 0.25        # seconds that thump takes to calm down
END_MENU_TOP = 460             # pixels, the first item of the menu after a handed-in exam
END_MENU_GAP = 50              # pixels between those items
# The slot-machine score: one reel (a little window with a rolling drum)
# per digit, in a gold frame with bulbs, like the MOOD-O-MATIC.
REEL_CELL = (42, 62)           # pixels, width and height of one digit's window
REEL_GAP = 6                   # pixels between the windows
REEL_DIGITS = 4                # the score always has at least this many reels (0040)
REEL_BLUR = 8                  # digits per second; a reel faster than this leaves blurred copies
REEL_LABEL_GAP = 14            # pixels between "SCORE" and the reels
DRUM_PAPER = (245, 240, 225)   # the reels' paper-white drum
DRUM_INK = (40, 30, 60)        # the digits on it
SPARK_TIME = 0.7               # seconds a burst of sparks flies when a part arrives
SPARK_SPEED = (120, 360)       # pixels per second, slowest and fastest spark
SPARK_GRAVITY = 500            # pixels per second², the sparks fall
SPARK_COLOURS = [NEON_YELLOW, GOLD_LIGHT, NEON_PINK, NEON_CYAN]
JACKPOT_FLASH = 0.4            # seconds between "JACKPOT!" and the label, once the count ends

# The run's results.
RUN_TITLE_Y = 52                   # pixels, the middle of "SEMESTER OVER"
RUN_PANEL = (40, 100, 540, 150)    # x, y, width, height of the box with the three exams, pixels
RUN_ROW = 42                       # pixels between the exams in it
RUN_OUTCOME_X = 380                # pixels from the box's left edge to the middle of the grade ("2.5/3")
RUN_TOTAL_Y = 302                  # pixels, the middle of the big total (under the exams' box)
RUN_TOTAL_SHIFT = 18               # pixels the total sits left of the box's middle
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
        total = "PRACTICE - NOT COUNTED" if run.practice else f"RUN TOTAL  {run.total()}"
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
        self.head_indicator(head_pause, self.width - INDICATOR_WIDTH - 16,
                            self.height - FOOTER_HEIGHT - INDICATOR_HEIGHT - 10,
                            INDICATOR_WIDTH)

    # ------------------------------------------------------------------
    # The slot-machine score
    # ------------------------------------------------------------------
    def slot_score(self, label, parts, elapsed, centre, exams=1):
        """
        The score counting up like a slot machine: "SCORE" and one rolling
        reel per digit in a gold frame with bulbs. How wild it is grows with
        the score (tally.strength()): while it counts it shakes, the bulbs
        chase round, and every part that arrives throws sparks; the label
        thumps. A huge score ends with "JACKPOT!" and flashing bulbs.
        exams: how many exams the score adds up (the run's total: 3).
        """
        value = running_value(parts, elapsed)
        final = max(0, sum(points for _, points in parts))
        power = strength(max(0.0, value), exams)   # grows as the score climbs
        counting = is_counting(parts, elapsed)
        won_big = is_done(parts, elapsed) and jackpot(final, exams)
        shown = parts_shown(parts, elapsed)
        since = elapsed - appear_time(shown - 1) if shown else 1e9   # since the newest part

        # The label: thumps when a part arrives; flashes "JACKPOT!" after a big one.
        word, colour = label, NEON_YELLOW
        if won_big and int(self.t / JACKPOT_FLASH) % 2 == 0:
            word, colour = "JACKPOT!", NEON_PINK
        label_image = self.neon_text(word, self.hud_huge, colour)
        # The label's room is as wide as the wider of the two words, so the
        # reels stay put while it flashes.
        label_width = max(self.hud_huge.size(label)[0], self.hud_huge.size("JACKPOT!")[0])
        thump = 1 + TALLY_THUMP * max(0.0, 1 - since / TALLY_THUMP_TIME)

        # Enough reels for the biggest number the count will show.
        biggest, total = final, 0
        for _, points in parts:
            total += points
            biggest = max(biggest, abs(total))
        digits = max(REEL_DIGITS, len(str(int(biggest))))
        cells = digits + (1 if value < 0 else 0)   # a "-" window for a negative score
        reels_width = cells * REEL_CELL[0] + (cells - 1) * REEL_GAP

        # Where everything goes: label and reels side by side, centred.
        left = centre[0] - (label_width + REEL_LABEL_GAP + reels_width) // 2
        shake = TALLY_SHAKE * power if counting else 0.0
        dx = shake * math.sin(self.t * 53)   # two odd speeds: it jitters, it does not swing
        dy = shake * math.cos(self.t * 41)
        label_centre = (left + label_width // 2 + dx, centre[1] + dy)
        self.blit_turned(label_image, label_centre, 0, thump)
        reels = pygame.Rect(left + label_width + REEL_LABEL_GAP + dx,
                            centre[1] - REEL_CELL[1] // 2 + dy, reels_width, REEL_CELL[1])

        self.reel_frame(reels, counting, won_big, power)
        speed = abs(running_value(parts, elapsed + 0.02) - value) / 0.02   # points per second
        for i in range(cells):
            cell = pygame.Rect(reels.x + i * (REEL_CELL[0] + REEL_GAP), reels.y, *REEL_CELL)
            if value < 0 and i == 0:
                self.reel_cell(cell, None, 0.0, 0.0, won_big)   # the minus sign
                continue
            place = cells - 1 - i   # 0 = the units digit (the right-most reel)
            position = abs(value) / 10 ** place
            if not counting:
                # Stopped: every reel clunks onto its whole digit. (While
                # counting they all spin smoothly, the higher ones slower.)
                position = math.floor(position)
            self.reel_cell(cell, position, speed / 10 ** place, power, won_big)

        if since < SPARK_TIME:
            self.sparks(reels.center, since, shown, power)

    def reel_frame(self, reels, counting, won_big, power):
        """
        The gold frame round the reels, with bulbs: they blink slowly while
        waiting, chase round while counting (faster for a bigger score), and
        all flash together for a jackpot.
        """
        outer = reels.inflate(18, 18)
        pygame.draw.rect(self.screen, GOLD_DARK, outer.inflate(6, 6), border_radius=12)
        pygame.draw.rect(self.screen, GOLD, outer, border_radius=10)
        pygame.draw.rect(self.screen, GOLD_LIGHT, outer, 2, border_radius=10)
        step = int(self.t * (8 + 16 * power))   # how fast the chase goes round
        for i, spot in enumerate(self.bulb_spots(reels.inflate(9, 9))):
            if won_big:
                lit = int(self.t * 8) % 2 == 0
            elif counting:
                lit = (i + step) % 3 == 0
            else:
                lit = (i + int(self.t * 2)) % 2 == 0
            pygame.draw.circle(self.screen, NEON_YELLOW if lit else BULB_OFF, spot, 3)

    def reel_cell(self, cell, position, speed, power, won_big):
        """
        One digit's window: a drum with the digits 0-9 rolling past.
        position: the number this reel shows, with its fraction (e.g. 4.3 =
        30 % of the way from 4 to 5), so it rolls smoothly; None = a minus
        sign. speed: digits per second (fast = blurred copies).
        """
        self.darken(255, cell, DRUM_PAPER)
        ink = DRUM_INK
        if won_big and int(self.t * 8) % 2 == 0:
            ink = NEON_RED
        elif power >= 0.5 and speed > REEL_BLUR:
            ink = mix(DRUM_INK, NEON_PINK, power)   # a big score glows while it spins
        self.screen.set_clip(cell)   # draw only inside the window
        if position is None:
            self.blit_turned(self.hud_huge.render("-", True, ink), cell.center)
        else:
            first = math.floor(position)
            offset = position - first   # 0..1, how far the drum has turned past `first`
            for k in (0, 1):
                digit = self.hud_huge.render(str((first + k) % 10), True, ink)
                y = cell.centery + (k - offset) * REEL_CELL[1]
                if speed > REEL_BLUR:
                    # Spinning fast: see-through copies trail behind it.
                    for ghost in (1, 2):
                        copy = digit.copy()
                        copy.set_alpha(80 // ghost)
                        self.blit_turned(copy, (cell.centerx, y + ghost * REEL_CELL[1] * 0.25))
                self.blit_turned(digit, (cell.centerx, y))
        self.screen.set_clip(None)
        self.screen.blit(self.drum_shade(cell.size), cell.topleft)
        pygame.draw.rect(self.screen, GOLD_DARK, cell, 2)

    def sparks(self, centre, since, part, power):
        """
        A burst of sparks from the reels when part number `part` arrives:
        more for a bigger score. Each spark flies out and falls; `since`
        is the time since the part arrived. Always the same burst for the
        same part (a fixed seed), so it does not flicker.
        """
        burst = random.Random(part)
        fade = 1 - since / SPARK_TIME
        for _ in range(4 + int(TALLY_SPARKS * power)):
            angle = burst.uniform(0, 2 * math.pi)
            speed = burst.uniform(*SPARK_SPEED) * (0.6 + power)
            colour = burst.choice(SPARK_COLOURS)
            x = centre[0] + math.cos(angle) * speed * since
            y = centre[1] + math.sin(angle) * speed * since + SPARK_GRAVITY * since ** 2 / 2
            size = max(1, int(4 * fade + 1))
            pygame.draw.circle(self.screen, colour, (int(x), int(y)), size)

    def draw_tally(self, game, elapsed):
        """
        The handed-in exam, counted up like in Balatro, as two tables: the
        questions (left) and the bonuses (right). Each row lights up in its
        colour when its turn comes, its points pop in, and the big score
        counts up and thumps on every part. Returns True when the count is over.
        """
        cx = self.width // 2
        title = "TIME'S UP - PAPER COLLECTED" if game.time_ran_out else "EXAM HANDED IN!"
        self.shout(title, self.hud_huge, NEON_GREEN, (cx, TALLY_TITLE_Y))
        parts = game.score_parts()
        shown = parts_shown(parts, elapsed)
        questions = game.paper.size()
        self.question_table(game, parts, shown, elapsed)
        self.bonus_table(parts[questions:], questions, shown, elapsed)
        self.slot_score("SCORE", parts, elapsed, (cx, TALLY_SCORE_Y))
        return is_done(parts, elapsed)

    def table_frame(self, rect, headers):
        """
        An empty table: the panel, a header row with its titles,
        headers = [(text, x from the left edge, "left" / "center" / "right")].
        Returns the y of the first row's middle.
        """
        self.panel(rect)
        x, y, width, _ = rect
        self.darken(150, (x + 2, y + 2, width - 4, TABLE_HEADER - 2), NEON_PINK)
        for text, column, align in headers:
            self.aligned(text, self.hud_small, NEON_CYAN, x + column, y + TABLE_HEADER // 2, align)
        pygame.draw.line(self.screen, NEON_PINK, (x, y + TABLE_HEADER), (x + width - 1, y + TABLE_HEADER), 2)
        return y + TABLE_HEADER + TABLE_ROW // 2

    def aligned(self, message, font, colour, x, y, align):
        """Text with a shadow, its middle at height y, and its left / middle / right at x."""
        image = font.render(message, True, colour)
        anchor = {"left": "midleft", "center": "center", "right": "midright"}[align]
        rect = image.get_rect(**{anchor: (x, y)})
        self.screen.blit(font.render(message, True, SHADOW), rect.move(2, 2))
        self.screen.blit(image, rect)

    def table_row(self, rect, row_y, colour, since):
        """
        The background of one counted row: it glows in `colour` when its
        turn comes (`since`: seconds since then) and calms down to a faint tint.
        """
        x, _, width, _ = rect
        flash = max(0.0, 1 - since / ROW_FLASH_TIME)
        self.darken(int(35 + 150 * flash), (x + 3, row_y - TABLE_ROW // 2 + 1, width - 6, TABLE_ROW - 2),
                    colour)

    def row_points(self, points, colour, x, row_y, since):
        """A row's points, right-aligned at x; they pop in bigger and settle."""
        # Plain text with a shadow: the neon ghosts make small numbers hard to read.
        label = f"{points:+d}" if points else "0"
        front = self.hud.render(label, True, colour)
        image = pygame.Surface((front.get_width() + 2, front.get_height() + 2), pygame.SRCALPHA)
        image.blit(self.hud.render(label, True, SHADOW), (2, 2))
        image.blit(front, (0, 0))
        pop = 1 + ROW_POP * max(0.0, 1 - since / ROW_FLASH_TIME)
        if pop != 1:
            image = pygame.transform.rotozoom(image, 0, pop)
        self.screen.blit(image, image.get_rect(midright=(x, row_y)))

    def question_table(self, game, parts, shown, elapsed):
        """
        One row per question: Q1, what you wrote, the answer key, right /
        wrong / blank, the points. The key and the result stay hidden until
        the row's turn; the last row is the grade, once all are counted.
        """
        rect = QUESTION_TABLE
        x = rect[0]
        c = QUESTION_COLUMNS
        row_y = self.table_frame(rect, [("Q", c["Q"], "center"), ("YOU", c["YOU"], "center"),
                                        ("KEY", c["KEY"], "center"), ("RESULT", c["RESULT"], "center"),
                                        ("POINTS", c["POINTS"], "right")])
        results = game.paper.results()
        for i, written in enumerate(game.paper.written):
            y = row_y + i * TABLE_ROW
            counted = i < shown
            colour = RESULT_COLOURS[results[i]] if counted else GREY
            if counted:
                self.table_row(rect, y, colour, elapsed - appear_time(i))
            self.aligned(f"Q{i + 1}", self.hud_small, WHITE, x + c["Q"], y, "center")
            self.aligned(written, self.hud, WHITE if counted else GREY, x + c["YOU"], y, "center")
            if not counted:
                self.aligned("?", self.hud, GREY, x + c["KEY"], y, "center")
                continue
            self.aligned(game.paper.right_letters[i], self.hud, NEON_YELLOW, x + c["KEY"], y, "center")
            self.aligned(RESULT_NAMES[results[i]], self.hud_small, colour, x + c["RESULT"], y, "center")
            self.row_points(parts[i][1], colour, x + c["POINTS"], y, elapsed - appear_time(i))

        # The grade, under the questions, once every question is counted.
        if shown >= len(results):
            y = row_y + len(results) * TABLE_ROW + 6
            pygame.draw.line(self.screen, NEON_PINK, (x + 10, y - TABLE_ROW // 2),
                             (x + rect[2] - 10, y - TABLE_ROW // 2), 1)
            counts = (f"{game.paper.count(CORRECT)} right  {game.paper.count(WRONG)} wrong  "
                      f"{game.paper.count(EMPTY)} blank")
            self.aligned(f"GRADE  {game.paper.points():g} / {len(results)}", self.hud_small, WHITE,
                         x + 14, y, "left")
            self.aligned(counts, self.small, WHITE, x + c["POINTS"], y, "right")

    def bonus_table(self, bonuses, first, shown, elapsed):
        """
        The bonuses (and the points taken off) one row each, as their turn
        comes. `first`: the part number of the first bonus (after the questions).
        """
        rect = BONUS_TABLE
        x, _, width, _ = rect
        row_y = self.table_frame(rect, [("BONUS", 16, "left"), ("POINTS", width - 20, "right")])
        if not bonuses:
            self.aligned("No bonuses this time", self.small, GREY, x + width // 2, row_y, "center")
        for j, (name, points) in enumerate(bonuses):
            if first + j >= shown:
                break
            y = row_y + j * TABLE_ROW
            since = elapsed - appear_time(first + j)
            colour = NEON_CYAN if points >= 0 else NEON_RED
            self.table_row(rect, y, colour, since)
            self.aligned(name, self.hud_small, WHITE, x + 16, y, "left")
            self.row_points(points, colour, x + width - 20, y, since)

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

        # A little left of the box's middle: five reels and "JACKPOT!" must
        # stay clear of the top scores box on the right.
        self.slot_score("TOTAL", parts, elapsed, (x + width // 2 - RUN_TOTAL_SHIFT, RUN_TOTAL_Y),
                        exams=len(QUIZZES))

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
