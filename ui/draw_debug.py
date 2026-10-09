"""
The debug panel (F3, on every screen): what the head tracking sees and
decides, step by step, for showing how the game works. Part of Renderer
(see render.py). It only reads; it changes nothing.

From top to bottom, in the order the data flows each frame:
    1. the webcam picture with MediaPipe's 478 face points (the mesh), the
       face box and an arrow where the nose points; how long MediaPipe took
    2. the head rotation matrix MediaPipe gives, and the angles from it
    3. the yaw/pitch chart: the calibrated thresholds split it into
       LEFT / SCREEN / RIGHT / DOWN; the hollow dot is this frame's raw
       angle, the full dot the smoothed one (SMOOTHING)
    4. the last few seconds of yaw and pitch, with the thresholds
    5. the decision: raw direction -> held for HOLD_TIME -> the direction used
       (drawn under the chart, above the graph)
    6. during an exam: the game's state (suspicion, teacher, reading)
"""

from collections import deque

import pygame

from settings import (DEBUG_HISTORY_TIME, DEBUG_ANGLE_RANGE, HOLD_TIME, SMOOTHING, MAX_WARNINGS,
                      LOST_DOWN_SPEED)
from tracking.head_tracker import DOWN, SCREEN, LEFT, RIGHT
from ui.style import WHITE, BLACK, NEON_CYAN, NEON_PINK, NEON_YELLOW, NEON_GREEN, mix, mono_font

DEBUG_WIDTH = 330             # pixels, the panel on the right side of the window
DEBUG_MARGIN = 8              # pixels inside the panel's edges
DEBUG_CAMERA_SIZE = (280, 210)   # pixels, the webcam picture (4:3)
DEBUG_ALPHA = 215             # 0-255, how dark the panel's background is
DEBUG_LINE = 15               # pixels from one line of text to the next
CHART_SIZE = (150, 116)       # pixels, the yaw/pitch chart
GRAPH_HEIGHT = 62             # pixels, the yaw and pitch over time
GREY = (140, 140, 150)
DIM = (60, 60, 70)
# A colour for each direction (the chart's areas, the decision line).
DIRECTION_COLOURS = {SCREEN: NEON_CYAN, LEFT: NEON_YELLOW, RIGHT: NEON_YELLOW, DOWN: NEON_GREEN, None: NEON_PINK}
YAW_COLOUR, PITCH_COLOUR = NEON_YELLOW, NEON_GREEN


class DebugDrawing:
    def draw_debug(self, tracker, now, camera_surface, track_ms, fps, game=None, teacher=None, direction=None):
        """
        The whole panel. now: the time the tracker was given (seconds);
        camera_surface: the webcam picture with the face drawn on (or None);
        track_ms: how long MediaPipe took this frame; game, teacher,
        direction: the exam's state, or None outside one.
        """
        if not hasattr(self, "debug_history"):
            self.debug_history = deque()   # (time, yaw, pitch) of the last DEBUG_HISTORY_TIME seconds
            self.debug_font = mono_font(13)
        yaw, pitch = tracker.relative_angles()
        self.debug_history.append((self.t, yaw, pitch))
        while self.debug_history and self.t - self.debug_history[0][0] > DEBUG_HISTORY_TIME:
            self.debug_history.popleft()

        left = self.width - DEBUG_WIDTH
        self.darken(DEBUG_ALPHA, (left, 0, DEBUG_WIDTH, self.height))
        x = left + DEBUG_MARGIN
        self.debug_text("DEBUG  (F3 = hide)", x, 6, NEON_PINK)

        # 1. The camera and MediaPipe.
        y = 24
        if camera_surface is not None:
            self.screen.blit(camera_surface, (x, y))
        pygame.draw.rect(self.screen, NEON_CYAN, (x, y, *DEBUG_CAMERA_SIZE), 1)
        y += DEBUG_CAMERA_SIZE[1] + 4
        points = len(tracker.landmarks) if tracker.landmarks is not None else 0
        # The tracker's note when there is no face ("head down", "face lost...").
        note = f" | {tracker.status}" if tracker.status else ""
        self.debug_text(f"MediaPipe: {points} face points{note}", x, y, NEON_PINK if note else WHITE)
        self.debug_text(f"inference {track_ms:5.1f} ms   game {fps:4.0f} fps", x, y + DEBUG_LINE)

        # 2 + 3. The chart, with the matrix and the angles next to it.
        y += 2 * DEBUG_LINE + 6
        self.angle_chart(tracker, x, y)
        self.rotation_and_angles(tracker, x + CHART_SIZE[0] + 10, y)

        # 5. The decision, under them.
        y += CHART_SIZE[1] + DEBUG_LINE + 4
        self.decision_line(tracker, now, x, y, direction)

        # 4. The angles over time.
        y += DEBUG_LINE + 10
        self.angle_graph(tracker, x, y, DEBUG_WIDTH - 2 * DEBUG_MARGIN)

        # 6. The exam.
        if game is not None and teacher is not None:
            self.game_state_lines(game, teacher, x, y + GRAPH_HEIGHT + 6)

    def debug_text(self, message, x, y, colour=WHITE):
        self.screen.blit(self.debug_font.render(message, True, colour), (x, y))

    def chart_point(self, rect, yaw, pitch):
        """Where (yaw, pitch) is on a chart: turning to your left goes left (mirrored, like the camera)."""
        fx = 0.5 - 0.5 * max(-1.0, min(1.0, yaw / DEBUG_ANGLE_RANGE))
        fy = 0.5 - 0.5 * max(-1.0, min(1.0, pitch / DEBUG_ANGLE_RANGE))
        return int(rect.x + fx * rect.width), int(rect.y + fy * rect.height)

    def angle_chart(self, tracker, x, y):
        """Yaw across, pitch up and down, split by the thresholds into the four directions."""
        rect = pygame.Rect(x, y, *CHART_SIZE)
        # The thresholds as lines: where LEFT, RIGHT and DOWN start.
        left_x = self.chart_point(rect, tracker.left_threshold, 0)[0]
        right_x = self.chart_point(rect, -tracker.right_threshold, 0)[0]
        down_y = self.chart_point(rect, 0, -tracker.down_threshold)[1]
        areas = [(DOWN, pygame.Rect(rect.x, down_y, rect.width, rect.bottom - down_y)),
                 (LEFT, pygame.Rect(rect.x, rect.y, left_x - rect.x, down_y - rect.y)),
                 (RIGHT, pygame.Rect(right_x, rect.y, rect.right - right_x, down_y - rect.y)),
                 (SCREEN, pygame.Rect(left_x, rect.y, right_x - left_x, down_y - rect.y))]
        current = tracker.raw_direction()
        for name, area in areas:
            # The area the head is in now is lit up.
            colour = DIRECTION_COLOURS[name]
            pygame.draw.rect(self.screen, mix(BLACK, colour, 0.35 if name == current else 0.12), area)
            label = self.debug_font.render(name, True, mix(BLACK, colour, 0.8))
            self.screen.blit(label, label.get_rect(center=area.center))
        pygame.draw.rect(self.screen, GREY, rect, 1)
        # The raw angle of this frame (hollow) and the smoothed one (full).
        raw = self.chart_point(rect, tracker.raw_yaw - tracker.neutral_yaw,
                               tracker.raw_pitch - tracker.neutral_pitch)
        pygame.draw.circle(self.screen, WHITE, raw, 5, 1)
        pygame.draw.circle(self.screen, NEON_PINK, self.chart_point(rect, *tracker.relative_angles()), 4)
        self.debug_text("yaw / pitch (deg)", x, rect.bottom - 1, GREY)

    def rotation_and_angles(self, tracker, x, y):
        """The rotation matrix MediaPipe gives, and the angles worked out from it."""
        self.debug_text("rotation matrix", x, y, GREY)
        rows = tracker.rotation or [[0.0] * 3] * 3
        for i, row in enumerate(rows):
            self.debug_text(" ".join(f"{value:+.2f}" for value in row), x, y + (i + 1) * DEBUG_LINE)
        yaw, pitch = tracker.relative_angles()
        y += 4 * DEBUG_LINE + 6
        self.debug_text(f"yaw   {yaw:+6.1f}", x, y, YAW_COLOUR)
        self.debug_text(f"pitch {pitch:+6.1f}", x, y + DEBUG_LINE, PITCH_COLOUR)
        self.debug_text(f"smoothing {SMOOTHING}", x, y + 2 * DEBUG_LINE, GREY)
        # How fast the head nods (negative = down): a fast nod down that loses
        # the face still counts as DOWN (LOST_DOWN_SPEED, head_tracker.py).
        speed = tracker.pitch_speed()
        self.debug_text(f"nod {speed:+5.0f} deg/s", x, y + 3 * DEBUG_LINE,
                        PITCH_COLOUR if speed < -LOST_DOWN_SPEED else GREY)

    def decision_line(self, tracker, now, x, y, direction):
        """
        raw -> held -> used: the direction of the angles right now, the bar
        filling while a new one waits HOLD_TIME, and the one the game uses.
        """
        raw = tracker.raw_direction()
        held = 1.0
        if tracker.candidate != tracker.direction:
            held = min(1.0, (now - tracker.candidate_since) / HOLD_TIME)
        shown = direction if direction is not None else tracker.direction
        raw_text = f"raw {raw} "
        self.debug_text(raw_text, x, y, DIRECTION_COLOURS[raw])
        bar_x = x + self.debug_font.size(raw_text)[0] + 4
        pygame.draw.rect(self.screen, DIM, (bar_x, y + 5, 50, 5))
        pygame.draw.rect(self.screen, NEON_CYAN, (bar_x, y + 5, int(50 * held), 5))
        self.debug_text(f"{HOLD_TIME:.1f}s -> used {shown}", bar_x + 56, y,
                        DIRECTION_COLOURS.get(shown, WHITE))

    def angle_graph(self, tracker, x, y, width):
        """Yaw and pitch over the last DEBUG_HISTORY_TIME seconds, with the thresholds dashed."""
        rect = pygame.Rect(x, y, width, GRAPH_HEIGHT)
        pygame.draw.rect(self.screen, mix(BLACK, WHITE, 0.06), rect)

        def height_of(angle):
            angle = max(-DEBUG_ANGLE_RANGE, min(DEBUG_ANGLE_RANGE, angle))
            return int(rect.centery - angle / DEBUG_ANGLE_RANGE * rect.height / 2)

        for angle, colour in ((tracker.left_threshold, YAW_COLOUR), (-tracker.right_threshold, YAW_COLOUR),
                              (-tracker.down_threshold, PITCH_COLOUR)):
            line_y = height_of(angle)
            for dash_x in range(rect.x, rect.right, 8):   # dashed: 4 on, 4 off
                pygame.draw.line(self.screen, mix(BLACK, colour, 0.5), (dash_x, line_y), (dash_x + 4, line_y))
        for index, colour in ((1, YAW_COLOUR), (2, PITCH_COLOUR)):
            points = [(int(rect.right - (self.t - sample[0]) / DEBUG_HISTORY_TIME * rect.width),
                       height_of(sample[index])) for sample in self.debug_history]
            if len(points) > 1:
                pygame.draw.lines(self.screen, colour, False, points, 2)
        pygame.draw.rect(self.screen, GREY, rect, 1)
        self.debug_text(f"last {DEBUG_HISTORY_TIME:.0f} s:", rect.x + 4, rect.y + 2, GREY)
        self.debug_text("yaw", rect.x + 90, rect.y + 2, YAW_COLOUR)
        self.debug_text("pitch", rect.x + 125, rect.y + 2, PITCH_COLOUR)

    def game_state_lines(self, game, teacher, x, y):
        """A few numbers from inside the exam's rules."""
        left, right = game.neighbours.focus_time[LEFT], game.neighbours.focus_time[RIGHT]
        lines = [
            (f"suspicion {game.suspicion.level * 100:3.0f} %   warnings {game.warnings}/{MAX_WARNINGS}",
             NEON_PINK if game.suspicion.level > 0.5 else WHITE),
            (f"teacher {teacher.place} {teacher.state} {teacher.time_in_state:.1f}/{teacher.duration:.1f} s",
             NEON_PINK if teacher.is_watching() else WHITE),
            (f"reading  L {left:.1f} s   R {right:.1f} s", WHITE),
        ]
        if game.in_scene():
            lines.append((f"scene {game.scene} {game.scene_time:.1f} s", NEON_YELLOW))
        for i, (message, colour) in enumerate(lines):
            self.debug_text(message, x, y + i * DEBUG_LINE, colour)
