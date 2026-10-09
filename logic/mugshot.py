"""
The mugshot photo: which part of the webcam picture to cut out so the
face sits in the middle of the photo clipped to the exam paper.

main.py takes the webcam picture at the moment you lose (the teacher has
just caught you) and ui/draw_mugshot.py puts the cut-out on the paper.
Only numbers here (no OpenCV, no pygame), so it is tested
(tests/test_mugshot.py).
"""

from settings import MUGSHOT_FACE_ZOOM, MUGSHOT_FACE_LOWER


def crop_box(face, frame_width, frame_height, aspect):
    """
    The part of the frame to cut out, as (x, y, width, height) in pixels.

    face: (left, top, right, bottom) of the face, each 0..1 of the frame
    (HeadTracker.face_box()), or None when no face was found.
    aspect: the photo's width divided by its height (e.g. 0.75 for 3:4).
    The box always has that shape and always stays inside the frame.
    """
    if face is None:
        # No face: the middle of the frame, as tall as it can be.
        height = frame_height
        centre_x, centre_y = frame_width / 2, frame_height / 2
    else:
        left, top, right, bottom = face
        face_height = (bottom - top) * frame_height
        height = face_height * MUGSHOT_FACE_ZOOM
        centre_x = (left + right) / 2 * frame_width
        centre_y = (top + bottom) / 2 * frame_height + MUGSHOT_FACE_LOWER * face_height
    width = height * aspect
    # Too big for the frame: made smaller, keeping its shape.
    shrink = min(1.0, frame_width / width, frame_height / height)
    width, height = width * shrink, height * shrink
    # Moved back inside the frame if it sticks out at a side.
    x = min(max(0.0, centre_x - width / 2), frame_width - width)
    y = min(max(0.0, centre_y - height / 2), frame_height - height)
    return int(x), int(y), int(width), int(height)
