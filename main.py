"""
The game: the classroom, the teacher, the copy bar, the suspicion bar.

Run it with:   ./run.sh      (or  .venv/bin/python main.py)
Keys:          Space = calibrate (start screen), q / Esc = quit,
               r = restart, c = recalibrate, F11 = fullscreen on/off,
               d = always show the classroom and the teacher's state (for testing)

The program is one loop that repeats about 30 times a second:
    1. handle key presses and clicks
    2. take the newest webcam frame and find the head direction
    3. move the teacher and the game rules forward (unless paused or over)
    4. play sounds for what happened, draw the screen
"""

import time

import pygame

from camera import Camera
from game import Game, PLAYING
from head_tracker import HeadTracker, Calibration, DOWN, SCREEN, LEFT, RIGHT
from render import Renderer, camera_to_surface, BIG_PREVIEW_SIZE
from settings import (CAMERA_INDEX, CALIBRATION_TIME, WINDOW_WIDTH, WINDOW_HEIGHT, FPS, FADE_TIME,
                      FULLSCREEN, MAXIMIZED)
from sounds import Sounds
from teacher import Teacher

MAX_DT = 0.1   # seconds; a slow frame must not fill a whole bar at once

# The screens. "Face not found" is not a screen of its own: it is the GAME
# screen with the game paused. DISCLAIMER is shown once, when the game opens.
DISCLAIMER, START, CALIBRATING, GAME, END = (
    "DISCLAIMER", "START", "CALIBRATING", "GAME", "END")

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


def main():
    pygame.init()
    fullscreen = FULLSCREEN
    screen = open_window(fullscreen)
    pygame.display.set_caption("Don't Get Caught - demo")
    renderer = Renderer(screen)
    sounds = Sounds()
    clock = pygame.time.Clock()

    camera = Camera(CAMERA_INDEX)
    if not camera.running:
        show_error(renderer, "Could not open the webcam. Try CAMERA_INDEX in settings.py.")
        pygame.quit()
        return

    tracker = HeadTracker()
    calibration = Calibration(tracker, CALIBRATION_TIME)
    game = Game()
    teacher = Teacher()
    screen_name = DISCLAIMER
    direction = SCREEN   # last known direction, kept while paused
    look_time = 0.0      # seconds the player has been looking at the screen in one go
    show_always = False  # d key: always show the classroom (for testing)
    previous_time = time.time()
    running = True

    while running:
        # 1. Keys, clicks and the window's X button.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    open_window(fullscreen)   # same surface size, so the renderer keeps working
                elif screen_name == DISCLAIMER:
                    # Checked before Space below, so one press does not also
                    # start calibrating.
                    if event.key == pygame.K_SPACE:
                        screen_name = START
                elif ((event.key == pygame.K_SPACE and screen_name == START)
                      or (event.key == pygame.K_c and screen_name == GAME)):  # c: recalibrate, keep the game
                    calibration.restart()
                    screen_name = CALIBRATING
                elif event.key == pygame.K_r:        # new game, back to the start screen
                    game.reset()
                    teacher.reset()
                    screen_name = START
                elif event.key == pygame.K_d:
                    show_always = not show_always
            elif event.type == pygame.MOUSEBUTTONDOWN and screen_name == DISCLAIMER:
                screen_name = START                  # a click anywhere continues
            elif (event.type == pygame.MOUSEBUTTONDOWN and screen_name == START
                  and renderer.button_rect.collidepoint(event.pos)):
                calibration.restart()
                screen_name = CALIBRATING

        # 2. Newest webcam frame and head angles.
        frame = camera.read()
        if frame is None:
            show_error(renderer, "The webcam stopped sending pictures.")
            break

        now = time.time()
        dt = min(now - previous_time, MAX_DT)
        previous_time = now
        face_found = tracker.read(frame, now)
        yaw, pitch = tracker.relative_angles()

        # 3 + 4. Rules, sounds and drawing for the current screen.
        if screen_name == DISCLAIMER:
            renderer.draw_disclaimer()

        elif screen_name in (START, CALIBRATING):
            tracker.draw_face(frame, WHITE_BGR)
            camera_surface = camera_to_surface(frame, BIG_PREVIEW_SIZE)
            face_visible = tracker.face_visible(now)
            if screen_name == START:
                renderer.draw_start(camera_surface, face_visible)
            else:
                calibration.add(face_visible, dt)
                renderer.draw_start(camera_surface, face_visible, calibration.seconds_left())
                if calibration.done():
                    screen_name = GAME

        else:  # GAME or END: both draw the game screen
            over = screen_name == END
            paused = False
            if not over:
                new_direction = tracker.current_direction(now, face_found)
                paused = new_direction is None   # None = the player is gone
            if not over and not paused:
                direction = new_direction
                look_time = look_time + dt if direction == SCREEN else 0.0
                # Event names match sound names.
                # Looking down at the paper you hear nothing from the teacher.
                heard = teacher.sounds(teacher.update(dt), can_hear=direction != DOWN)
                for name in heard + game.update(direction, dt, teacher):
                    sounds.play(name)

            tracker.draw_face(frame, FACE_COLOURS[direction])
            # The classroom is always shown at the end: if you were caught, you
            # see the teacher looking at you.
            view = 1.0 if over else classroom_view(direction, look_time, show_always)
            note = "" if over else tracker.status
            renderer.draw_game(game, teacher, direction, view, camera_to_surface(frame),
                               yaw, pitch, clock.get_fps(), note, show_always)
            if over:
                renderer.draw_end(game)
            elif paused:
                renderer.draw_paused()       # nothing was updated: the game is frozen
            elif game.popup_text:
                renderer.draw_popup(game.popup_text)
            if game.state != PLAYING:
                screen_name = END

        pygame.display.flip()
        clock.tick(FPS)

    # Give the webcam back to the system and close everything.
    camera.release()
    tracker.close()
    pygame.quit()


if __name__ == "__main__":
    main()
