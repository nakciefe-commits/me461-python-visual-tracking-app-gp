"""
The game: menus, the classroom, the teacher, the copy bar, the suspicion bar.

Run it with:   ./run.sh      (or  .venv/bin/python main.py)
Keys:          Space = calibrate (start screen), q = quit, F11 = fullscreen on/off,
               menus: arrows / Enter / Esc (or the head: tilt up/down, turn right = select,
                      turn left = back), or the mouse,
               in the game: a / b / c / d = write that answer (while looking at your paper),
                      r = restart, m = main menu, k = recalibrate, Esc = quit,
                      t = always show the classroom and the teacher's state (for testing),
                      Space = skip the scenes after losing

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

import glitch_intro
from camera import Camera
from disclaimer import Disclaimer
from game import Game, PLAYING
from head_tracker import HeadTracker, Calibration, DOWN, SCREEN, LEFT, RIGHT
from menu import (Menu, HeadMenuInput, next_choice, loading_steps, loading_progress,
                  UP, DOWN as MENU_DOWN, SELECT, BACK)
from render import (Renderer, camera_to_surface, BIG_PREVIEW_SIZE, MENU_PREVIEW_SIZE,
                    HELP_LINES, LOADING_TIPS, DISCLAIMER_LETTERS)
from settings import (CAMERA_INDEX, CALIBRATION_TIME, WINDOW_WIDTH, WINDOW_HEIGHT, FPS, FADE_TIME,
                      FULLSCREEN, MAXIMIZED, EXAM_TIME_CHOICES, LOADING_TIME, SMOOTH_SCALING)
from sounds import Sounds
from teacher import Teacher

MAX_DT = 0.1   # seconds; a slow frame must not fill a whole bar at once
# Answer keys -> the letter they write on your paper.
LETTER_KEYS = {pygame.K_a: "A", pygame.K_b: "B", pygame.K_c: "C", pygame.K_d: "D"}
# Menu keys -> the same actions the head gives (see menu.py).
MENU_KEYS = {pygame.K_UP: UP, pygame.K_DOWN: MENU_DOWN,
             pygame.K_RETURN: SELECT, pygame.K_KP_ENTER: SELECT, pygame.K_SPACE: SELECT,
             pygame.K_RIGHT: SELECT, pygame.K_LEFT: BACK, pygame.K_BACKSPACE: BACK}

# The screens. "Face not found" is not a screen of its own: it is the GAME
# screen with the game paused. DISCLAIMER is shown once, when the game opens.
# LOADING is the short "get ready" screen before each game.
DISCLAIMER, START, CALIBRATING, MENU, HELP, SETTINGS, LOADING, GAME, END = (
    "DISCLAIMER", "START", "CALIBRATING", "MENU", "HELP", "SETTINGS", "LOADING", "GAME", "END")
MENU_SCREENS = (MENU, HELP, SETTINGS, END)   # screens with a list of items to choose from
TITLES = {MENU: "DON'T GET CAUGHT", HELP: "HOW TO PLAY", SETTINGS: "SETTINGS"}

# Colour of the face drawing for each direction, (Blue, Green, Red) for OpenCV.
FACE_COLOURS = {DOWN: (240, 150, 80), SCREEN: (60, 200, 240),
                LEFT: (110, 200, 70), RIGHT: (110, 200, 70)}
WHITE_BGR = (240, 240, 240)


def show_error(renderer, message):
    """Show an error on the window for a few seconds (e.g. no webcam)."""
    renderer.screen.fill((25, 28, 35))
    renderer.text(message, renderer.medium, (220, 60, 60),
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), center=True)
    pygame.display.flip()
    print(message)
    time.sleep(3)


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
            SETTINGS: Menu(["EXAM TIME", "SOUND", "FULLSCREEN", "RECALIBRATE", "BACK"]),
            END: Menu(["PLAY AGAIN", "MAIN MENU", "QUIT"]),
        }
        self.head_input = HeadMenuInput()

        self.notice = Disclaimer(DISCLAIMER_LETTERS)   # the disclaimer screen's state
        self.screen_name = DISCLAIMER
        self.after_calibration = MENU   # where calibrating leads to
        self.direction = SCREEN   # last known direction, kept while paused
        self.look_time = 0.0      # seconds the player has been looking at the screen in one go
        self.show_always = False  # t key: always show the classroom (for testing)
        self.loading_time = 0.0   # seconds the loading screen has been shown
        self.loading_tip = 0      # which funny loading line it shows
        self.loading_plan = []    # when the loading bar jumps (see menu.loading_steps())
        self.start_time = time.time()
        self.running = True

    # ------------------------------------------------------------------
    # Moving between screens
    # ------------------------------------------------------------------
    def go_to(self, name):
        self.screen_name = name
        if name in MENU_SCREENS:
            # The head may still be turned from before: wait until it is straight.
            self.head_input.reset()
        if name == END:
            self.menus[END].selected = 0   # "PLAY AGAIN"

    def calibrate_then(self, next_screen):
        """Calibrate, then go to next_screen."""
        self.calibration.restart()
        self.after_calibration = next_screen
        self.go_to(CALIBRATING)

    def start_game(self):
        """A new game, after the short loading screen (see loading_screen())."""
        self.loading_time = 0.0
        self.loading_tip = random.randrange(len(LOADING_TIPS))
        self.loading_plan = loading_steps(random.Random())   # a new uneven fill each time
        self.go_to(LOADING)

    def begin_playing(self):
        """The loading screen is over: reset everything and start the clock."""
        self.game.reset()
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
        return [f"EXAM TIME   {self.game.exam_time} s",
                f"SOUND   {on_off[not self.sounds.muted]}",
                f"FULLSCREEN   {on_off[self.fullscreen]}",
                "RECALIBRATE",
                "BACK"]

    def menu_action(self, action):
        """UP, DOWN, SELECT or BACK, from the head, the keys or the mouse."""
        menu = self.menus[self.screen_name]
        if action in (UP, MENU_DOWN):
            menu.move(-1 if action == UP else 1)
            self.sounds.play("menu_move")
        elif action == BACK:
            if self.screen_name != MENU:   # the main menu has nothing to go back to
                self.sounds.play("menu_move")
                self.go_to(MENU)
        else:
            self.sounds.play("menu_select")
            self.choose(menu.current())

    def choose(self, item):
        """Do what the selected menu item says."""
        if item in ("PLAY", "PLAY AGAIN"):
            self.start_game()
        elif item == "HOW TO PLAY":
            self.go_to(HELP)
        elif item == "SETTINGS":
            self.go_to(SETTINGS)
        elif item in ("MAIN MENU", "BACK"):
            self.go_to(MENU)
        elif item == "QUIT":
            self.running = False
        elif item == "EXAM TIME":
            # Used from the next game on (Game.reset() reads it).
            self.game.exam_time = next_choice(EXAM_TIME_CHOICES, self.game.exam_time)
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
                for i, rect in enumerate(self.renderer.menu_rects):
                    if rect.collidepoint(event.pos):
                        self.menus[self.screen_name].selected = i
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
            elif name == END and key == pygame.K_r:
                self.start_game()
            elif name == END and key == pygame.K_m:
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
            elif key == pygame.K_r:                  # new game
                self.start_game()
            elif key == pygame.K_m:                  # give up, back to the main menu
                self.go_to(MENU)
            elif key in LETTER_KEYS:
                # game.write() checks that you look at your paper and
                # have read the answer; otherwise nothing happens.
                for sound in self.game.write(LETTER_KEYS[key], self.direction):
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
        """LOADING: a few seconds to get ready, so the game does not start all at once."""
        self.loading_time += dt
        time_part = min(1.0, self.loading_time / LOADING_TIME)
        self.renderer.draw_loading(loading_progress(time_part, self.loading_plan), self.loading_tip)
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
            self.game_screen(frame, face_found, time.time(), 0.0, over=True)
            self.renderer.draw_end(self.game, self.menu_labels(), selected,
                                   select_progress, back_progress, head_pause)
        else:
            self.tracker.draw_face(frame, WHITE_BGR)
            if name == HELP:
                lines, camera_surface = HELP_LINES, None   # the text needs the room
            else:
                lines, camera_surface = None, camera_to_surface(frame, MENU_PREVIEW_SIZE)
            self.renderer.draw_menu(TITLES[name], self.menu_labels(), selected,
                                    select_progress, back_progress, camera_surface, lines,
                                    head_pause)

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
                heard = self.teacher.sounds(self.teacher.update(dt),
                                            can_hear=self.direction != DOWN)
            # game.update() also runs during the scene: it counts the scene down.
            for name in heard + self.game.update(self.direction, dt, self.teacher):
                self.sounds.play(name)

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
            self.renderer.draw_scene(self.game, self.teacher)
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
        if not self.camera.running:
            show_error(self.renderer, "Could not open the webcam. Try CAMERA_INDEX in settings.py.")
            pygame.quit()
            return
        # Our team's intro first; it returns False if the window was closed.
        self.running = glitch_intro.play(self.renderer.screen, self.clock)

        previous_time = time.time()
        while self.running:
            # 1. Keys, clicks and the window's X button.
            self.handle_events()

            # 2. Newest webcam frame and head angles.
            frame = self.camera.read()
            if frame is None:
                show_error(self.renderer, "The webcam stopped sending pictures.")
                break
            now = time.time()
            dt = min(now - previous_time, MAX_DT)
            previous_time = now
            face_found = self.tracker.read(frame, now)
            # Seconds since the program started: the renderer animates with it.
            self.renderer.t = now - self.start_time

            # 3 + 4. Rules, sounds and drawing for the current screen.
            if self.screen_name == DISCLAIMER:
                for sound in self.notice.update(dt):
                    self.sounds.play(sound)
                self.renderer.draw_disclaimer(self.notice)
                if self.notice.done():
                    self.go_to(START)
            elif self.screen_name in (START, CALIBRATING):
                self.start_screen(frame, now, dt)
            elif self.screen_name == LOADING:
                self.loading_screen(dt)
            elif self.screen_name in MENU_SCREENS:
                self.menu_screen(frame, face_found, dt)
            else:
                self.game_screen(frame, face_found, now, dt)

            pygame.display.flip()
            self.clock.tick(FPS)

        # Give the webcam back to the system and close everything.
        self.camera.release()
        self.tracker.close()
        pygame.quit()


if __name__ == "__main__":
    App().run()
