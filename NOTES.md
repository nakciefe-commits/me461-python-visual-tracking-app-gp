# Update notes

ME461 group project by Glitch Please: a visual tracking game written only in
Python and its libraries.

This file is the project's update log. Every commit gets one entry, numbered in
order, newest at the bottom. Read it top to bottom to learn what exists and why.

**Adding an entry:** copy the headings of the last entry, use the next commit
number and today's date, and describe what changed, not how you felt about it.

## Setup and run

```
sudo apt install -y python3-venv            # once per computer, Ubuntu
python3 -m venv .venv                       # create the project's own Python environment
.venv/bin/pip install -r requirements.txt   # install the libraries into it
./run.sh                                    # start the program
```

Quit with `q`, Esc, or the window's X button. The video window must be selected
for the keys to work.

---

## Commit #1 — Added simple body tracker

- **Date:** 30 Sep 2026
- **Hash:** `e99a82a`

### Summary

A program that opens the webcam, finds 33 body joints and draws them as a
skeleton on the live video. Measured at about 25 frames per second on a 640x480
webcam. The game itself is not designed yet; this is the tracking base it will
be built on.

### Added

| File | Purpose |
|---|---|
| `tracker.py` | The program. |
| `run.sh` | Launcher: runs `tracker.py` with the Python in `.venv`. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model (the "full" variant), downloaded from Google. |
| `requirements.txt` | Libraries to install: `opencv-python`, `mediapipe`. |
| `.gitignore` | Keeps `.venv/` and `__pycache__/` out of the repository. |

### How it works

`main()` in `tracker.py` runs one loop, once per webcam frame:

1. `camera.read()` grabs a frame.
2. `find_joints()` passes the frame to MediaPipe and returns 33 joints, or
   `None` if no person is seen. Each joint has `x` and `y` (0.0 to 1.0 across
   the frame, `y = 0` at the top) and `visibility` (0.0 to 1.0).
3. `draw_skeleton()` converts the positions to pixels and draws the bones
   listed in `BONES` as lines and the joints as dots. Joints with visibility
   below `MIN_VISIBILITY` (0.5) are skipped.
4. The frame is mirrored, the FPS counter is drawn, and the frame is shown.

### Details worth knowing

- Joints are addressed by name through `J`, for example `joints[J.LEFT_WRIST]`.
- MediaPipe 1.0 has only the `mediapipe.tasks` API; the older
  `mediapipe.solutions` API used in most online tutorials does not exist in it.
- The detector runs in `VIDEO` mode and needs a timestamp in milliseconds that
  increases with every frame.
- OpenCV frames are BGR and MediaPipe expects RGB, so `find_joints()` converts.
- The frame is mirrored after detection. Mirroring before would swap the left
  and right joint labels.
- Text is drawn after mirroring, otherwise it would be mirrored too.
- The loop checks whether the window is still visible, because OpenCV reopens
  a closed window on the next `imshow` call.
- Set `CAMERA_INDEX` to 1 if the wrong camera opens.

---

## Commit #2 — Added update notes and README

- **Date:** 30 Sep 2026
- **Hash:** `604ed6f`

### Summary

Added the project's documentation. No code changed.

### Added

| File | Purpose |
|---|---|
| `NOTES.md` | Update log with one entry per commit, plus setup and run instructions. |
| `README.md` | The repository's front page: what the project is, who made it, how to set it up and run it. |

---

## Commit #3 — Fixed OpenCV package conflict

- **Date:** 1 Oct 2026

### Summary

The project installed two OpenCV packages that overwrite each other. It now
installs only one. No code changed.

### Changed

| File | Change |
|---|---|
| `requirements.txt` | `opencv-python` replaced with `opencv-contrib-python`. |

### The problem

`requirements.txt` asked for `opencv-python`, but `mediapipe` needs
`opencv-contrib-python`, so pip installed both. The two are the same OpenCV
library: `opencv-contrib-python` is the main package plus extra modules. Both
install into the same `cv2/` folder and share 41 files there, so whichever was
installed last overwrote the other's files. Pip does not warn about this
because the packages have different names.

It worked only because both were the same version. It breaks when:

- one of them is upgraded and the other is not, leaving a `cv2/` folder with
  files from two versions;
- one of them is uninstalled, which deletes the shared files and breaks `cv2`
  for the other one too.

### Details worth knowing

- `opencv-contrib-python` includes everything in `opencv-python`, so the code
  did not need to change.
- Do not add `opencv-python` (or any other OpenCV package) to
  `requirements.txt` again.
- **If you set up `.venv` before this commit**, uninstall both packages, then
  reinstall. Uninstalling only one breaks the other:

  ```
  .venv/bin/pip uninstall -y opencv-python opencv-contrib-python
  .venv/bin/pip install -r requirements.txt
  .venv/bin/python -c "import cv2; print(cv2.__version__)"   # should print a version
  ```

---

## Commit #4 — Added game plan, head tracker and demo

- **Date:** 1 Oct 2026

### Summary

The game is designed (`PLAN.md`, `STEPS.md`) and its first playable demo is
built (steps 0–2 of `STEPS.md`). The webcam now tracks which way the head points
instead of the whole body. The demo has the copying and staring rules, sounds
and a warning popup, drawn with shapes and text. There is no teacher yet, so
you cannot get caught.

### Added

| File | Purpose |
|---|---|
| `PLAN.md` | Game design: rules, teacher, graphics and sound, code structure, demo, future ideas. |
| `STEPS.md` | Step-by-step build instructions, written so an AI agent or a person can follow them. |
| `settings.py` | Every tuning number (angles, times, window size) in one place. |
| `head_tracker.py` | `HeadTracker`: webcam frame → yaw/pitch → `DOWN` / `SCREEN` / `LEFT` / `RIGHT`; also draws the tracked face. `Calibration`: measures the player's neutral angles. |
| `camera.py` | `Camera`: reads the webcam in a background thread, so the game never waits for it. |
| `head_test.py` | OpenCV test window showing the direction and angles, for tuning `settings.py`. |
| `game.py` | `Game`: the rules. Returns events like `"tick"` and `"warning"`. |
| `sounds.py` | `Sounds`: tick, ding, buzz, win and lose sounds, generated with NumPy. |
| `render.py` | `Renderer`: start (with Calibrate button), game, paused and end screens. |
| `main.py` | The main loop and the screen changes. |
| `tests/` | 31 unit tests for the rules, the direction logic and calibration. |
| `face_landmarker.task` | Pre-trained MediaPipe face model (float16), downloaded from Google. |
| `assets/images/`, `assets/sounds/` | Empty folders for the art and sounds. |

### Changed

| File | Change |
|---|---|
| `run.sh` | Starts `main.py` instead of `tracker.py`. |
| `requirements.txt` | Added `pygame-ce`. |
| `README.md` | New status, how to play, files table, tests. |

### How it works

- **Head direction:** the Face Landmarker returns a transformation matrix per
  face. Its third column is the direction the nose points; `atan2` / `asin` of
  it give yaw and pitch in degrees. Angles are smoothed, then compared with the
  calibrated neutral: more than 20° down = `DOWN`, more than 25° sideways =
  `LEFT`/`RIGHT`, else `SCREEN`. A new direction must last 0.2 s
  (`HOLD_TIME`) before it counts, so one shaky frame is not a glance.
- **Copying:** 2.5 s of `LEFT`/`RIGHT` fills one answer; a tick plays every
  0.3 s meanwhile. Looking away resets the progress. After an answer you must
  look away before the next one starts.
- **Staring:** the first 3 s at the screen are free, then the suspicion bar
  fills over 2 s. Full = warning popup + buzz. 3 warnings = game over.
- **Start:** the start screen shows the webcam with the tracking drawn on the
  face. The player clicks **Calibrate** (or presses Space) when ready; 2 s of
  looking at the screen sets the neutral angles.
- **Tracking drawn on the face:** face outline, eyes, irises, lips, and an arrow
  from the nose tip showing where the head points. In the game it is coloured
  like the active option box.
- **No face:** the face often vanishes for a few frames in the middle of a head
  turn. A gap shorter than `FACE_LOST_GRACE` (0.6 s) is ignored: the last
  direction is kept and "face lost..." shows under the preview. Longer than
  that, the game rules are not updated, so everything freezes, and a "Face not
  found" layer is drawn on top.
- **Looking down hides the face:** bent over the paper, the camera mostly sees
  the top of the head and MediaPipe finds no face, for as long as the player
  looks down. So if the face vanishes while it was tilting down (last seen
  more than `LOST_DOWN_PITCH` = 8° below neutral), the direction becomes
  `DOWN` and the game keeps running ("head down" under the preview). This
  cannot be used to cheat: `DOWN` is the safe option and earns nothing.
  `HeadTracker.current_direction()` holds all of these lost-face rules.

### Details worth knowing

- Use `pygame-ce`, imported as `import pygame`. Do not also install plain
  `pygame`: like the two OpenCV packages, they overwrite each other.
- `game.py` has no pygame or OpenCV imports, so its tests run without a
  camera or window. Keep it that way.
- `dt` (seconds since the last frame) is capped at 0.1 s in `main.py`, so a
  frozen frame cannot fill a whole bar at once.
- **Not yet checked with a person in front of the camera.** If left and right
  are swapped, or looking up counts as down, set `YAW_SIGN` / `PITCH_SIGN` to
  `-1` in `settings.py`.
- **Frame rate:** reading a frame takes ~19 ms and face detection ~15 ms.
  Done one after the other, plus drawing, that kept the game under 30 fps.
  With `camera.py` reading in a background thread the loop runs at ~30 fps,
  the webcam's maximum. The fps is shown under the preview.
- MediaPipe's three confidence limits are lowered from 0.5 to 0.3
  (`MIN_FACE_CONFIDENCE`), so it keeps a face that is turned to the side.
- The tests use time steps of 0.125 s because 0.1 added ten times is not
  exactly 1.0 in floating point.
