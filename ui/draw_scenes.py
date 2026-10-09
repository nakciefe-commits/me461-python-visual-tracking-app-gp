"""
Drawing the scenes: short moments where the game is frozen (game.py says
which one plays and for how long).
    warning    the teacher walks up to your desk and points at you
    caught     a Metal Gear "!", then the teacher tears up your exam
    mugshot    your taped-up exam with your photo (in draw_mugshot.py)
    game over  the Gemini and Claude logos, with faces, make fun of you
And the grade roast after the final (draw_verdict()): the same two logos
comment on your semester grade, over the results screen.
Part of Renderer (see render.py).
"""

import math
import random

import pygame

from logic.game import WARNING_SCENE, CAUGHT_SCENE, GAME_OVER_SCENE, MUGSHOT_SCENE
from settings import (MAX_WARNINGS, WARNING_SCENE_TIME, TEACHER_APPROACH_TIME, CAUGHT_SCENE_TIME,
                      CAUGHT_EXCLAIM_TIME, GAME_OVER_TIME, VERDICT_FADE)
from ui.style import BLACK, WHITE, NEON_RED, NEON_YELLOW, NEON_PINK, NEON_CYAN, NEON_GREEN, mix, menu_font
from logic.teacher import BOARD, DESK

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
CAUGHT_TEXTS = ("CAUGHT COPYING!", "\"SO... YOU'RE CHEATING, HUH?\"")
# What the teacher yells in the warning scene: one line per warning, in order
# (the last one is the warning that ends the game).
WARNING_LINES = [
    "\"DO NOT STARE AT ME! LOOK AT YOUR DAMN PAPER!\"",
    "\"YOU WANNA FAIL, YOU LITTLE RACCOON?\"",
    "\"IT IS OVER FOR YOU, YOU CHEATING NOODLE!\"",
]

# The game over screen: two logos with faces make fun of you, one line
# each, typed out like a chat app. Several conversations per way of failing;
# main.py picks one with a Bag (logic/bag.py), so the same joke does not
# come back until all the others have been told. Each line is (who, text);
# "{exam}" becomes the exam's name. Keep a line under ~75 letters (two
# lines in the bubble). When both lines are typed, both logos laugh.
GEMINI, CLAUDE = "GEMINI", "CLAUDE"   # Gemini drew the pictures, Claude wrote the code
GAME_OVER_CHAT = {
    "caught": [
        [(GEMINI, "Copying from your neighbour? With HIM watching? Bold move."),
         (CLAUDE, "Maybe next semester you can study instead of copying.")],
        [(CLAUDE, "You turned your head like a lighthouse. Very subtle."),
         (GEMINI, "Even your neighbour noticed. And she was half asleep.")],
        [(GEMINI, "I drew that teacher. I gave him eyes for a reason."),
         (CLAUDE, "And I wrote the alarm. You heard it. You stayed.")],
        [(GEMINI, "He tore up your exam so fast, it was almost art."),
         (CLAUDE, "Honestly, the tear was the best thing on that paper.")],
        [(CLAUDE, "Fun fact: the \"hmm\" means LOOK AWAY."),
         (GEMINI, "Less fun fact: you just found that out.")],
        [(GEMINI, "{exam}: zero points. Impressive, in a way."),
         (CLAUDE, "Your neighbour should charge you rent for that look.")],
        [(CLAUDE, "You had one job. It is literally the name of the game."),
         (GEMINI, "Maybe the sequel should be called \"Got Caught\".")],
    ],
    "warnings": [
        [(CLAUDE, "Man, you stared at the teacher like it was a Netflix show."),
         (GEMINI, "Maybe try looking at the teacher during class, not during the quiz.")],
        [(GEMINI, "Three warnings. He walked over to you THREE times."),
         (CLAUDE, "That is more cardio than he did all semester.")],
        [(CLAUDE, "A staring contest with the teacher. You lost. Three times."),
         (GEMINI, "He didn't even blink. I know. I drew him.")],
        [(GEMINI, "Your paper was RIGHT THERE. Just look down."),
         (CLAUDE, "Down. Like your grade point average.")],
        [(CLAUDE, "Were you trying to copy from HIM?"),
         (GEMINI, "To be fair, he does have the answer key.")],
        [(GEMINI, "\"Do not stare at me,\" he said. Three times."),
         (CLAUDE, "Some people just really want attention.")],
        [(CLAUDE, "{exam} is over. Reason: too much eye contact."),
         (GEMINI, "We should put that on your transcript.")],
        [(GEMINI, "You looked at him more than at your exam."),
         (CLAUDE, "Is this a crush? Should we give you two some privacy?")],
    ],
}
CHAT_START = 1.2               # seconds of "GAME OVER" alone before the chat starts
CHAT_LINE_TIME = 2.6           # seconds between the two chat lines
CHAT_TYPE_SPEED = 40           # letters per second the lines are typed
CHAT_BLIP_LETTERS = 2          # letters per talking blip while a line is typed (1 = a blip per letter)
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
VERDICT_DARKEN = 225           # 0-255, how dark the results screen gets behind the grade roast
# The show for a good grade (hype 1 = BB, 2 = BA, 3 = AA; see logic/verdict.py).
HYPE_TITLES = {1: "RESPECTABLE.", 2: "CERTIFIED SNEAKY", 3: "LEGENDARY CHEATER"}   # under the big letter
HYPE_CONFETTI = {1: 25, 2: 60, 3: 140}     # pieces of confetti
LETTER_SHOW_Y = 270            # pixels, the middle of the big letter during the show
LETTER_TOP_Y = 66              # pixels, where it goes when the chat starts
LETTER_SCALE = {1: 2.2, 2: 2.8, 3: 3.6}    # how big the letter is during the show (x the big font)
LETTER_SLAM_TIME = 0.3         # seconds the letter takes to slam down from huge
LETTER_SLAM_FROM = 3.0         # it starts this many times bigger
LETTER_RISE_TIME = 0.4         # seconds it takes to go up when the chat starts
HYPE_TITLE_GAP = 125           # pixels from the big letter's middle down to its title (during the show)
GOLD = (255, 200, 40)          # the AA's letters
RAYS = 14                      # light rays behind the big letter (BA and AA)
RAY_SPEED = 25                 # degrees per second they turn
RAY_LENGTH = 700               # pixels
FLASH_TIME_AA = 0.5            # seconds of the white flash when an AA lands
SHAKE_AA = 22                  # pixels the screen shakes when an AA lands ...
SHAKE_FIREWORK = 6             # ... and on each firework during the show
FIREWORK_TIME = 1.4            # seconds a firework's sparks fly
FIREWORK_SPARKS = 70           # sparks in one firework
FIREWORK_SPEED = (200, 520)    # pixels per second, slowest and fastest spark
FIREWORK_TRAIL = 0.09          # seconds of flight each spark's trail shows
FIREWORK_GRAVITY = 180         # pixels per second², the sparks fall
FIREWORK_COLOURS = [GOLD, NEON_PINK, NEON_CYAN, NEON_GREEN, NEON_YELLOW, WHITE]
END_TEXTS = {   # lose_reason -> big text on the end screen
    "caught": "CAUGHT COPYING!",
    "warnings": "TOO MANY WARNINGS",
}


def typed_letters(chat, elapsed):
    """
    For each chat line, how many of its letters are typed `elapsed` seconds
    after the chat started (0 = not started yet, len(text) = all typed).
    main.py uses it for the talking blips.
    """
    return [max(0, min(len(text), int((elapsed - CHAT_START - i * CHAT_LINE_TIME) * CHAT_TYPE_SPEED)))
            for i, (who, text) in enumerate(chat)]


class SceneDrawing:
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
        watching = self.picture(f"classroom_{teacher.place.lower()}_watching")
        zoom = 1 + (APPROACH_ZOOM - 1) * walk * walk
        self.screen.fill(BLACK)
        self.screen.blit(self.zoomed(watching, TEACHER_FACE[teacher.place], zoom), offset)

        if arrived < 0:
            return
        # Arrived: the pointing picture, at once. The white flash below hides
        # the cut from the zoomed picture.
        if POINTING_IMAGE in self.classroom:
            self.screen.blit(self.picture(POINTING_IMAGE), offset)
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

    def draw_scene(self, game, teacher, chat):
        """Whichever scene game.scene says is playing."""
        if game.scene == WARNING_SCENE:
            self.draw_warning_scene(game, teacher)
        elif game.scene == CAUGHT_SCENE:
            self.draw_caught_scene(game, teacher)
        elif game.scene == MUGSHOT_SCENE:
            self.draw_mugshot(game)            # see draw_mugshot.py
        elif game.scene == GAME_OVER_SCENE:
            self.draw_game_over(game, chat)
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
            self.screen.blit(self.picture(CAUGHT_IMAGE), self.scene_shake(since_cut))
        else:
            # The moment you are seen: the teacher, and the "!" popping up big.
            self.screen.blit(self.picture(f"classroom_{teacher.place.lower()}_watching"), (0, 0))
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

    def draw_game_over(self, game, chat):
        """
        The game over scene: black, "GAME OVER" in big letters, then the
        Gemini and Claude logos chat about how you lost (`chat`: one of
        GAME_OVER_CHAT, picked by main.py). When it ends, draw_end() keeps
        this screen and adds the menu under it.
        """
        self.chat_screen(chat, GAME_OVER_TIME - game.scene_time, END_TEXTS[game.lose_reason])
        self.footer("Space = skip")

    def chat_screen(self, chat, elapsed, subtitle):
        """
        "GAME OVER", a line of text under it, and the chat (a list of
        (who, text)) as it is `elapsed` seconds after it started (long
        after = all typed, both laughing).
        """
        cx = self.width // 2
        self.screen.fill(BLACK)
        self.shout("GAME OVER", self.menu_title_font, NEON_RED, (cx, 62))
        # Plain (narrower) font, so it stays clear of the logos at the sides.
        self.shadow_text(subtitle, self.medium, WHITE, (cx, 116), center=True)
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

    def draw_verdict(self, verdict):
        """
        The grade roast (logic/verdict.py) over the results screen: it
        darkens, and Gemini and Claude's lines are typed out in the same
        bubbles as the game over chat. A good grade first gets a show (its
        hype): the letter slams down big in the middle, with confetti (BB),
        light rays (BA), and for an AA a flash, a shake and fireworks; then
        it goes up to the top and the chat starts.
        """
        t, hype = verdict.time, verdict.hype
        self.darken(int(VERDICT_DARKEN * min(1.0, t / VERDICT_FADE)))
        if hype:
            self.hype_show(verdict)
        else:
            cx = self.width // 2
            self.shout("THE VERDICT", self.menu_title_font, NEON_YELLOW, (cx, 62))
            self.shadow_text(f"SEMESTER GRADE: {verdict.letter}", self.medium, WHITE, (cx, 116), center=True)
        for i, ((who, message), letters) in enumerate(zip(verdict.lines, verdict.letters())):
            if letters == 0:
                break   # not said yet
            self.chat_line(who, message, letters, CHAT_TOP + i * CHAT_ROW, verdict.laughing())
        self.footer("Space = skip")
        if hype >= 3:
            self.aa_flash_and_shake(verdict)

    def hype_show(self, verdict):
        """The big letter with its effects, more the higher the hype."""
        t, hype = verdict.time, verdict.hype
        cx = self.width // 2
        # Where the letter is: in the middle during the show, then it rises to the top.
        rise = min(1.0, max(0.0, (t - verdict.reveal) / LETTER_RISE_TIME))
        rise = rise * rise * (3 - 2 * rise)   # smoothstep: starts and stops gently
        y = LETTER_SHOW_Y + (LETTER_TOP_Y - LETTER_SHOW_Y) * rise
        scale = LETTER_SCALE[hype] + (1 - LETTER_SCALE[hype]) * rise
        # The slam: it starts huge and lands, like a stamp.
        slam = min(1.0, t / LETTER_SLAM_TIME)
        scale *= 1 + (LETTER_SLAM_FROM - 1) * (1 - slam) ** 2
        if hype >= 2:
            self.light_rays((cx, y), t, hype, 1 - 0.6 * rise)
        if hype >= 3:
            for i, start in enumerate(verdict.firework_times()):
                if 0 <= t - start < FIREWORK_TIME:
                    self.firework_burst(i, t - start)
        self.confetti(t, HYPE_CONFETTI[hype])
        colour = self.hype_colour(hype, t)
        angle = 4 * math.sin(t * 5) * (1 - rise) if hype >= 3 else 0
        pulse = 1 + 0.06 * math.sin(t * 10) * (1 - rise) if hype >= 2 else 1
        self.blit_turned(self.neon_text(verdict.letter, self.hud_huge, colour, glow=True),
                         (cx, int(y)), angle, scale * pulse)
        # Its title under it, while it is in the middle.
        if slam >= 1 and rise < 1:
            title = self.neon_text(HYPE_TITLES[hype], self.hud_big, WHITE if hype < 3 else GOLD)
            title.set_alpha(int(255 * (1 - rise)))
            self.blit_turned(title, (cx, int(y + HYPE_TITLE_GAP * (1 - rise))))

    @staticmethod
    def hype_colour(hype, t):
        """The big letter's colour: yellow (BB), pink to yellow (BA), gold flashing rainbow (AA)."""
        if hype == 1:
            return NEON_YELLOW
        if hype == 2:
            return mix(NEON_PINK, NEON_YELLOW, 0.5 + 0.5 * math.sin(t * 4))
        return mix(GOLD, WHITE, 0.5 + 0.5 * math.sin(t * 9))   # shimmering gold

    def light_rays(self, centre, t, hype, strength):
        """Rays of light turning slowly behind the big letter (stage lights)."""
        layer = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        colour = GOLD if hype >= 3 else NEON_PINK
        for k in range(RAYS):
            angle = math.radians(k * 360 / RAYS + t * RAY_SPEED)
            spread = math.radians(360 / RAYS / 4)   # each ray is a quarter of its slice
            tip_a = (centre[0] + RAY_LENGTH * math.cos(angle - spread), centre[1] + RAY_LENGTH * math.sin(angle - spread))
            tip_b = (centre[0] + RAY_LENGTH * math.cos(angle + spread), centre[1] + RAY_LENGTH * math.sin(angle + spread))
            pygame.draw.polygon(layer, (*colour, int(70 * strength)), [centre, tip_a, tip_b])
        self.screen.blit(layer, (0, 0))

    def firework_burst(self, number, since):
        """
        Firework number `number`, `since` seconds after it went off: a ring of
        sparks flying out and falling, fading. Where it is and its colour
        come from a fixed seed, so it does not flicker.
        """
        burst = random.Random(number * 31 + 1)
        centre = (burst.uniform(0.12, 0.88) * self.width, burst.uniform(0.12, 0.55) * self.height)
        colour = burst.choice(FIREWORK_COLOURS)
        fade = 1 - since / FIREWORK_TIME
        if since < 0.12:   # the flash of the bang in the middle
            pygame.draw.circle(self.screen, mix(colour, WHITE, 0.5), (int(centre[0]), int(centre[1])),
                               int(26 * (1 - since / 0.12)) + 3)
        for _ in range(FIREWORK_SPARKS):
            angle = burst.uniform(0, 2 * math.pi)
            speed = burst.uniform(*FIREWORK_SPEED)
            # A trail: from where the spark was a moment ago to where it is now.
            tail, head = (self.spark_at(centre, angle, speed, max(0.0, since - FIREWORK_TRAIL)),
                          self.spark_at(centre, angle, speed, since))
            spark = mix(BLACK, mix(colour, WHITE, 0.3 * fade), max(0.0, fade))
            pygame.draw.line(self.screen, spark, tail, head, max(1, int(3 * fade + 1)))
            pygame.draw.circle(self.screen, mix(spark, WHITE, 0.5), head, max(1, int(2 * fade + 1)))

    @staticmethod
    def spark_at(centre, angle, speed, since):
        """Where a firework's spark is `since` seconds after the bang (air slows it down, gravity pulls it)."""
        flown = (1 - math.exp(-2.5 * since)) / 2.5
        return (int(centre[0] + math.cos(angle) * speed * flown),
                int(centre[1] + math.sin(angle) * speed * flown + FIREWORK_GRAVITY * since ** 2 / 2))

    def aa_flash_and_shake(self, verdict):
        """An AA lands: a white flash, and the whole screen shakes (a little again on each firework)."""
        t = verdict.time
        flash = max(0.0, 1 - t / FLASH_TIME_AA)
        if flash > 0:
            self.darken(int(255 * flash ** 2), colour=WHITE)
        shake = SHAKE_AA * max(0.0, 1 - t / 0.8)
        for start in verdict.firework_times():
            if start < verdict.reveal and 0 <= t - start < 0.2:
                shake = max(shake, SHAKE_FIREWORK * (1 - (t - start) / 0.2))
        if shake >= 1:
            picture = self.screen.copy()
            self.screen.fill(BLACK)
            self.screen.blit(picture, (random.uniform(-shake, shake), random.uniform(-shake, shake)))
