"""
The game: menus, a run of three exams (the classroom, the teacher, the
suspicion bar), the score count after each exam and the run's results.

Run it with:   ./run.sh      (or  .venv/bin/python main.py)
Keys:          Space = calibrate (start screen), q = quit, F11 = fullscreen on/off,
               menus: arrows / Enter / Esc (or the head: tilt up/down, turn right = select,
                      turn left = back), or the mouse,
               in the game: a / b / c / d = write that answer, s = leave it blank
                      (both while looking at your paper),
                      r = restart the run, m = main menu, k = recalibrate, Esc = quit,
                      t = always show the classroom and the teacher's state (for testing),
                      Space = skip the scenes after losing, and the score count

The program is one loop that repeats about 30 times a second:
    1. handle key presses and clicks
    2. take the newest webcam frame and find the head direction
    3. move the menu, or the teacher and the game rules, forward
    4. play sounds for what happened, draw the screen
"""

import os
import random
import time

import pygame

from ui import glitch_intro
from tracking.camera import Camera
from logic.disclaimer import Disclaimer
from logic.bag import Bag
from logic.highscore import load_top, add_score, save_top
from logic.game import Game, PLAYING
from logic.run import Run
from logic.slot import reel_position, has_stopped, passed
from tracking.head_tracker import HeadTracker, Calibration, DOWN, SCREEN, LEFT, RIGHT
from logic.menu import (Menu, HeadMenuInput, loading_steps, loading_progress,
                  UP, DOWN as MENU_DOWN, SELECT, BACK)
from ui.draw_menus import BIG_PREVIEW_SIZE, MENU_PREVIEW_SIZE, HELP_LINES
from ui.draw_scenes import GAME_OVER_CHAT
from ui.draw_notice import DISCLAIMER_LETTERS
from ui.render import Renderer, camera_to_surface
from settings import (CAMERA_INDEX, CALIBRATION_TIME, WINDOW_WIDTH, WINDOW_HEIGHT, FPS, FADE_TIME,
                      FULLSCREEN, MAXIMIZED, LOADING_TIME, SMOOTH_SCALING, SCREEN_FADE_TIME,
                      HIGH_SCORE_FILE)
from ui.sounds import Sounds, tally_sound
from logic.tally import parts_shown, is_done
from logic.teacher import Teacher

MAX_DT = 0.1   # seconds; a slow frame must not fill a whole bar at once
# The top scores file sits next to this file, wherever the game is started from.
HIGH_SCORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), HIGH_SCORE_FILE)
# Answer keys -> the letter they write on your paper.
LETTER_KEYS = {pygame.K_a: "A", pygame.K_b: "B", pygame.K_c: "C", pygame.K_d: "D"}
BLANK_KEY = pygame.K_s   # leave the current question blank
# Menu keys -> the same actions the head gives (see menu.py).
MENU_KEYS = {pygame.K_UP: UP, pygame.K_DOWN: MENU_DOWN,
             pygame.K_RETURN: SELECT, pygame.K_KP_ENTER: SELECT, pygame.K_SPACE: SELECT,
             pygame.K_RIGHT: SELECT, pygame.K_LEFT: BACK, pygame.K_BACKSPACE: BACK}

# The screens. "Face not found" is not a screen of its own: it is the GAME
# screen with the game paused. DISCLAIMER is shown once, when the game opens.
# Before each exam: BRIEFING (the hallway gossip: what happened to the
# teacher; "I'm ready" goes on), then LOADING (a short "get ready" screen).
# END is the score count (or game over) after each exam, RUN_END the results
# of the whole run (three exams) and the top scores.
DISCLAIMER, START, CALIBRATING, MENU, HELP, SETTINGS, BRIEFING, LOADING, GAME, END, RUN_END = (
    "DISCLAIMER", "START", "CALIBRATING", "MENU", "HELP", "SETTINGS", "BRIEFING", "LOADING",
    "GAME", "END", "RUN_END")
# Screens with a list of items to choose from.
MENU_SCREENS = (MENU, HELP, SETTINGS, BRIEFING, END, RUN_END)
# Screens without music: it fades out while loading, so the exam is quiet.
SILENT_SCREENS = (DISCLAIMER, LOADING, GAME)
TITLES = {MENU: "DON'T GET CAUGHT", HELP: "HOW TO PLAY", SETTINGS: "SETTINGS"}

# Colour of the face drawing for each direction, (Blue, Green, Red) for OpenCV.
FACE_COLOURS = {DOWN: (240, 150, 80), SCREEN: (60, 200, 240),
                LEFT: (110, 200, 70), RIGHT: (110, 200, 70)}
WHITE_BGR = (240, 240, 240)


def open_window(fullscreen):
    """
    Open (or reopen) the window and return the surface to draw on.
    SCALED: we always draw on a WINDOW_WIDTH x WINDOW_HEIGHT surface and
    pygame stretches it to the real window (with black bars so nothing is
    squashed) and converts mouse clicks back.
    Not fullscreen: a normal window with a title bar. RESIZABLE lets the
    player drag its edges, and with MAXIMIZED it starts filling the screen.
    Fullscreen: a borderless window the size of the desktop (the monitor's
    resolution is not changed).
    """
    if fullscreen:
        return pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT),
                                       pygame.SCALED | pygame.FULLSCREEN)
    surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT),
                                      pygame.SCALED | pygame.RESIZABLE)
    if MAXIMIZED:
        pygame.Window.from_display_module().maximize()
    return surface


def classroom_view(direction, look_time, show_always):
    """
    How visible the classroom is: 0 = black, 1 = fully shown. It is black
    while looking away, and fades in over FADE_TIME after looking at the
    screen (like eyes refocusing).
    """
    if show_always:
        return 1.0
    if direction != SCREEN:
        return 0.0
    return min(1.0, look_time / FADE_TIME)


class App:
    """Everything the running program needs, and one method per job."""

    def __init__(self):
        if SMOOTH_SCALING:
            # Tell SDL (under pygame) to stretch the picture to the window with
            # smoothing instead of copying pixels; must be set before the window opens.
            os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "linear")
        pygame.init()
        self.fullscreen = FULLSCREEN
        screen = open_window(self.fullscreen)
        pygame.display.set_caption("Don't Get Caught")
        self.renderer = Renderer(screen)
        self.sounds = Sounds()
        self.clock = pygame.time.Clock()

        self.camera = Camera(CAMERA_INDEX)
        self.tracker = HeadTracker()
        self.calibration = Calibration(self.tracker, CALIBRATION_TIME)
        self.game = Game()
        self.teacher = Teacher()
        self.menus = {
            MENU: Menu(["PLAY", "HOW TO PLAY", "SETTINGS", "QUIT"]),
            HELP: Menu(["BACK"]),
            SETTINGS: Menu(["SOUND", "FULLSCREEN", "RECALIBRATE", "BACK"]),
            BRIEFING: Menu(["SPIN"]),   # then "I'M READY", see start_spin()
            END: Menu(["NEXT EXAM", "MAIN MENU"]),   # changed after each exam, see go_to()
            RUN_END: Menu(["PLAY AGAIN", "MAIN MENU", "QUIT"]),
        }
        self.head_input = HeadMenuInput()

        self.notice = Disclaimer(DISCLAIMER_LETTERS)   # the disclaimer screen's state
        # The three exams being played (a new one on PLAY). Not called
        # "self.run": that would hide the main loop, App.run().
        self.current_run = Run()
        self.top = load_top(HIGH_SCORE_PATH)    # the best runs so far, best first
        self.new_place = None                   # where the last run got in the top scores (0 = first), or None
        self.screen_name = DISCLAIMER
        self.after_calibration = MENU   # where calibrating leads to
        self.direction = SCREEN   # last known direction, kept while paused
        self.look_time = 0.0      # seconds the player has been looking at the screen in one go
        self.show_always = False  # t key: always show the classroom (for testing)
        self.loading_time = 0.0   # seconds the loading screen has been shown
        self.loading_plan = []    # when the loading bar jumps (see menu.loading_steps())
        self.end_time = 0.0       # seconds the END / RUN_END screen has been shown (the score count uses it)
        self.start_time = time.time()
        # The game over chat: a Bag per way of failing, so the same joke does
        # not come back until all the others were told (see logic/bag.py).
        self.chat_bags = {reason: Bag(range(len(chats))) for reason, chats in GAME_OVER_CHAT.items()}
        self.chat = []            # the conversation of the last failed exam
        self.spin_time = None     # seconds since the gossip slot machine started; None = not yet
        # Changing screens: the last picture of the old screen is laid over the
        # new one and fades out over SCREEN_FADE_TIME (a "crossfade").
        self.fade_picture = None
        self.fade_time = 0.0
        self.running = True

    # ------------------------------------------------------------------
    # Moving between screens
    # ------------------------------------------------------------------
    def go_to(self, name):
        # Keep what is on the screen now, to fade it out over the new screen.
        self.fade_picture = self.renderer.screen.copy()
        self.fade_time = 0.0
        self.screen_name = name
        if name in MENU_SCREENS:
            # The head may still be turned from before: wait until it is straight.
            self.head_input.reset()
        if name == END:
            # One exam is over: keep its result; the menu leads on.
            self.current_run.finish_quiz(self.game)
            items = ["SEE RESULTS"] if self.current_run.is_over() else ["NEXT EXAM", "MAIN MENU"]
            self.menus[END] = Menu(items)
            self.end_time = 0.0
        if name == RUN_END:
            self.menus[RUN_END].selected = 0   # "PLAY AGAIN"
            self.end_time = 0.0
            self.record_run()

    def record_run(self):
        """The run is over: put its total into the top scores, and save them if it got in."""
        date = time.strftime("%d %b").lstrip("0").upper()   # e.g. "7 OCT"
        self.top, self.new_place = add_score(self.top, self.current_run.total(), date)
        if self.new_place is not None:
            save_top(HIGH_SCORE_PATH, self.top)

    def calibrate_then(self, next_screen):
        """Calibrate, then go to next_screen."""
        self.calibration.restart()
        self.after_calibration = next_screen
        self.go_to(CALIBRATING)

    def start_run(self):
        """A new run: three new exams with new moods, starting with the first."""
        self.current_run = Run()
        self.start_exam()

    def start_exam(self):
        """The run's next exam: first the hallway gossip, then (when ready) the loading screen."""
        self.spin_time = None
        self.menus[BRIEFING] = Menu(["SPIN"])
        self.go_to(BRIEFING)

    def spinning(self):
        """True while the gossip slot machine is turning (no menu then)."""
        return self.spin_time is not None and not has_stopped(self.spin_time)

    def reel(self):
        """Where the slot machine's reel is (logic/slot.py), or None before the spin."""
        if self.spin_time is None:
            return None
        run = self.current_run
        return reel_position(run.chosen(), len(run.pool()), self.spin_time)

    def turn_reel(self, dt):
        """Move the slot machine on: a tick per mood passing, a ding and "I'm ready" when it stops."""
        if not self.spinning():
            return
        before = self.reel()
        self.spin_time += dt
        for _ in range(passed(before, self.reel())):
            self.sounds.play("slot_tick")
        if has_stopped(self.spin_time):
            self.sounds.play("slot_stop")
            self.menus[BRIEFING] = Menu(["I'M READY"])

    def start_loading(self):
        """The short loading screen before the exam (see loading_screen())."""
        self.loading_time = 0.0
        self.loading_plan = loading_steps(random.Random())   # a new uneven fill each time
        self.go_to(LOADING)

    def begin_playing(self):
        """The loading screen is over: a fresh exam, today's teacher, start the clock."""
        self.game = self.current_run.new_game()
        self.teacher.set_mood(self.current_run.mood())
        self.teacher.reset()
        self.direction = SCREEN
        self.look_time = 0.0
        self.go_to(GAME)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        open_window(self.fullscreen)   # same surface size, so the renderer keeps working

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------
    def menu_labels(self):
        """The text of each item on the current menu. Settings show their values."""
        if self.screen_name != SETTINGS:
            return self.menus[self.screen_name].items
        on_off = {True: "ON", False: "OFF"}
        return [f"SOUND   {on_off[not self.sounds.muted]}",
                f"FULLSCREEN   {on_off[self.fullscreen]}",
                "RECALIBRATE",
                "BACK"]

    def menu_action(self, action):
        """UP, DOWN, SELECT or BACK, from the head, the keys or the mouse."""
        menu = self.menus[self.screen_name]
        if self.screen_name == BRIEFING and self.spinning():
            return   # nothing to choose while the slot machine turns
        if action in (UP, MENU_DOWN):
            menu.move(-1 if action == UP else 1)
            self.sounds.play("menu_move")
        elif action == BACK:
            if self.screen_name != MENU:   # the main menu has nothing to go back to
                self.sounds.play("menu_back")
                self.go_to(MENU)
        else:
            self.sounds.play("menu_select")
            self.choose(menu.current())

    def choose(self, item):
        """Do what the selected menu item says."""
        if item in ("PLAY", "PLAY AGAIN"):
            self.start_run()
        elif item == "NEXT EXAM":
            self.start_exam()
        elif item == "SPIN":
            self.spin_time = 0.0
        elif item == "I'M READY":
            self.start_loading()
        elif item == "SEE RESULTS":
            self.go_to(RUN_END)
        elif item == "HOW TO PLAY":
            self.go_to(HELP)
        elif item == "SETTINGS":
            self.go_to(SETTINGS)
        elif item in ("MAIN MENU", "BACK"):
            self.go_to(MENU)
        elif item == "QUIT":
            self.running = False
        elif item == "SOUND":
            self.sounds.muted = not self.sounds.muted
        elif item == "FULLSCREEN":
            self.toggle_fullscreen()
        elif item == "RECALIBRATE":
            self.calibrate_then(SETTINGS)

    # ------------------------------------------------------------------
    # 1. Keys, clicks and the window's X button
    # ------------------------------------------------------------------
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.screen_name in MENU_SCREENS:
                    self.head_input.pause()   # keys in charge: the head waits a moment
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEMOTION and self.screen_name in MENU_SCREENS:
                # Pointing at an item selects it, like moving with the arrows.
                menu = self.menus[self.screen_name]
                for i, rect in enumerate(self.renderer.menu_rects):
                    if rect.collidepoint(event.pos) and menu.selected != i:
                        menu.selected = i
                        self.sounds.play("menu_move")
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.screen_name in MENU_SCREENS:
                    self.head_input.pause()   # the mouse in charge: the head waits a moment
                self.handle_click(event.pos)

    def handle_key(self, key):
        name = self.screen_name
        if key == pygame.K_q:
            self.running = False
        elif key == pygame.K_F11:
            self.toggle_fullscreen()
        elif key == pygame.K_t:
            self.show_always = not self.show_always
        elif name == DISCLAIMER:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.press_notice()
        elif name == START:
            if key == pygame.K_SPACE:
                self.sounds.play("menu_select")
                self.calibrate_then(MENU)
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif name in MENU_SCREENS:
            if key == pygame.K_ESCAPE:
                # Esc goes back; on the main menu (nowhere to go back to) it quits.
                if name == MENU:
                    self.running = False
                else:
                    self.menu_action(BACK)
            elif (name in (END, RUN_END) and key in (pygame.K_SPACE, pygame.K_RETURN)
                  and not self.count_done()):
                self.end_time = 1e9                  # skip the score count to its end
            elif name in (END, RUN_END) and key == pygame.K_r:
                self.start_run()
            elif name in (END, RUN_END) and key == pygame.K_m:
                self.go_to(MENU)
            elif key in MENU_KEYS:
                self.menu_action(MENU_KEYS[key])
        elif name == GAME:
            if key == pygame.K_ESCAPE:
                self.running = False
            elif key in (pygame.K_SPACE, pygame.K_RETURN):
                self.game.skip_scene()               # only works after losing
            elif key == pygame.K_k:                  # recalibrate, keep the game
                self.calibrate_then(GAME)
            elif key == pygame.K_r:                  # a new run
                self.start_run()
            elif key == pygame.K_m:                  # give up, back to the main menu
                self.go_to(MENU)
            elif key in LETTER_KEYS or key == BLANK_KEY:
                # Only works while looking at your paper; any letter goes,
                # read or not (a guess). game.write() checks it.
                if key == BLANK_KEY:
                    events = self.game.leave_blank(self.direction)
                else:
                    events = self.game.write(LETTER_KEYS[key], self.direction)
                for sound in events:
                    self.sounds.play(sound)
        elif key == pygame.K_ESCAPE:
            self.running = False

    def press_notice(self):
        """Space on the disclaimer: read faster, sign, or go on after the stamp."""
        for sound in self.notice.press():
            self.sounds.play(sound)

    def handle_click(self, pos):
        name = self.screen_name
        if name == DISCLAIMER:
            self.press_notice()                      # a click anywhere does what Space does
        elif name == START and self.renderer.button_rect.collidepoint(pos):
            self.sounds.play("menu_select")
            self.calibrate_then(MENU)
        elif name == GAME:
            self.game.skip_scene()                   # only works after losing
        elif name in MENU_SCREENS:
            for i, rect in enumerate(self.renderer.menu_rects):
                if rect.collidepoint(pos):
                    self.menus[name].selected = i
                    self.menu_action(SELECT)
                    break

    # ------------------------------------------------------------------
    # 3 + 4. Rules, sounds and drawing for each screen
    # ------------------------------------------------------------------
    def start_screen(self, frame, now, dt):
        """START and CALIBRATING: a big webcam preview and the Calibrate button."""
        self.tracker.draw_face(frame, WHITE_BGR)
        camera_surface = camera_to_surface(frame, BIG_PREVIEW_SIZE)
        face_visible = self.tracker.face_visible(now)
        if self.screen_name == START:
            self.renderer.draw_start(camera_surface, face_visible)
            return
        self.calibration.add(face_visible, dt)
        self.renderer.draw_start(camera_surface, face_visible, self.calibration.seconds_left())
        if self.calibration.done():
            self.go_to(self.after_calibration)

    def loading_screen(self, dt):
        """LOADING: a few seconds to get ready, with the exam's name and today's gossip."""
        self.loading_time += dt
        time_part = min(1.0, self.loading_time / LOADING_TIME)
        self.renderer.draw_loading(loading_progress(time_part, self.loading_plan),
                                   self.current_run.number(), self.current_run.quiz()["title"])
        if self.loading_time >= LOADING_TIME:
            self.begin_playing()

    def menu_screen(self, frame, face_found, dt):
        """MENU, HELP, SETTINGS and END: the head (or keys, or mouse) chooses an item."""
        yaw, pitch = self.tracker.relative_angles()
        action = self.head_input.update(yaw, pitch, dt, face_found)
        if action is not None:
            self.menu_action(action)
            if self.screen_name not in MENU_SCREENS:
                # Left the menus (e.g. PLAY): the new screen is drawn from the
                # next frame on; this frame keeps showing the menu.
                return

        name = self.screen_name
        selected = self.menus[name].selected
        select_progress = self.head_input.progress(SELECT)
        back_progress = self.head_input.progress(BACK) if name != MENU else 0.0
        head_pause = self.head_input.paused_part()
        if name == END:
            self.count_score(dt)
            self.game_screen(frame, face_found, time.time(), 0.0, over=True)
            self.renderer.draw_end(self.game, self.current_run, self.chat, self.menu_labels(), selected,
                                   select_progress, back_progress, head_pause, self.end_time)
        elif name == BRIEFING:
            self.turn_reel(dt)
            run = self.current_run
            labels = [] if self.spinning() else self.menus[BRIEFING].items
            self.renderer.draw_briefing(run.number(), run.quiz()["title"], run.pool(),
                                        run.chosen(), self.spin_time, labels,
                                        self.menus[BRIEFING].selected, select_progress,
                                        back_progress, head_pause)
        elif name == RUN_END:
            self.count_score(dt)
            self.renderer.draw_run_end(self.current_run, self.top, self.new_place,
                                       self.menu_labels(), selected, select_progress,
                                       back_progress, head_pause, self.end_time)
        else:
            self.tracker.draw_face(frame, WHITE_BGR)
            if name == HELP:
                lines, camera_surface = HELP_LINES, None   # the text needs the room
            else:
                lines, camera_surface = None, camera_to_surface(frame, MENU_PREVIEW_SIZE)
            self.renderer.draw_menu(TITLES[name], self.menu_labels(), selected,
                                    select_progress, back_progress, camera_surface, lines,
                                    head_pause, self.top if name == MENU else None)

    def pick_chat(self):
        """An exam was just failed: pick the game over conversation (never the same twice in a row)."""
        reason = self.game.lose_reason
        chat = GAME_OVER_CHAT[reason][self.chat_bags[reason].draw()]
        title = self.current_run.quiz()["title"]
        self.chat = [(who, text.replace("{exam}", title)) for who, text in chat]

    def crossfade(self, dt):
        """Lay the old screen's last picture over the new screen, fading it out."""
        if self.fade_picture is None:
            return
        self.fade_time += dt
        left = 1 - self.fade_time / SCREEN_FADE_TIME   # 1 = just changed, 0 = done
        if left <= 0:
            self.fade_picture = None
            return
        # Smoothstep (3x² - 2x³): starts and ends gently, not at one speed.
        self.fade_picture.set_alpha(int(255 * left * left * (3 - 2 * left)))
        self.renderer.screen.blit(self.fade_picture, (0, 0))

    def counted_parts(self):
        """
        What the END / RUN_END screen counts up (tally.py): the exam's score
        parts, or each exam's score for the run. [] = nothing (a failed exam).
        """
        if self.screen_name == RUN_END:
            return self.current_run.score_parts()
        return self.game.score_parts()

    def count_done(self):
        """True when the score count is over (or there is none)."""
        return is_done(self.counted_parts(), self.end_time)

    def count_score(self, dt):
        """The score count (tally.py): a rising tick for each new part, a chord at the end."""
        parts = self.counted_parts()
        if not parts:
            return
        was_done = is_done(parts, self.end_time)
        before = parts_shown(parts, self.end_time)
        self.end_time += dt
        for i in range(before, parts_shown(parts, self.end_time)):
            self.sounds.play(tally_sound(i))
        if is_done(parts, self.end_time) and not was_done:
            new_top = self.screen_name == RUN_END and self.new_place is not None
            self.sounds.play("new_top" if new_top else "tally_done")

    def game_screen(self, frame, face_found, now, dt, over=False):
        """GAME (and, with over=True, the frozen game under the END menu)."""
        paused = False
        if not over:
            new_direction = self.tracker.current_direction(now, face_found)
            # None = the player is gone. After losing (the scenes before the
            # end menu) nothing depends on the face, so nothing pauses.
            paused = new_direction is None and self.game.state == PLAYING
        if not over and not paused:
            if new_direction is not None:
                self.direction = new_direction
            in_scene = self.game.in_scene()
            # After the warning scene the classroom fades in again.
            looking = self.direction == SCREEN and not in_scene
            self.look_time = self.look_time + dt if looking else 0.0
            # Event names match sound names.
            # Looking down at the paper you hear nothing from the teacher.
            # During the warning scene the teacher is at your desk: they stop.
            heard = []
            if not in_scene:
                # Above the exam's hidden suspicion point the teacher keeps
                # watching you until the bar drains back under it.
                changes = self.teacher.update(dt, keep_watching=self.game.under_suspicion())
                heard = self.teacher.sounds(changes, can_hear=self.direction != DOWN)
            # game.update() also runs during the scene: it counts the scene down.
            for name in heard + self.game.update(self.direction, dt, self.teacher):
                self.sounds.play(name)
                if name == "lost":
                    self.pick_chat()

        self.tracker.draw_face(frame, FACE_COLOURS[self.direction])
        # The classroom is always shown at the end: if you were caught, you
        # see the teacher looking at you.
        view = 1.0 if over else classroom_view(self.direction, self.look_time, self.show_always)
        note = "" if over else self.tracker.status
        yaw, pitch = self.tracker.relative_angles()
        self.renderer.draw_game(self.game, self.teacher, self.direction, view,
                                camera_to_surface(frame), yaw, pitch, self.clock.get_fps(),
                                note, self.show_always)
        if over:
            return
        if self.game.in_scene():
            self.renderer.draw_scene(self.game, self.teacher, self.chat)
        elif self.game.popup_text:
            self.renderer.draw_popup(self.game.popup_text)
        if paused:
            self.renderer.draw_paused()       # nothing was updated: the game is frozen
        # After the last warning, the scene plays out before the end screen.
        if self.game.state != PLAYING and not self.game.in_scene():
            self.go_to(END)

    # ------------------------------------------------------------------
    # The main loop
    # ------------------------------------------------------------------
    def run(self):
        # Our team's intro first; it returns False if the window was closed.
        # (The camera starts in the background meanwhile, see camera.py.)
        self.running = glitch_intro.play(self.renderer.screen, self.clock)
        camera_waiting = False

        previous_time = time.time()
        while self.running:
            # 1. Keys, clicks and the window's X button.
            self.handle_events()

            if not self.running:
                break   # quitting must also work before the camera has sent a picture

            # 2. Newest webcam frame and head angles.
            frame = self.camera.read()
            if frame is None:
                # No (fresh) picture: the camera is starting or reconnecting (camera.py
                # does that in the background). Everything waits, and the waiting
                # time is thrown away, so the exam clock does not run meanwhile.
                previous_time = time.time()
                if not camera_waiting:
                    self.tracker.reset_tracking()   # old angles are not true any more
                    self.game.neighbours.reset_focus()   # waiting must not count as looking
                camera_waiting = True
                if self.screen_name == CALIBRATING:
                    self.calibration.restart()
                self.renderer.t = previous_time - self.start_time
                self.renderer.draw_camera_wait(self.camera.status
                                               or "Waiting for a fresh camera picture...")
                pygame.display.flip()
                self.clock.tick(FPS)
                continue
            camera_waiting = False
            now = time.time()
            dt = min(now - previous_time, MAX_DT)
            previous_time = now
            face_found = self.tracker.read(frame, now)
            # Seconds since the program started: the renderer animates with it.
            self.renderer.t = now - self.start_time

            # The music: only in the menus; it fades out while loading an exam
            # and fades back in after it.
            self.sounds.music(self.screen_name not in SILENT_SCREENS, dt)

            # 3 + 4. Rules, sounds and drawing for the current screen.
            if self.screen_name == DISCLAIMER:
                for sound in self.notice.update(dt):
                    self.sounds.play(sound)
                self.renderer.draw_disclaimer(self.notice)
                if self.notice.done():
                    self.go_to(START)
                    # The music starts here, from its beginning: not during the
                    # intro (its own sound) or the notice (typewriter and stamp).
                    self.sounds.start_music()
            elif self.screen_name in (START, CALIBRATING):
                self.start_screen(frame, now, dt)
            elif self.screen_name == LOADING:
                self.loading_screen(dt)
            elif self.screen_name in MENU_SCREENS:
                self.menu_screen(frame, face_found, dt)
            else:
                self.game_screen(frame, face_found, now, dt)

            self.crossfade(dt)
            pygame.display.flip()
            self.clock.tick(FPS)

        # Give the webcam back to the system and close everything.
        self.camera.release()
        self.tracker.close()
        pygame.quit()


if __name__ == "__main__":
    App().run()
