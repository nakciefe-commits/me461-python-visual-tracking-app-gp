# Rules for working on this project

"Don't Get Caught", a webcam game in Python (ME461, team Glitch Please).
Read `README.md` (how to run), `PLAN.md` (design and what is next) and
`NOTES.md` (what changed and why) before changing anything. `LEARN.md`
explains the code for beginners.

## Project facts (do not break these)

- **Linux, Python 3.14**, virtual environment in `.venv/`. Run things with
  `.venv/bin/python …`, install with `.venv/bin/pip install …`.
- Libraries: `opencv-contrib-python`, `mediapipe`, `pygame-ce`, `numpy` (comes
  with mediapipe). No others unless the team agrees.
  - **Never** add `opencv-python`: it conflicts with `opencv-contrib-python`
    (see `NOTES.md` commit #3).
  - `pygame-ce` is imported as `import pygame`. Never install plain `pygame`
    next to it.
- **MediaPipe 1.0** only has the `mediapipe.tasks` API
  (`from mediapipe.tasks.python import vision`). The old `mp.solutions.*` API
  from most tutorials **does not exist**.
- MediaPipe in `VIDEO` mode needs a millisecond timestamp that **strictly
  increases** every frame (`HeadTracker.read()` handles this).
- OpenCV frames are **BGR**; MediaPipe and pygame want **RGB**.
- Run face detection on the **unmirrored** frame; mirror only for display.
- The game must run **without a sound device** (silently) and without the
  sound files (generated beeps instead).

## Code style

- Beginner-friendly: the team are students. Short functions, clear names.
- A docstring at the top of every file saying what it does.
- A short comment on every non-obvious step, saying *why*, in plain words.
- All tuning numbers go in **`settings.py`** as UPPER_CASE constants with a
  comment giving the unit (seconds, degrees, pixels). No magic numbers in the
  other files.
- Game rules (everything in `logic/`) never import pygame or OpenCV, so they
  can be tested without a camera or window. Code is in `logic/` (rules),
  `tracking/` (webcam, head) and `ui/` (drawing, sounds); `main.py` and
  `settings.py` stay at the top.

## Tests

- Rule logic gets `unittest` tests in `tests/`. Run all of them with:
  ```
  .venv/bin/python -m unittest discover -s tests -v
  ```
- Tests read timings from `settings.py` instead of hard-coding them, so tuning
  a number does not break them.
- All tests must pass before committing.
- The webcam and the feel of the game cannot be tested by an agent: list
  exactly what a person should try.

## After every change

1. Run the tests.
2. Add an entry to **`NOTES.md`** in the same format as the others (Summary,
   Added/Changed/Removed tables, Details worth knowing, Next). Next commit
   number, today's date.
3. Update `README.md` if running or playing changed, `LEARN.md` if how the
   code works changed, `PLAN.md` if the design or the to-do list changed.
4. Commit or push only when the team asks. The game is on the
   `dont-get-caught` branch.
