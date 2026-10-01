"""
The game (demo version): head direction, copy bar, suspicion bar, warnings.

Run it with:   ./run.sh      (or  .venv/bin/python main.py)
Keys:          Space = calibrate (start screen), q / Esc = quit,
               r = restart, c = recalibrate

The program is one loop that repeats about 30 times a second:
    1. handle key presses and clicks
    2. take the newest webcam frame and find the head direction
    3. move the game rules forward (unless paused or over)
    4. play sounds for what happened, draw the screen
"""

import time

import pygame

from camera import Camera
from game import Game, PLAYING
from head_tracker import HeadTracker, Calibration, DOWN, SCREEN, LEFT, RIGHT
from render import Renderer, camera_to_surface, BIG_PREVIEW_SIZE
from settings import CAMERA_INDEX, CALIBRATION_TIME, WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from sounds import Sounds

MAX_DT = 0.1   # seconds; a slow frame must not fill a whole bar at once

# The screens. "Face not found" is not a screen of its own: it is the GAME
# screen with the game paused.
START, CALIBRATING, GAME, END = "START", "CALIBRATING", "GAME", "END"

# Colour of the face drawing for each direction, (Blue, Green, Red) for OpenCV.
# Matches the option boxes on screen.
FACE_COLOURS = {DOWN: (240, 150, 80), SCREEN: (60, 200, 240), LEFT: (110, 200, 70),
                RIGHT: (110, 200, 70)}
WHITE_BGR = (240, 240, 240)


def show_error(renderer, message):
    """Show an error on the window for a few seconds (e.g. no webcam)."""
    renderer.screen.fill((25, 28, 35))
    renderer.text(message, renderer.medium, (220, 60, 60),
                  (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2), center=True)
    pygame.display.flip()
    print(message)
    time.sleep(3)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Don't Get Caught - demo")
    renderer = Renderer(screen)
    sounds = Sounds()
    clock = pygame.time.Clock()

    camera = Camera(CAMERA_INDEX)
    if not camera.is_open():
        show_error(renderer, "Could not open the webcam. Try CAMERA_INDEX in settings.py.")
        pygame.quit()
        return

    tracker = HeadTracker()
    calibration = Calibration(tracker, CALIBRATION_TIME)
    game = Game()
    screen_name = START
    direction = SCREEN   # last known direction, kept while the face is lost

    start_time = time.time()
    previous_time = start_time
    last_timestamp_ms = -1
    running = True

    while running:
        # 1. Keys, clicks and the window's X button.
        start_calibrating = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE and screen_name == START:
                    start_calibrating = True
                elif event.key == pygame.K_r:        # new game, back to the start screen
                    game.reset()
                    screen_name = START
                elif event.key == pygame.K_c and screen_name == GAME:
                    start_calibrating = True         # recalibrate, keep the game
            elif (event.type == pygame.MOUSEBUTTONDOWN and screen_name == START
                  and renderer.button_rect.collidepoint(event.pos)):
                start_calibrating = True
        if start_calibrating:
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

        # MediaPipe needs a timestamp that grows on every frame.
        timestamp_ms = max(int((now - start_time) * 1000), last_timestamp_ms + 1)
        last_timestamp_ms = timestamp_ms
        face_found = tracker.read_angles(frame, timestamp_ms)
        # Seen recently enough? Short gaps (mid-turn) do not count as lost.
        face_visible = tracker.face_visible(timestamp_ms)
        yaw, pitch = tracker.relative_angles()

        # A note under the preview when the face is not tracked right now.
        tracking_note = None
        if not face_found and tracker.lost_while_looking_down():
            tracking_note = "head down"
        elif not face_found:
            tracking_note = "face lost..."

        # Draw the tracking onto the face, coloured like the current option.
        in_game = screen_name in (GAME, END)
        tracker.draw_face(frame, FACE_COLOURS[direction] if in_game else WHITE_BGR)

        # 3 + 4. Rules, sounds and drawing for the current screen.
        if screen_name in (START, CALIBRATING):
            camera_surface = camera_to_surface(frame, BIG_PREVIEW_SIZE)
            if screen_name == CALIBRATING:
                calibration.add(face_visible, dt)
                renderer.draw_start(camera_surface, face_visible, calibration.seconds_left())
                if calibration.done():
                    screen_name = GAME
            else:
                renderer.draw_start(camera_surface, face_visible)

        elif screen_name == GAME:
            # None = the player is gone: the game pauses.
            new_direction = tracker.current_direction(now, timestamp_ms, face_found)
            paused = new_direction is None
            if not paused:
                direction = new_direction
                for name in game.update(direction, dt):
                    sounds.play(name)   # event names match sound names
            renderer.draw_game(game, direction, camera_to_surface(frame), yaw, pitch,
                               clock.get_fps(), tracking_note, show_popup=not paused)
            if paused:
                renderer.draw_paused()  # nothing was updated: the game is frozen
            if game.state != PLAYING:
                screen_name = END

        else:  # END
            renderer.draw_game(game, direction, camera_to_surface(frame), yaw, pitch,
                               clock.get_fps(), tracking_note, show_popup=False)
            renderer.draw_end(game)

        pygame.display.flip()
        clock.tick(FPS)

    # Give the webcam back to the system and close everything.
    camera.release()
    tracker.close()
    pygame.quit()


if __name__ == "__main__":
    main()
