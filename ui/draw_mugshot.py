"""
Drawing the mugshot scene, after losing and before game over: on a black,
silent screen your exam paper (torn in half and taped back together)
slowly fades in, with the webcam photo taken the moment you were caught
clipped on it. Then the teacher writes "GOT CAUGHT!" over it with a red
marker (a marker sound plays). Part of Renderer (see render.py).

The two pictures (see IMAGE_PROMPTS.md, "The mugshot"):
    MUGSHOT_IMAGE          the paper, with a pure green rectangle where the photo goes
    MUGSHOT_WRITTEN_IMAGE  the same paper with "GOT CAUGHT!" written on it
The green rectangle is found by its colour, so a new picture needs no
measuring. "Writing" = showing the written picture from left to right
over the plain one. Without the pictures the photo is shown on black with
the words under it.

The photo is only kept in memory (never saved), and replaced next time.
"""

import cv2
import numpy as np
import pygame

from logic.mugshot import crop_box
from settings import MUGSHOT_SCENE_TIME, MUGSHOT_FADE_TIME, MUGSHOT_WRITE_DELAY, MUGSHOT_WRITE_TIME
from ui.style import BLACK, WHITE

MUGSHOT_IMAGE = "torn"                  # the taped-up exam with the empty green photo
MUGSHOT_WRITTEN_IMAGE = "got_caught"    # the same, with "GOT CAUGHT!" written on it
GREEN_MARGIN = 40          # 0-255: a pixel is the photo's green if green is this much above red and blue
WRITING_DIFFERENCE = 80    # 0-255 (summed over R, G, B): a pixel this different is part of the writing
WRITING_COLUMN_PIXELS = 4  # a column with this many writing pixels is inside the writing
MUGSHOT_OUT_TIME = 0.4     # seconds the end fades to black, into the game over screen
PHOTO_BRIGHTNESS = 0.85    # the photo is a little darker: the paper is lit by one lamp
# Without the pictures:
PLAIN_PHOTO_SIZE = (180, 240)   # pixels, the photo on the black screen
PLAIN_RED = (220, 30, 40)       # the words "GOT CAUGHT!"
NO_PHOTO_GREY = (60, 60, 60)    # the photo when there was no webcam picture


def load_fitted(path, height):
    """A picture scaled to `height` pixels tall, keeping its shape."""
    picture = pygame.image.load(path).convert()
    return pygame.transform.smoothscale_by(picture, height / picture.get_height())


def green_mask(picture):
    """True for each pixel of the photo's green rectangle (as a numpy array, [x][y])."""
    rgb = pygame.surfarray.array3d(picture).astype(int)
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (green > red + GREEN_MARGIN) & (green > blue + GREEN_MARGIN)


def writing_columns(plain, written):
    """The first and last x where the two pictures differ (the writing), or the whole width."""
    difference = np.abs(pygame.surfarray.array3d(plain).astype(int)
                        - pygame.surfarray.array3d(written).astype(int)).sum(axis=2)
    columns = np.nonzero((difference > WRITING_DIFFERENCE).sum(axis=1) >= WRITING_COLUMN_PIXELS)[0]
    if len(columns) == 0:
        return 0, plain.get_width()
    return int(columns[0]), int(columns[-1]) + 1


class MugshotDrawing:
    def load_mugshot(self):
        """Loads the two paper pictures once (see render.py); without them, plain drawing."""
        from ui.render import image_file   # here: render.py imports this file
        plain, written = image_file(MUGSHOT_IMAGE), image_file(MUGSHOT_WRITTEN_IMAGE)
        self.mugshot_paper = None
        self.mugshot = None   # (plain paper, written paper) with your photo on, set by take_mugshot()
        if plain is None or written is None:
            return
        self.mugshot_paper = (load_fitted(plain, self.height), load_fitted(written, self.height))
        mask = green_mask(self.mugshot_paper[0])
        xs, ys = np.nonzero(mask)
        if len(xs) == 0:
            self.mugshot_paper = None   # no green rectangle: no idea where the photo goes
            return
        self.photo_rect = pygame.Rect(xs.min(), ys.min(), xs.max() - xs.min() + 1, ys.max() - ys.min() + 1)
        # A see-through sheet that only lets the photo through on the green pixels,
        # so the paperclip on its edge stays on top of the photo.
        cut = mask[self.photo_rect.left:self.photo_rect.right, self.photo_rect.top:self.photo_rect.bottom]
        self.photo_alpha = (cut * 255).astype(np.uint8)
        self.writing_x = writing_columns(*self.mugshot_paper)
        # The picture is narrower than the window: the sides are filled with
        # the colour of its own edges (almost black), so no seam shows.
        edges = pygame.surfarray.array3d(self.mugshot_paper[0])[[0, -1]]
        self.mugshot_back = tuple(int(c) for c in edges.reshape(-1, 3).mean(axis=0))

    def take_mugshot(self, frame, face):
        """
        The moment you lose: cut your face out of the webcam `frame` (BGR,
        unmirrored; None if there is none) and clip it onto the paper.
        face: HeadTracker.face_box(), or None.
        """
        size = self.photo_rect.size if self.mugshot_paper else PLAIN_PHOTO_SIZE
        if frame is None:
            photo = pygame.Surface(size)
            photo.fill(NO_PHOTO_GREY)
        else:
            frame_height, frame_width = frame.shape[:2]
            x, y, width, height = crop_box(face, frame_width, frame_height, size[0] / size[1])
            cut = cv2.resize(frame[y:y + height, x:x + width], size, interpolation=cv2.INTER_AREA)
            cut = cv2.flip(cut, 1)   # mirrored, like the player sees themself everywhere else
            cut = cv2.convertScaleAbs(cut, alpha=PHOTO_BRIGHTNESS)
            rgb = cv2.cvtColor(cut, cv2.COLOR_BGR2RGB)   # OpenCV is BGR, pygame wants RGB
            photo = pygame.image.frombuffer(rgb.tobytes(), size, "RGB").convert()
        if self.mugshot_paper is None:
            self.mugshot = photo
            return
        photo = photo.convert_alpha()
        pygame.surfarray.pixels_alpha(photo)[:] = self.photo_alpha   # only on the green
        papers = []
        for paper in self.mugshot_paper:
            paper = paper.copy()
            paper.blit(photo, self.photo_rect)
            papers.append(paper)
        self.mugshot = tuple(papers)

    def draw_mugshot(self, game):
        """One frame of the mugshot scene (game.scene_time says how far it is)."""
        elapsed = MUGSHOT_SCENE_TIME - game.scene_time
        writing = min(1.0, max(0.0, (elapsed - MUGSHOT_WRITE_DELAY) / MUGSHOT_WRITE_TIME))
        self.screen.fill(BLACK)
        if self.mugshot is None:
            self.take_mugshot(None, None)   # no photo was taken (should not happen): a grey one
        if self.mugshot_paper is None:
            self.plain_mugshot(writing)
        else:
            plain, written = self.mugshot
            self.screen.fill(self.mugshot_back)
            left = (self.width - plain.get_width()) // 2
            self.screen.blit(plain, (left, 0))
            # The written picture, shown from the left up to where the pen is now.
            start, end = self.writing_x
            pen_x = start + int((end - start) * writing)
            if pen_x > start:
                self.screen.blit(written, (left + start, 0), pygame.Rect(start, 0, pen_x - start, self.height))
        # Slowly out of the black at the start, quickly back into it at the end.
        light = min(1.0, elapsed / MUGSHOT_FADE_TIME, game.scene_time / MUGSHOT_OUT_TIME)
        if light < 1:
            self.darken(int(255 * (1 - light)))

    def plain_mugshot(self, writing):
        """Without the paper pictures: the photo in a white frame, the words under it."""
        photo = self.mugshot
        frame = photo.get_rect(center=(self.width // 2, self.height // 2 - 50)).inflate(16, 16)
        pygame.draw.rect(self.screen, WHITE, frame)
        self.screen.blit(photo, photo.get_rect(center=frame.center))
        words = self.hud_big.render("GOT CAUGHT!", True, PLAIN_RED)
        shown = pygame.Rect(0, 0, int(words.get_width() * writing), words.get_height())
        self.screen.blit(words, words.get_rect(midtop=(self.width // 2, frame.bottom + 30)), shown)
