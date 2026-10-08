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
./run.sh                                    # start the game (first run also installs the libraries)
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

---

## Commit #5 — run.sh installs the libraries

- **Date:** 1 Oct 2026

### Summary

`./run.sh` now sets everything up by itself, so nobody has to run
`pip install` by hand, also not after a `git pull` that adds a library.

### Changed

| File | Change |
|---|---|
| `run.sh` | Creates `.venv` if missing; installs `requirements.txt` when needed; then starts the game. |
| `README.md` | Setup is now only `sudo apt install -y python3-venv`. |

### How it works

After a successful install, `run.sh` copies `requirements.txt` to
`.venv/installed-requirements.txt`. On every start it compares the two files
(`cmp`); only if they differ (first run, or `requirements.txt` changed) does it
run `pip install`. So normal starts are as fast as before and need no internet.

### Details worth knowing

- To force a reinstall, delete `.venv/installed-requirements.txt`.
- If creating `.venv` fails, `run.sh` tells you to install `python3-venv`.
- The first start needs internet and takes a few minutes (MediaPipe is large).

---

## Commit #6 — Simplified the code, added LEARN.md

- **Date:** 1 Oct 2026

### Summary

Same game, less code, so it is easier to learn, plus `LEARN.md`, a guide to
how the code works. Nothing changes for the
player. The game code went from 1,066 to 856 lines (not counting tests and
the old `tracker.py`).

### Added

| File | Purpose |
|---|---|
| `LEARN.md` | Beginner guide: the big picture, key ideas (frames, BGR/RGB, `dt`, events, screens), every file explained, one frame followed step by step, and practice exercises. |

### Removed

| File | Why |
|---|---|
| `head_test.py` | The game now shows everything it did (face drawing, angles, direction), so it was duplicate code. |

### Changed

| File | Change |
|---|---|
| `camera.py` | The background thread just keeps the newest frame in `self.frame`; `read()` returns it. No more `Condition` waiting. Still ~30 fps. |
| `head_tracker.py` | `read(frame, now)` replaces `read_angles(frame, timestamp_ms)`: the tracker makes MediaPipe's millisecond timestamps itself. All lost-face rules are in `current_direction(now, face_found)`, which also sets `status` ("head down", "face lost...") for the screen. Times are in seconds everywhere. |
| `game.py` | `copy_progress` and `suspicion` removed (they were `copy_time` and `stare_time` written differently). `update()` is one function with two clear parts: copying and staring. `WARNING_TIME` = grace + fill time. |
| `sounds.py` | One `tone()` function instead of three; `loop`/`stop` placeholders removed until Step 5 needs them. |
| `render.py` | The suspicion bar is one bar (yellow during the grace time, red after) with a marker line. The popup is drawn by its own `draw_popup()`, called from `main.py`. |
| `main.py` | No timestamp handling; uses `tracker.status` for the note under the preview. |
| `tests/` | Updated for the new names (30 tests). |
| `README.md` | Points to `LEARN.md`; `head_test.py` removed from the files table. |
| `STEPS.md` | "Shared interfaces" matches the new code; Step 4 now says to add `lose_reason` and the `teacher` parameter. |

---

## Commit #7 — The teacher, classroom art, sounds and a docs clean-up

- **Date:** 2 Oct 2026

### Summary

The demo became a real game. A **teacher** now erases the board or plays on
the phone, then turns and watches the class. The game can be lost in three
ways: being **caught** copying, **3 warnings** for staring, or the **exam
clock** (60 s) running out. The teacher is drawn with our own **classroom
pictures**, and the classroom is only visible while the player looks at the
screen. While copying, the player can only *hear* the teacher: Luigi's "hmm"
means the teacher is about to look up. While looking at the paper they hear
nothing at all.

Most of the rules were changed several times while playtesting during the
session; the final rules and the reasons are below. The docs were also
cleaned up: `STEPS.md` is gone, `CLAUDE.md` is new, `PLAN.md` was rewritten.

### Added

| File | Purpose |
|---|---|
| `teacher.py` | The teacher's state machine: `BUSY → TURNING → WATCHING → BUSY`, each lasting a random time from `TEACHER_DURATIONS`. Two places, `BOARD` and `DESK`; after watching, the teacher moves to the other place with chance `MOVE_CHANCE`. `is_watching()`, `is_facing_class()`, `image_name()`, and `sounds(events, can_hear)`, which decides what the player hears. |
| `assets/images/classroom_*.jpeg` | Four classroom pictures, the same room from the same seat: the teacher erasing the board / on the phone at the desk, each also looking at the player. Made with Gemini, then sharpened 4× with Real-ESRGAN and saved at 2048 px wide. |
| `assets/images/original/` | The pictures as Gemini made them (1024 px, blurry), kept in case the sharpening needs redoing. |
| `assets/sounds/luigi-hmm.mp3` | The teacher's turning sound. |
| `assets/sounds/mgs-alert-sound.mp3` | Game over by being caught or by warnings. |
| `assets/sounds/Erasing Chalk On Chalkboard Sound Effect.mp3` | Not used yet; meant as a loop while the teacher erases the board. |
| `tests/test_teacher.py` | 14 tests: state order, durations, places, the caught grace, picture names, the picture files exist, and what the player hears. |
| `CLAUDE.md` | The "rules for every step" from `STEPS.md` (project facts, code style, tests, what to update after a change), now in the file Claude Code reads automatically. |

### Removed

| File | Why |
|---|---|
| `STEPS.md` | 707 lines of instructions for an AI agent. Steps 0–4 are done (and recorded here in `NOTES.md`), steps 5–9 repeated the roadmap in `PLAN.md`, and the rules moved to `CLAUDE.md`. Five docs had grown to ~1,900 lines with a lot of repetition. |

### Changed

| File | Change |
|---|---|
| `game.py` | `update(direction, dt, teacher=None)`. New `time_left` (exam clock) and `lose_reason` (`"warnings"`, `"caught"`, `"time"`). Losing emits `"lost"` plus `"lost_<reason>"`, so each way of losing can have its own sound. `stare_time` is replaced by one **`suspicion_level`** (0..1, read with `suspicion()`), see "The suspicion bar" below. The copy bar now keeps its progress when you look away, and does not move while the teacher sees you. A `"spotted"` event (alarm) starts each seen glance. Without a teacher it works as before. |
| `render.py` | The game screen is the classroom picture (scaled and cropped by `load_classroom()`) with see-through strips: answers, warnings and the exam clock (red under 15 s) at the top, the copy and suspicion bars at the bottom, a smaller webcam preview on the right. Black screen with "You can't see the teacher - listen!" while looking away. End screen text depends on `lose_reason`. The three option boxes and the big title are gone. |
| `main.py` | Updates the teacher every frame (frozen with the game while paused), passes its events through `teacher.sounds()`. `classroom_view()` gives the fade-in from black. `d` key: always show the classroom and write the teacher's state (for testing). The end screen always shows the classroom, so a caught player sees the teacher looking at them. |
| `sounds.py` | `SOUND_FILES` table: a sound name → a file in `assets/sounds/`, replacing the generated beep of that name (kept as a fallback if the file is missing). New beeps: `spotted` (rising alarm). `lost` split into `lost_time` (falling notes); `lost_caught` and `lost_warnings` use the MGS file. Removed: the `caught` buzz (it played on top of the game-over sound) and a "teacher is busy again" beep (it gave away when it was safe). |
| `settings.py` | New: `EXAM_TIME`, `TEACHER_DURATIONS`, `MOVE_CHANCE`, `CAUGHT_GRACE`, `CAUGHT_TIME`, `STARE_ONLY_WHEN_FACING`, `SUSPICION_DRAIN_TIME`, `FADE_TIME`, `CLASSROOM_TOP`. Tuned values in the table below. |
| `tests/test_game.py` | Tests with a `FakeTeacher`: caught, escaping in time, glances adding up, no copying while seen, the shared suspicion bar, slow draining, the staring rule, exam clock, pause, copying in pieces, lose events. Times are read from `settings.py` and the helpers run *at least* the given time, so tuning a number no longer breaks the tests. |
| `tests/test_head_tracker.py` | The thresholds and hold time come from `settings.py` instead of being written in the tests. |
| `PLAN.md` | Rewritten to match the game as it is now (rules, teacher, sounds, art, code structure), with the open questions updated (Q2, Q4, Q5 decided), a "Done and next" list that replaces `STEPS.md` steps 5–9, and future ideas. The finished demo section was removed. |
| `LEARN.md` | New `teacher.py` section; `game.py`, `sounds.py`, `render.py`, `main.py` and "Follow one frame" describe the new code; numbers updated; an exercise that pointed at removed code replaced. |
| `README.md` | How to play with the teacher and sounds, the files table (assets, `CLAUDE.md`, no `STEPS.md`). |

### Tuned settings

| Setting | Was | Now | Why |
|---|---|---|---|
| `SMOOTHING` | 0.4 | 0.8 | Faster reaction to head turns. |
| `HOLD_TIME` | 0.2 s | 0.1 s | Faster reaction; 0.2 s felt laggy. |
| `PITCH_DOWN_THRESHOLD` | 20° | 28° | Tuned by the team at the desk. |
| `YAW_THRESHOLD` | 25° | 18° | You had to turn too far to copy. |
| `COPY_TIME` | 2.5 s | 3.0 s | The game was too easy. |
| `EXAM_TIME` | (new) | 60 s | 90 s was too easy. |
| Teacher `BUSY` | (new) | 3.5–6.5 s | 4–8 s was too easy, 2.5–5 s changed too often. |
| Teacher `TURNING` | (new) | 0.2 s | Started at 1 s; the "hmm" felt too far ahead of the danger. |
| Teacher `WATCHING` | (new) | 4–7 s | Longer so the teacher changes less often. |
| `CAUGHT_GRACE` | (new) | 0.1 s | 0.3 s left too long a gap after the "hmm". |
| `CAUGHT_TIME` | (new) | 0.9 s | Time to react to the alarm; 0.7 s was a bit too harsh. |
| `SUSPICION_DRAIN_TIME` | (new) | 8 s | Slow enough that the bar doesn't give the teacher away. |
| `FADE_TIME` | (new) | 0.15 s | Started at 0.3 s; shorter so looking up feels instant. |

### How the rules got here, and why

- **The classroom is only visible while looking at the screen.** Turning the
  head 18° still lets you see the monitor from the corner of your eye, so
  without this you could copy and watch the teacher at once. We tried a blur
  and a grey screen; black is the only one that gives nothing away. Looking
  back fades the classroom in (like eyes refocusing); looking away is black
  at once, so there is no last glimpse.
- **Sound tells you about the teacher, but only when your head is up.**
  Looking at the paper is safe, so it must cost something: you see and hear
  nothing there. If you look up while the teacher is still turning, you hear
  the "hmm" late (once per turn), so looking up is never punished.
- **No sound when the teacher is busy again.** A "safe" sound made it too easy:
  you could copy without ever looking. Now you have to look.
- **Being seen is not instant game over.** While copying you are looking
  away, and you may miss the "hmm". So being seen starts an alarm and fills
  the suspicion bar fast (0.9 s); look away in time and you escape.
- **No copying while seen.** Otherwise you could "look, look away, look
  again" while the teacher watches and still fill answers, always just
  before the bar was full. Now glancing while watched is all risk, no gain.
- **One suspicion bar.** It used to be two counters (staring, being seen)
  and the bar showed the bigger one, so staring after being seen made the bar
  stop. Now both add to the same bar.
- **The bar drains slowly instead of resetting.** A bar that jumps to empty
  tells the player exactly when the teacher looked away.
- **Copying in pieces (PLAN Q2).** Losing all progress when you looked away
  felt unfair once the teacher could interrupt you; now the copy bar keeps
  its progress.
- **Different game-over sounds.** The MGS alert fits being caught and being
  warned out; running out of time is a different kind of failure.

### Details worth knowing

- **Why `TURNING` has no picture:** the teacher has not looked up yet, so the
  busy picture stays. The warning is the sound, because the player who needs
  it is looking away from the screen.
- **The pictures are cropped to fit the window:** scaled to 960 px wide, then
  `CLASSROOM_TOP` px cut off the top (ceiling) and the rest off the bottom.
- **Sharpening the pictures** was done once by hand with
  `realesrgan-ncnn-vulkan -n realesrgan-x4plus` (downloaded separately, not
  part of the project), then shrunk to 2048 px and saved as JPEG quality 95.
  A 4× PNG was 27 MB; the JPEG is ~0.9 MB.
- **The teacher can change place while you look:** after watching, a move
  to the other place is an instant picture swap. Usually you are looking away
  then.
- **The suspicion bar can still hint a little:** it stops rising when the
  teacher stops watching, and you can see the bar on the black screen.
- **`d` key** keeps the classroom visible and writes the teacher's state on
  screen: the quickest way to test the timings.
- **Sound files are clips from Nintendo (Luigi) and Konami (Metal Gear).**
  Fine for a class project; check the licences before publishing the game
  anywhere else.
- 62 tests, all passing. Not tested by the agent: the webcam, the feel of the
  timings, and the sounds on real speakers.

### Next

1. Playtest with the whole team and tune `settings.py` (teacher durations,
   `COPY_TIME`, `EXAM_TIME`, `CAUGHT_TIME`). If it feels easy, try
   `COPY_TIME` 3.5.
2. Use the chalk sound as a loop while the teacher erases the board (needs
   `loop()`/`stop()` in `sounds.py`).
3. Pictures for looking down (your paper) and sideways (the neighbour's
   paper) instead of the black screen.
4. Menus, difficulty and score: see `PLAN.md` section 8.

---

## Commit #8 — Simplified main.py and render.py

- **Date:** 3 Oct 2026

### Summary

Small clean-up with **no change to how the game plays or looks**. The code
was already short; this removes the few places where the same thing was
written twice.

### Changed

| File | Change |
|---|---|
| `main.py` | GAME and END are one branch: both drew the face and the game screen with almost the same call. END now skips the update and passes `view = 1.0` and an empty tracking note, as before. Space (start screen) and `c` (in game) share one "start calibrating" branch. Removed a stale comment about the option boxes, which no longer exist. |
| `render.py` | `draw_start()` picks the message and colour first, then draws once instead of three copies of the same `text()` call. `draw_game()` reads `game.suspicion()` once. |
| `LEARN.md` | The `main.py` section says END shares the GAME branch. |

### Details worth knowing

- 62 tests, all passing. The screens were also drawn once without a window
  (SDL dummy driver) to check nothing crashes. Not tested by the agent: the
  real game with a webcam. A person should check: Space and the Calibrate
  button start calibration, `c` recalibrates during a game, the pause screen
  appears when you leave the camera, and the end screen shows the classroom
  with the win/lose text.
- The `windows` branch (Windows launcher) also uses the number #8 in its
  NOTES entry. If it is merged later, renumber one of them.

### Next

Same as commit #7.

---

## Commit #9 — Disclaimer screen

- **Date:** 3 Oct 2026

### Summary

The game now opens with a satirical **WARNING** screen: the game is not
real life, any resemblance to real exams or professors is coincidental, it
is only for fun, and we love our professor and respect academic honesty.
Space or a click goes on to the start screen. It is shown once per launch;
`r` goes back to the start screen, not to the disclaimer.

### Changed

| File | Change |
|---|---|
| `main.py` | New first screen `DISCLAIMER`. Space or a mouse click anywhere moves on to `START`. The disclaimer check comes before the "Space = calibrate" check, so one press does not skip both screens. |
| `render.py` | `DISCLAIMER_LINES` (text and colour per line) and `draw_disclaimer()`. |
| `README.md` | Mentions the warning screen. |
| `LEARN.md` | The screen diagram, the `render.py` screen list and the `main.py` loop include the disclaimer. |

### Details worth knowing

- The text is in `DISCLAIMER_LINES` in `render.py`: change the wording there.
  At font size 34 a line can be about 80 characters before it is wider than
  the 960 px window (the longest line now is 743 px).
- While the disclaimer is shown, only Space, a click and `q`/Esc do
  anything; `r`, `c` and `d` are ignored.
- 62 tests, all passing; the screen was drawn without a window and checked
  as a picture. A person should check: the game opens on the warning, Space
  goes to the start screen (and does **not** start calibrating), a click
  does the same, and `q` still quits.

### Next

Same as commit #7.

---

## Commit #10 — Maximized window and F11 fullscreen

- **Date:** 5 Oct 2026

### Summary

The game now opens as a normal window (title bar and taskbar still visible)
that is maximized to fill the screen and can be resized. The game is still
drawn at 960×600 and pygame stretches it to fit, with black bars so nothing
is squashed. F11 switches to a borderless window covering the whole screen
and back.

### Added

| File | Change |
|---|---|
| `settings.py` | `FULLSCREEN = False`: start in a normal window (True = borderless fullscreen). `MAXIMIZED = True`: the normal window starts maximized. |
| `main.py` | `open_window(fullscreen)` opens the window with `pygame.SCALED`, plus `pygame.FULLSCREEN`, or `pygame.RESIZABLE` and a `maximize()` call. F11 calls it again with the other mode. |

### Changed

| File | Change |
|---|---|
| `README.md` | F11 key and the `FULLSCREEN` / `MAXIMIZED` settings. |
| `LEARN.md` | How the window is scaled, in the `main.py` section. |

### Details worth knowing

- The first version opened borderless fullscreen by default; the team
  wanted a maximized window with the title bar instead, so that is now the
  default and fullscreen is behind F11.
- Maximizing uses `pygame.Window.from_display_module().maximize()` (pygame-ce
  2.5+); `set_mode()` has no flag for it.
- `SCALED | FULLSCREEN` uses SDL's "desktop fullscreen": the monitor keeps
  its resolution, so Alt-Tab and other windows still work, unlike real
  exclusive fullscreen.
- `SCALED` also converts mouse positions, so the Calibrate button still
  works without changes in `render.py`.
- F11 calls `set_mode()` again instead of `pygame.display.toggle_fullscreen()`,
  because the toggle is not supported by every video driver (it fails with
  the dummy driver). The surface stays 960×600, so the renderer keeps working.
- Tests: all 62 pass (after the fix in commit #11). Opening and
  switching the window was checked without a screen (SDL dummy driver).
  A person should check: the game opens maximized with its title bar and
  the taskbar visible, dragging the window smaller still shows the whole
  game, F11 switches to borderless fullscreen and back (maximized again), the Calibrate button
  still reacts to clicks in both modes, and `q`/Esc still quits.

### Next

Same as commit #7.

---

## Commit #11 — Tuning and two test fixes

- **Date:** 5 Oct 2026

### Summary

New tuning numbers in `settings.py` after play-testing. Two tests broke with
them: one had a time written into it, the other showed a rounding bug where
the suspicion bar could stop just below full. Both are fixed; all 62 tests
pass.

### Changed

| File | Change |
|---|---|
| `settings.py` | `MIN_FACE_CONFIDENCE` 0.3 → 0.4, `PITCH_DOWN_THRESHOLD` 28 → 23, `COPY_TIME` 3 → 5 s, `STARE_GRACE_TIME` 3 → 2 s, `STARE_FILL_TIME` 2 → 1 s, `EXAM_TIME` 60 → 80 s, `CAUGHT_TIME` 0.9 → 0.7 s, `SUSPICION_DRAIN_TIME` 8 → 10 s. |
| `game.py` | The bar counts as full from `FULL = 1 - 1e-9` instead of exactly 1. |
| `tests/test_game.py` | `test_looking_down_drains_slowly` stares for `WARNING_TIME / 2` instead of a fixed 4 s, which is longer than the new `WARNING_TIME` (3 s). |

### Details worth knowing

- Adding `dt / 3.0` 24 times gives 0.99999…, not 1, so the warning came one
  frame late. Any `WARNING_TIME` or `CAUGHT_TIME` that is not a power of two
  can do this; `FULL` absorbs the rounding. In play it was one frame, so
  only the test noticed.
- A person should check that the new numbers feel right: copying an answer
  takes 5 s, staring at the screen gives a warning after 3 s, and looking
  down counts at a smaller head tilt.

### Next

Same as commit #7.

---

## Commit #12 — Pictures for looking down, left and right

- **Date:** 6 Oct 2026

### Summary

The instructor asked for pictures instead of the black screen while the
player looks away. Looking down now shows your own exam paper, looking left
or right shows that neighbour copying their exam. None of them show the
teacher, so you still have to look at the screen (or listen) to know what
the teacher is doing.

### Added

| File | Change |
|---|---|
| `assets/images/classroom_desk_looking_down.jpeg` | Your desk from above: the spiral exam paper, hands, pencil, breadboard. |
| `assets/images/classroom_desk_looking_left.jpeg` | The left neighbour (curly hair, beige t-shirt) writing on their exam. |
| `assets/images/classroom_desk_looking_right.jpeg` | The right neighbour (maroon t-shirt, calculator) writing on their exam. |
| `render.py` | `LOOK_AWAY_IMAGES`: direction → picture. `LOOK_AWAY_STRIP`: height of the text strip, pixels. |
| `tests/test_teacher.py` | `test_images_exist` also checks the three new pictures. |

### Changed

| File | Change |
|---|---|
| `render.py` | `draw_game` draws the look-away picture instead of black. The "Copying from the left" text moved from the middle to a dark strip above the bars, so it does not cover the neighbour's paper. Looking down now says "You can't see or hear the teacher" (you really hear nothing then). |
| `README.md`, `LEARN.md`, `PLAN.md` | The screen is no longer black while looking away; PLAN section 5 says how the pictures were made. |

### Details worth knowing

- The pictures were made with Gemini by giving it
  `original/classroom_board_busy.jpeg` and asking for the same room,
  style and students from the same seat. Making them from text only would
  give a different classroom each time. They are 2048×2048.
- They go through the same `load_classroom()` as the teacher pictures, so
  only about 26%–89% of the height is shown. Their important part is in
  that band.
- The first moment after turning back to the screen is still black, then
  the classroom fades in (`FADE_TIME`), as before.
- The right picture shows part of the board but not the teacher. That is
  fine: the board alone says nothing about the teacher.
- Tests: all 62 pass. The three screens were drawn without a window (SDL
  dummy driver) and checked by eye. A person should check: looking left
  shows the curly-haired neighbour and looking right shows the one with the
  calculator (if they are swapped, the camera's left/right is flipped:
  `YAW_SIGN`); looking down shows your paper; the text strip does not cover
  the neighbour's paper; the copy bar is still readable on top.

### Next

Same as commit #7, minus the look-away pictures.

---

## Commit #13 — A-D answers: read from a neighbour, write on your paper

- **Date:** 6 Oct 2026

### Summary

Copying no longer fills an answer by itself. Each question has a right
letter (A, B, C or D), and only one neighbour, chosen at random, knows it.
Looking at a neighbour until the copy bar is full **reads** their paper: a
note above it shows the letter, or "?" if they don't know it (then the other
neighbour does). The player must remember the letter, look down at their own
paper and press A-D to **write** it. After 5 answers the exam is handed in
and the end screen shows the grade (e.g. 4/5 correct). This answers open
question Q1 in `PLAN.md`.

### Added

| File | Change |
|---|---|
| `game.py` | Answer key `right_letters` / `knowing_side` (random at `reset()`), `written`, `read_sides`. `paper_shows(side)`, `can_write()`, `write(letter, direction)`, `correct_count()`, `question()`. `Game(rng)` takes a `random.Random` like `Teacher`. `LETTERS`, `UNKNOWN`. |
| `main.py` | `LETTER_KEYS`: A/B/C/D call `game.write()`. |
| `render.py` | `answer_boxes()` (letters in the boxes; green/red at the end), `neighbour_note()` (the white note with the letter or "?"), `look_away_texts()` (hints), the letters handwritten on your paper. `PAPER_SPOT`, `NOTE_SIZE`, `OWN_ANSWER_X`, `OWN_ANSWER_Y`: pixel positions in the pictures. |
| `sounds.py` | `"read"` (ding, was `"answer"`), `"write"` (a short pencil scratch made from random noise). |
| `tests/test_game.py` | 13 copying tests for reading, "?", writing only while looking down and after reading, separate progress per side, wrong letters graded, the random key. 69 tests now. |

### Changed

| File | Change |
|---|---|
| `game.py` | `copy_time` is one number per side (`{LEFT: .., RIGHT: ..}`); halves from two sides do not add up. `answers` is now `len(written)`. `copy_locked` is gone: a paper already read gives nothing more anyway. Winning = 5 answers written. |
| `main.py`, `render.py` | Keys: recalibrate `c` → `k`, testing view `d` → `t`, because C and D are answers now. |
| `render.py` | While looking down the text strip is at the top, so it does not hide answer lines 4 and 5. End screen: "Exam handed in!" and the grade. |
| `settings.py` | Comments of `ANSWERS_NEEDED` and `COPY_TIME`. |
| `README.md`, `LEARN.md`, `PLAN.md` | The new way of answering, the keys, the grade. |

### Details worth knowing

- Decided with the team: any letter can be written (wrong ones only lower
  the grade), but only after the answer was read, so guessing without
  copying is not possible. The letter is **not** shown while looking down:
  remembering it is part of the game.
- Each neighbour is random per question, so a side can know several answers
  in a row; nothing forces a mix.
- Writing is checked with the direction from the last frame, so a key
  pressed while turning down may be ignored for a moment.
- `test_win_on_last_second_is_a_win` now writes the last answer in the last
  frame of the exam, because filling the bar no longer wins by itself.
- Tests: all 69 pass. The look-left, look-right, look-down and end screens
  were drawn without a window and checked by eye. A person should check:
  the note sits above each neighbour's paper; "?" really comes from one side
  and the letter from the other; A-D do nothing while not looking down or
  before reading; letters appear on the right lines of your paper; K
  recalibrates and T shows the teacher; the end screen colours the boxes.

### Next

- The team's funny sound for wrong answers (on the end screen).
- Maybe a pass mark (e.g. 3/5) so a bad grade is not a win.
- Then the rest of commit #7's list.

---

## Commit #14 — Neighbour pictures with the answer on their paper

- **Date:** 6 Oct 2026

### Summary

The white note with the letter is replaced by pictures: once the copy bar
is full, the neighbour's picture changes to one where the letter (A-D) or a
"?" is circled on their exam sheet. Before the bar is full the plain picture
is shown, so the answer cannot be seen early.

### Added

| File | Change |
|---|---|
| `assets/images/left_A … left_D.jpeg`, `left_unknown.jpeg` | The left neighbour with that letter (or "?", scratching her head) on her sheet. Made with Gemini from `classroom_desk_looking_left.jpeg`. |
| `assets/images/right_A … right_D.jpeg`, `right_unknown.jpeg` | The same for the right neighbour. |
| `render.py` | `PAPER_IMAGES`, `SIDE_NAMES`, `neighbour_picture(game, side)`: which picture to show. |
| `tests/test_game.py` | `test_nothing_shown_until_the_bar_is_full`: one frame before full, still hidden. |
| `tests/test_teacher.py` | `test_images_exist` also checks the 10 paper pictures. |

### Changed

| File | Change |
|---|---|
| `render.py` | Looking sideways draws `neighbour_picture()`. The white note (`neighbour_note()`) is only a fallback for a missing picture. |
| `assets/images/left_?.jpeg`, `right_?.jpeg` | Renamed to `left_unknown.jpeg`, `right_unknown.jpeg`: `?` in a file name breaks on Windows and in the shell. |
| `README.md`, `LEARN.md`, `PLAN.md` | The new pictures. |

### Details worth knowing

- The picture only depends on `game.paper_shows(side)`, which stays `None`
  until the copy bar is full, so the answer cannot leak early. The new test
  checks the last frame before full.
- `left_A` and `right_A` are 1024 px (not sharpened); the others 2048 px.
  They still fill the window, just a bit softer. Sharpen them with
  Real-ESRGAN like the others when there is time.
- In the right "?" picture the circle sits just above the text strip; check
  it is not covered.
- Tests: all 70 pass. Drew the left picture one frame before full (plain),
  at full (`left_C`), and the right "?" (`right_unknown`) without a window
  and checked them by eye. A person should check: the letter on each
  picture is readable on your screen, it only appears when the bar is full,
  and the wrong-side neighbour shows "?".

### Next

Same as commit #13.

---

## Commit #15 — Neon main menu controlled by the head

- **Date:** 7 Oct 2026

### Summary

The game now has menus in a neon 80s style, like the game Hotline Miami: a
main menu (Play, How to play, Settings, Quit), a how-to-play screen, a
settings menu and a menu on the end screen (Play again, Main menu, Quit).
They are controlled with the head: tilt up/down to move the selection, turn
right and hold to choose, turn left and hold to go back. Arrow keys, Enter,
Esc and the mouse work too. After calibrating, the game opens the main menu
instead of starting straight away.

### Added

| File | Change |
|---|---|
| `menu.py` | `Menu` (items and the selected one, wraps around), `HeadMenuInput` (head angles → `UP` / `DOWN` / `SELECT` / `BACK`, with hold times and a "straight first" rule), `next_choice()`. No pygame, so it is tested. |
| `render.py` | `draw_menu()`, and the helpers `menu_background()` (gradient, turning rays, scanlines), `neon_text()`, `blit_turned()`, `menu_title()`, `menu_items()`, `menu_footer()`, `menu_font()`, `mix()`. `HELP_LINES`, the menu colours and the animation numbers (`BEAT_TIME`, `TITLE_WOBBLE`, ...). |
| `settings.py` | `MENU_PITCH_THRESHOLD`, `MENU_YAW_THRESHOLD`, `MENU_MOVE_HOLD`, `MENU_REPEAT_TIME`, `MENU_SELECT_TIME`, `EXAM_TIME_CHOICES`. |
| `sounds.py` | `"menu_move"` (blip) and `"menu_select"` (two notes) beeps; `muted`. |
| `tests/test_menu.py` | 14 tests: moving and wrapping, the poses, hold times, repeating, a glance does not choose, one long turn chooses once, nothing before the head was straight, `next_choice()`. |
| `tests/test_game.py` | `test_exam_time_from_the_settings_menu`. 85 tests now. |

### Changed

| File | Change |
|---|---|
| `main.py` | The loop is now inside a class `App` with one method per job (`go_to`, `start_game`, `calibrate_then`, `menu_action`, `choose`, `handle_key`, `handle_click`, `start_screen`, `menu_screen`, `game_screen`, `run`), because the menus need to share a lot of state. New screens `MENU`, `HELP`, `SETTINGS`. Calibrating leads to `after_calibration`: the main menu at the start, the game after `k`, settings after "Recalibrate". `r` starts a new game straight away (no recalibrating); `m` goes to the main menu. Esc goes back in the menus and quits on the main menu and in the game. |
| `game.py` | `Game(rng, exam_time)`: `self.exam_time` is used by `reset()`, so the settings menu can change it. |
| `render.py` | `draw_end()` takes the menu labels and draws the result higher up with the menu under it. |
| `README.md`, `LEARN.md`, `PLAN.md` | The menus, the new screens, the keys, `menu.py`. |

### Details worth knowing

- The head needs calibration to know what "straight" is, so the main menu
  comes after the start screen, not before it.
- Tilting up uses a smaller angle (12°) than looking down in the game (23°):
  tilting the head up far is uncomfortable and makes the face harder to
  track.
- After a choice, and when a menu opens, the head must come back straight
  before the next action. Without that, being caught while looking sideways
  would start choosing on the end menu at once.
- The menu font: Impact if the computer has it (Windows), else Arial Black,
  else DejaVu Sans Bold (most Linux), slanted by pygame. It is not shipped
  with the game, so it can look a bit different on each computer.
- The settings are not saved: they go back to `settings.py`'s values when
  the game restarts. The exam time chosen is used from the next game on.
- The uncommitted `EXAM_TIME = 200` in `settings.py` was left as it was.
- Drawing one menu frame takes about 2 ms, so 30 fps is easy.
- Tests: all 85 pass. Drew the main, how-to-play, settings and end menus
  without a window and checked them by eye. Ran the real loop with a fake
  camera and keys: disclaimer → start → main menu → how to play → back →
  settings (exam time, sound) → back → play → game over → main menu → quit.
  A person should check, with the webcam: tilting up/down moves the
  selection one step at a time and repeats when held; turning right fills
  the bar and chooses; turning left goes back; a quick glance chooses
  nothing; entering the end menu while turned sideways does not choose by
  itself; the mouse hover and clicks hit the right items; fullscreen and
  sound settings work; the title does not get cut off on your screen.

### Next

- Menu music (a synthwave loop would fit), needs `loop()`/`stop()` in
  `sounds.py`.
- Save the settings to a file so they are kept between runs.
- Maybe a sensitivity setting for the head thresholds.
- Then the rest of `PLAN.md` section 8.

---

## Commit #16 — Loading screen and a neon game interface

- **Date:** 7 Oct 2026

### Summary

Choosing Play no longer drops the player straight into the exam: a
3-second "chapter" screen comes first, like the ones in Hotline Miami
("ME461 - CHAPTER 1", "THE MIDTERM", today's date, a funny loading line and
a bar). The rest of the interface now matches the menus: the disclaimer and
start screens have the neon background, and in the game the strips, bars,
texts, warning popup, pause screen and end screen are in the same neon
style.

### Added

| File | Change |
|---|---|
| `render.py` | `draw_loading()`, `LOADING_CHAPTER`, `LOADING_TITLE`, `LOADING_TIPS`, `TIPS_PER_LOADING`. Helpers `shadow_text()`, `hud_strip()`, `shout()`, `beat()`. `self.t`, the animation time. Colours `NEON_GREEN`, `NEON_RED`, `HUD_PURPLE`; `HUD_ALPHA`, `HUD_LINE`, `FOOTER_HEIGHT`, `TEXT_SHADOW`, `TEXT_WOBBLE`, `CLOCK_PULSE`. |
| `main.py` | Screen `LOADING`; `loading_screen()`, `begin_playing()`. |
| `settings.py` | `LOADING_TIME` (3 s). |

### Changed

| File | Change |
|---|---|
| `render.py` | Disclaimer and start screens: neon background, slanted Calibrate button. Game: purple strips with a pink edge, slanted bars (`bar()` draws a parallelogram), bold slanted labels, neon answer boxes and warning circles, a neon clock that turns pink and thumps every second under 15 s. Popup: a band across the screen with wobbling text. Pause and end screens: big neon text. `draw_menu()` and `draw_end()` no longer take `t` (they use `self.t`). `menu_footer()` is now `footer(hint)`, used by every neon screen. Removed the colours nothing used any more (`BACKGROUND`, `DARK_GREY`, `GREEN`, `RED`, `BLUE`). |
| `main.py` | `start_game()` shows the loading screen; `begin_playing()` does what `start_game()` did. Sets `renderer.t` every frame. |
| `render.py` | While looking down, the text strip is centred left of the webcam preview, which covered the end of the line. |
| `render.py` | The Calibrate button is sized from its text (`BUTTON_TEXT`, `BUTTON_PADDING`, `BUTTON_HEIGHT`) instead of a fixed 300 px, so the text no longer touches its slanted ends. |
| `README.md`, `LEARN.md`, `PLAN.md` | The loading screen and the neon style. |

### Details worth knowing

- The loading screen is shown for Play, Play again and `r`, but not after
  `k` (recalibrating in the middle of a game goes straight back to it).
- During loading the game, the teacher and the clock do not move; the game
  is reset only when loading ends.
- The top strip measures its labels (`ANSWERS`, `WARNINGS`) and places the
  boxes, circles and clock after them, because the menu font differs
  between computers (Impact, Arial Black or DejaVu Sans Bold).
- The yaw/pitch/fps numbers stay in the plain font: they are for testing.
- Tests: all 85 pass (no rule changed). Drew every screen without a window
  (disclaimer, start, calibrating, loading, game, popup, looking left and
  down, paused, won, lost) and checked them by eye; ran the real loop with
  a fake camera from the disclaimer through loading, a game, the end menu
  and quit. A person should check: the loading screen feels the right
  length; the game texts are readable on top of every classroom picture;
  the clock's thumping in the last 15 s is not too distracting; the
  warning banner does not hide something important.

### Next

Same as commit #15.

---

## Commit #17 — The teacher comes over after a warning

- **Date:** 7 Oct 2026

### Summary

A warning is no longer just a red box: the teacher walks up to your desk
and points at you angrily. The screen zooms into the teacher's picture
(faster and faster, like someone walking at you), then shows them at your
desk pointing their index finger at you, the screen shakes and flashes red,
and "WARNING 1/3" and "STOP STARING AT ME!" appear. The game is frozen for
the 2.5 s of the scene. The picture (`classroom_warning.jpeg`) was made by
the team with Gemini.

### Added

| File | Change |
|---|---|
| `game.py` | `scene_time` and `in_scene()`: while the scene plays, `update()` only counts it down. `can_write()` is False during it. |
| `assets/images/classroom_warning.jpeg` | The teacher (with his camouflage bandana) two metres in front of your desk, pointing at you angrily. Made with Gemini from the two "watching" originals; the prompt is in `PLAN.md` section 5. |
| `render.py` | `draw_warning_scene()`, `zoomed()`. `POINTING_IMAGE` (the picture above; optional), `POINTING_TOP` (its own top cut), `TEACHER_FACE` (where the teacher's face is in each watching picture), `APPROACH_ZOOM`, `FLASH_TIME`, `SHAKE_PIXELS`, `SHAKE_TIME`. `load_classroom()` takes a `top`. |
| `settings.py` | `WARNING_SCENE_TIME` (2.5 s), `TEACHER_APPROACH_TIME` (0.8 s). |
| `tests/test_game.py` | `test_warning_scene_freezes_the_game`, `test_last_warning_scene_plays_before_game_over`. 87 tests now. |

### Changed

| File | Change |
|---|---|
| `main.py` | The teacher does not move during the scene; the scene is drawn instead of the popup; the end screen waits until the last warning's scene is over; the classroom fades in again after it. |
| `game.py` | The scene check comes before the game-over check in `update()`, so the scene of the last warning plays. |
| `tests/test_game.py` | The three-warnings tests stare for `ALL_WARNINGS_TIME` (from `settings.py`) instead of a fixed 15 s, which would break when the scene time is tuned. `test_popup_disappears` waits for the scene. |
| `README.md`, `LEARN.md`, `PLAN.md` | The warning scene and the picture to make. |

### Details worth knowing

- Freezing the game is on purpose: during the scene you cannot see the
  classroom, so the clock and the bars must not run against you.
- The zoom uses the "watching" picture of wherever the teacher is (board
  or desk); `TEACHER_FACE` holds the pixel spots of their faces, measured on
  the 960×600 window. If the pictures change, measure them again.
- The pointing picture is cut less at the top (`POINTING_TOP` 120 instead
  of `CLASSROOM_TOP` 250): with the normal cut the bandana touched the top
  of the window and the "WARNING" strip covered the face.
- First tries: the picture faded in over the end of the zoom, but for a
  moment two teachers were seen on top of each other. Now it is a hard cut
  at the moment of arrival, hidden by a white flash (`FLASH_TIME`), like
  the cuts in Hotline Miami. `APPROACH_ZOOM` is 3.5 so the zoomed teacher is
  about as big as in the picture.
- The first Gemini picture was too close and had a cap instead of the
  bandana; the prompt in `PLAN.md` now says both.
- The "warning" buzz still plays when the scene starts. An angry voice file
  could replace it in `SOUND_FILES`.
- Tests: all 87 pass. Drew the scene at several moments (walking, arrived,
  at the board and at the desk, with a placeholder pointing picture) and
  checked them by eye. Ran the real loop: after the last warning the screen
  stays on the scene, the teacher does not move, and the end screen comes
  after it. A person should check: the zoom feels like the teacher walking
  over; 2.5 s is not too long to wait; the shake and the white flash are
  not too strong.

### Next

- An angry voice for the warning (in `SOUND_FILES`, replacing the buzz).
- Then the list of commit #15.

---

## Commit #18 — Caught scene and a game over screen with two talking logos

- **Date:** 7 Oct 2026

### Summary

Getting caught now plays a scene: the teacher freezes with a big red Metal
Gear "!" over his head (the MGS alert was already playing), then a white
flash, a paper-ripping sound, and the teacher tears up your exam ("CAUGHT
COPYING!" / "YOUR EXAM: 0/5 - SEE YOU NEXT SEMESTER"). After every loss a
GAME OVER screen follows: on black, the Gemini and Claude logos, drawn in
code with cartoon faces, make fun of you in a two-line chat that depends on
how you lost (e.g. "Maybe try looking at the teacher during class, not
during the quiz."), with a "nooo" sound. Space skips it. The
loading screen now says "THE QUIZ" instead of "THE MIDTERM".

### Added

| File | Change |
|---|---|
| `game.py` | `scene` (`WARNING_SCENE`, `CAUGHT_SCENE`, `GAME_OVER_SCENE`), `start_scene()`, `skip_scene()`, `start_game_over()`. Events `"rip"` and `"nooo"`. |
| `render.py` | `draw_scene()`, `draw_caught_scene()`, `make_exclaim()`, `scene_texts()`, `scene_shake()`, `draw_game_over()`, `chat_line()`, `wrap()`, `make_gemini_logo()`, `claude_logo()`, `logo_face()`. `CAUGHT_IMAGE` (optional `classroom_caught.jpeg`), `CAUGHT_TEXTS`, `GAME_OVER_CHAT` and the chat/logo constants. |
| `sounds.py` | `rip()` (crackly noise) and `nooo()` (a voice-like sound sliding down) made in code; `"nooo"` can be replaced by `assets/sounds/noooo.mp3`. |
| `settings.py` | `CAUGHT_SCENE_TIME` (4 s), `CAUGHT_EXCLAIM_TIME` (1.2 s), `GAME_OVER_TIME` (8 s). |
| `tests/test_game.py` | `test_caught_scene_then_game_over`, `test_time_up_goes_straight_to_game_over`, `test_skip_only_after_losing`; the last-warning test checks the game over scene follows. 90 tests now. |

### Changed

| File | Change |
|---|---|
| `game.py` | `lose()` starts the caught or game over scene; when a scene ends after losing, the game over scene starts. |
| `render.py` | The end of the warning scene (red light, texts, flash) is `scene_texts()`, shared with the caught scene. `POINTING_TOP` is now `SCENE_PICTURE_TOP`, used by both scene pictures. `LOADING_TITLE` is "THE QUIZ". |
| `main.py` | Draws any scene with `draw_scene()`. After losing nothing pauses when the face is lost. Space, Enter or a click skips the scenes after losing. |
| `sounds.py` | A sound file that does not exist is skipped silently (the beep stays); only a broken file prints a message. Needed for the optional `noooo.mp3`. |
| `README.md`, `LEARN.md`, `PLAN.md` | The scenes, the game over screen, "The Quiz". |

### Details worth knowing

- The logos are drawn in code, not copied as picture files: simple shapes
  like the real ones (Claude's orange burst, Gemini's blue-purple
  four-pointed star) that can have faces and move. The joke: Gemini drew
  the game's pictures and Claude wrote its code.
- The chat lines are in `GAME_OVER_CHAT` in `render.py`; change them
  freely. When both lines are typed, both logos laugh. Lines longer than
  `BUBBLE_MAX_WIDTH` wrap.
- Order after losing: caught → caught scene → game over → end menu; last
  warning → warning scene → game over → end menu; time up → game over →
  end menu.
- `classroom_caught.jpeg` does not exist yet; until it does, the caught
  scene stays on the "!" picture with the texts. It is cut like
  `classroom_warning.jpeg` (`SCENE_PICTURE_TOP`).
- Tests: all 90 pass. Drew the "!" (popping, at the board and at the desk),
  the caught texts, and the game over chat for all three ways of losing
  (while typing and at the end) and checked them by eye. Ran the real loop
  with the face lost: caught scene → game over scene → Space → end menu.
  A person should check: the "!" pops at the same moment as the MGS sound;
  the rip and nooo sounds are funny, not annoying; the chat is readable and
  not too slow; Space skips.

### Next

- `classroom_caught.jpeg` (the prompt is in `PLAN.md` section 5; then
  check its cut).
- The team's own `noooo.mp3`.
- Then the list of commit #15.

---

## Commit #19 — A loading bar that fills like a real one, chat without "haha"

- **Date:** 7 Oct 2026

### Summary

The loading screen shows one funny line (picked at random) instead of
changing it while loading, and its bar no longer fills at an even speed: it
gets stuck, jumps, gets stuck again and makes the last jump to 100 % right
at the end, with the percentage next to it. On the game over screen the
"hahahaha" at the end of the chat lines is gone; instead both logos laugh
once the second line is typed.

### Added

| File | Change |
|---|---|
| `menu.py` | `loading_steps(rng)` (a random plan of jumps) and `loading_progress(time, steps)` (how full the bar is). |
| `settings.py` | `LOADING_JUMPS` (5), `LOADING_STALL` (0.6). |
| `tests/test_menu.py` | `LoadingTests`: starts at 0, ends at 1, never goes back, gets stuck and jumps, not full before the end. 94 tests now. |

### Changed

| File | Change |
|---|---|
| `render.py` | `draw_loading()`: one line for the whole loading, the percentage next to the bar. `TIPS_PER_LOADING` removed. The chat lines lose their "hahahaha"; `chat_line()` takes `laughing`, which `draw_game_over()` turns on for both logos when the chat is over. |
| `main.py` | `start_game()` makes a new `loading_plan`; `loading_screen()` uses `loading_progress()`. |
| `render.py` | More colourful logos (the team found them dull): Gemini's star in blue, green, yellow and red going round it, lighter in the middle (`GEMINI_COLOURS`); Claude's rays in warm colours in turn (`CLAUDE_COLOURS`); both with a dark outline (`OUTLINE`) and a pulsing glow behind (`make_glow()`, `LOGO_GLOW`, `GLOW_ALPHA`). Faces: eyes with a shine, rosy cheeks (`CHEEKS`), a tongue when laughing. `make_claude_logo()` replaces `claude_logo()`: the logo is made once, as a picture. |
| `LEARN.md`, `PLAN.md`, `NOTES.md` (#18) | The new loading bar; no "haha" in the chat. |

### Details worth knowing

- Between two points of the plan the bar is stuck for the first 60 %
  (`LOADING_STALL`) of the time and then moves quickly, so it looks like
  real loading. Each loading gets a new random plan.
- The team will pick the sound files themselves (`noooo.mp3` and others).
- Tests: all 94 pass. Printed one plan (0% 0% 6% 8% 10% 10% 26% 38% ...
  51% 51% 51% 51% 51% 54% 69% 84% 100%) and drew the loading screen at 26 %
  and 90 % and the end of the chat, and checked them by eye; same for the
  new logos (talking and laughing). A person should check: the uneven fill
  feels like loading, not like a bug; the logos look good on your screen.
- The Gemini star is coloured pixel by pixel when the game starts; it adds
  a fraction of a second to the start, once.

### Next

Same as commit #18.

---

## Commit #20 — The tearing picture shows, a line per warning, keys pause the head

- **Date:** 7 Oct 2026

### Summary

Three smaller changes. The caught scene now shows the team's picture of the
teacher tearing up the exam: it had been saved as `.png`, and the game only
looked for `.jpeg`. The warning scene shows a different line for each
warning. In the menus, a key press or a click turns head control off for
1 s, so the head and the keys do not fight; a box above the webcam shows
"KEYBOARD", then "HEAD CONTROL".

### Added

| File | Change |
|---|---|
| `assets/images/classroom_caught.png` | The teacher tearing your exam in half, the class shocked and laughing. Made by the team with Gemini (prompt in `PLAN.md`). |
| `render.py` | `image_file(name)`: finds a picture as `.jpeg`, `.jpg` or `.png` (`IMAGE_TYPES`). `WARNING_LINES`: 1 "DO NOT STARE AT ME! LOOK AT YOUR DAMN PAPER!", 2 "YOU WANNA FAIL, YOU LITTLE RACCOON?", 3 "IT IS OVER FOR YOU, YOU CHEATING NOODLE!" (chosen by the team). `head_indicator()`, `INDICATOR_HEIGHT`. |
| `menu.py` | `HeadMenuInput.pause()` and `paused_part()`. |
| `settings.py` | `HEAD_PAUSE_AFTER_KEYS` (1 s). |
| `tests/test_menu.py` | `test_keys_pause_head_control`. |

### Changed

| File | Change |
|---|---|
| `render.py` | `SCENE_PICTURE_TOP` is a dict, one cut per picture (warning 120, caught 60): in the caught picture the teacher stands higher. `draw_menu()` and `draw_end()` take `head_pause`. |
| `main.py` | A key press or a left click on a menu screen calls `head_input.pause()`. |

### Details worth knowing

- Only the menus pause the head. In the game the A-D keys are pressed while
  looking down, so pausing the head there would break the game.
- Moving the mouse does not pause the head (a mouse that moves a little on
  the desk would keep it off all the time); clicks do.
- After the pause the head must be straight once, like after opening a
  menu, so a head still tilted from before does not move the selection.
- There is a `assets/images/Antigravity_CLI.webp` the game does not use; it
  was left alone.

### Next

Same as commit #18.

---

## Commit #21 — "Glitch Please" intro

- **Date:** 7 Oct 2026

### Summary

The game now opens with our team's intro, like a studio logo before a film:
on black, "GLITCH PLEASE" glitches in (red and cyan copies sliding apart,
slices jumping sideways, flickering, TV static lines), settles, the "GP"
mark with a glitched slice appears above it and "presents" below, and it
fades to black. About 3.4 s with a sound made in code (chopped digital
buzzes, then a low hit). Any key or click skips it. It is one file that
only needs pygame, meant to be copied into all our projects.

### Added

| File | Change |
|---|---|
| `glitch_intro.py` | `play(screen, clock)`, `draw_frame()`, `glitch_blit()`, `static_lines()`, `make_mark()`, `make_pictures()`, `make_sound()`, `find_font()`. All its numbers at its top. |
| `main.py` | `run()` plays the intro before the loop; closing the window during it quits. |

### Details worth knowing

- The two coloured copies are blitted with `BLEND_ADD` on black: where they
  overlap they add up to white. They are rendered on a black background:
  rendered see-through, the colour hidden in the see-through pixels was
  added too, and the name showed as a white box.
- The settings of the intro are in `glitch_intro.py`, not in `settings.py`,
  on purpose: then it stays a single file that works in any project.
- Without numpy or a sound device it is silent.
- Tests: none (it only draws). Drew it at six moments and checked them by
  eye. A person should check: it feels like a studio intro, not too long;
  the sound is not too loud; a key skips it.

### Next

Same as commit #18.

---

## Commit #22 — The disclaimer as an official notice

- **Date:** 7 Oct 2026

### Summary

The disclaimer no longer looks like the menus. A cream paper slides in onto
a wooden desk: "OFFICIAL NOTICE — ACADEMIC INTEGRITY DEPARTMENT - ME461".
The six lines are typed out in a typewriter font with a key sound and a
blinking cursor (Space shows them all at once). Space signs it (a blue
scribbled signature, a pencil sound), then a red "APPROVED" stamp slams
down with a thump and shakes the paper, and the game goes on by itself
(or at once with Space).

### Added

| File | Change |
|---|---|
| `disclaimer.py` | `Disclaimer`: `letters()`, `typed()`, `press()`, `update()`, `sign_progress()`, `stamp_time()`, `stamp_age()`, `done()`. No drawing, so it is tested. |
| `tests/test_disclaimer.py` | 5 tests: typing, no going on without a signature, Space while typing, sign → stamp → go on, Space after the stamp. 100 tests now. |
| `render.py` | `draw_disclaimer(notice)`, `make_desk()`, `make_stamp()`, `signature()`, `mono_font()`. `DISCLAIMER_LETTERS`, `NOTICE_TITLE`, `NOTICE_FROM`, the paper/ink/stamp/desk colours, `PAPER_RECT`, `PAPER_SLIDE`, `STAMP_ANGLE`, `STAMP_SLAM`, `MONO_FONTS`. |
| `sounds.py` | `"type"` (a short click), `"sign"` (pencil scribble), `"stamp"` (a low thump). |
| `settings.py` | `NOTICE_TYPE_DELAY`, `NOTICE_TYPE_SPEED`, `NOTICE_SIGN_TIME`, `NOTICE_STAMP_HOLD`. |

### Changed

| File | Change |
|---|---|
| `render.py` | `DISCLAIMER_LINES` have ink colours for the paper (dark, faded, blue for the serious last line). |
| `main.py` | `self.notice`; Space, Enter or a click on the disclaimer call `press_notice()`; the disclaimer goes on to the start screen when `notice.done()`. |

### Details worth knowing

- The typewriter font is the first of Courier New, Courier, Nimbus Mono PS
  (a Courier copy on Linux), DejaVu Sans Mono, Liberation Mono.
- The stamp is a bit see-through, like ink, and slightly over the paper's
  edge, like a real one.
- Tests: all 100 pass. Drew the paper sliding in, half typed, signing,
  the stamp slamming and landing, and checked them by eye. Ran the real
  loop: Space finished the typing, Space signed, the stamp came, then the
  start screen. A person should check: the typing speed; the stamp sound.

### Next

Same as commit #18.

---

## Commit #23 — Softer, smoother menus

- **Date:** 7 Oct 2026

### Summary

The menus keep the Hotline Miami look but are softer and have many more
tones: a three-colour sunset gradient drawn one pixel row at a time instead
of 4-pixel strips, light rays with soft edges that fade outwards, very
light film grain that hides colour steps, fainter scanlines, darker
corners, half see-through pink/cyan copies of the text and a blurred glow
behind the titles and the selected item. On big screens the 960×600
picture is now stretched smoothly instead of pixel by pixel.

### Added

| File | Change |
|---|---|
| `render.py` | `make_menu_layers()` (ray fade, vignette and grain, made once with NumPy), `item_glow()`. `VIGNETTE_ALPHA`, `GRAIN_ALPHA`, `GLOW_BLUR`, `GHOST_ALPHA`. `neon_text(..., glow=True)`. |
| `settings.py` | `SMOOTH_SCALING` (True). |

### Changed

| File | Change |
|---|---|
| `render.py` | `MENU_PALETTES` are (top, middle, bottom) sunset colours, a little less saturated. `menu_background()` draws the rays at half size, fades them, stretches them smoothly. `SCANLINE_ALPHA` 45 → 20 (the scanlines were the main source of hard contrast; they also show in the game's scenes, softer now too). `RAY_ALPHA` 28 → 60 in the middle, fading outwards. `GRADIENT_STEP` removed. `render.py` now imports NumPy (it comes with MediaPipe). |
| `main.py` | With `SMOOTH_SCALING`, sets `SDL_RENDER_SCALE_QUALITY=linear` before the window opens. |

### Details worth knowing

- A menu frame takes about 3.7 ms to draw (it was about 2 ms), still far
  under the 33 ms of a frame at 30 fps.
- Really sharp "HD" would mean drawing everything at e.g. 1920×1200; every
  pixel position in `render.py` would change, so that is left for later.
- Smooth stretching only shows on a real window bigger than 960×600; it
  could not be checked without a screen. If the game looks blurry instead,
  set `SMOOTH_SCALING = False`.
- Tests: all 100 pass. Drew the main menu at two moments (pink and violet
  palettes) and checked them by eye; ran the whole start of the game in the
  real loop (intro, notice, start, menu, loading). A person should check:
  the menus look softer but still neon; text is sharp; on a big screen the
  game is smooth, not blurry.

### Next

- The team's sounds (they will pick them from a sound library).
- Then the list of commit #15.

---

## Commit #24 — Gradual focus and camera reconnecting (from Emre), score and best score

- **Date:** 7 Oct 2026

### Summary

The team found the game not fun (copying was just waiting) and with no
reason to play it again. Two fixes. **Copying is active now**: the
neighbour's paper is blurry and gets sharper the longer you keep looking
(2.5 s); every look starts blurry again, so reading means holding a risky
look. **A score**: right answers, the time left, close calls (seen copying,
but looked away in time: +150) and warnings; the best score is saved and
shown on the main menu and the end screen. Also the camera no longer closes
the game when it drops out: it reconnects by itself while the game waits.

The gradual focus and the camera reconnecting are Emre's work, from his
branch `me461-python-visual-tracking-app2-gp` (commit `2ddf878`, his NOTES
#12–#14). That branch started from commit `681fe15` and rebuilt the papers
in a different way (drawn A-E papers, both neighbours knowing the answer),
so it was not merged with git: the team chose to bring his ideas and his
camera code into this branch, keeping the pictures, menus and scenes.

### Added

| File | Change |
|---|---|
| `camera.py` | Emre's reader, as it is: background start, retries, reconnecting, a camera fallback before the first picture, `read()` returns a copy or `None`. |
| `tests/test_camera.py` | Emre's camera tests (fake camera and clock), as they are. |
| `head_tracker.py` | `reset_tracking()` (Emre): forget old angles after a camera gap, keep the calibration. One test. |
| `game.py` | `focus_time`, `paper_clarity()`, `reset_paper_focus()`, `paper_says()`. `close_calls`, `"close_call"` event and popup. `score_parts()`, `score()`. |
| `highscore.py` | `load_best()`, `save_best()` (JSON file; missing/broken = 0; cannot write = only a message). |
| `tests/test_highscore.py` | 4 tests. |
| `render.py` | `blurred(picture, clarity)`, `BLUR_SMALLEST`, `BLUR_SOFTEN`. `draw_camera_wait()`. Score, breakdown, "NEW BEST!" / "BEST" on the end screen; "BEST SCORE" on the main menu. |
| `settings.py` | `PAPER_FOCUS_TIME` (2.5 s); `CAMERA_FALLBACK_INDICES` (1), `CAMERA_WARMUP_TIME`, `CAMERA_STALE_TIME`, `CAMERA_RECONNECT_TIME`, `CAMERA_RETRY_INTERVAL`, `CAMERA_READ_RETRY`, `CAMERA_STOP_TIMEOUT`; `SCORE_PER_CORRECT` (1000), `SCORE_TIME_BONUS` (1000), `SCORE_PER_CLOSE_CALL` (150), `SCORE_PER_WARNING` (300), `HIGH_SCORE_FILE`. |
| `sounds.py` | `"close_call"` (two rising notes). |
| `.gitignore` | `highscore.json` (each computer has its own best score). |

### Changed

| File | Change |
|---|---|
| `game.py` | Copying: the focus grows while you look at a side (not while seen), resets whenever the direction changes, and reading happens once at full focus. A side already read gets sharp again when you look back. |
| `render.py` | The neighbour's picture with the letter (or "?") is shown from the start of a look, blurred by the focus. The copy bar is gone: the blur shows the progress, so the bottom strip only has the suspicion bar (`BOTTOM_BAR` 80 → 46 px). Texts: "Reading answer 1 from the left - keep looking". The end screen is laid out for the score. |
| `main.py` | No frame → "WAITING FOR CAMERA" screen, tracker and focus reset, waiting time thrown away (the clock does not run). Quitting works before the first picture. The best score is checked when the end screen opens (`check_best()`), and kept next to `main.py`. `show_error()` removed (nothing closes the game any more). |
| `tests/test_game.py` | Copying tests rewritten for the focus (sharper, blurry again after looking away, short glances do not add up, what the paper says before reading); score and close call tests. 121 tests now. |
| `README.md`, `LEARN.md`, `PLAN.md` | Focus, score, camera. Emre is named where his ideas are described. |

### Removed

| Item | Why |
|---|---|
| `COPY_TIME`, `TICK_INTERVAL`, the tick sound, `copy_time` | The copy bar (5 s, kept between looks) was replaced by the focus. The blur shows the progress; the ticks were only noise. |
| `show_error()` in `main.py` | Camera problems now wait and reconnect instead of closing. |

### Details worth knowing

- Not taken from Emre's branch: `CAMERA_INDEX = 1` (his computer's
  camera; here it stays 0, with 1 as the fallback), the drawn A-E papers,
  both neighbours knowing the answer, Up/Down answer revising, F2/F3 keys.
  The team chose: every look starts blurry (his rule), one neighbour knows
  and the other shows "?" (ours).
- The blur shrinks the picture (to 3 % of its size when blurriest), softens
  it and stretches it back: about 7 ms per frame. clarity² makes it stay
  unreadable for a while and sharpen quickly at the end.
- The time bonus is a share of the exam time, so choosing a longer exam in
  the settings does not give more points.
- A close call is counted whenever being seen ends without being caught
  (also if the teacher looks away first: lucky, but still a close call).
- Tests: all 121 pass. Drew the left neighbour at 0 %, 45 %, 75 % and 100 %
  focus, the end screen (new best, not new best, lost), the main menu with
  a best score and the camera waiting screen, and checked them by eye. Ran
  the real loop: the opening, the menus, the loading; and a camera that
  sends nothing at first, then pictures. A person should check, with the
  webcam: 2.5 s feels right; the letter is unreadable until near the end;
  close calls feel rewarding; the camera unplugged and plugged back in.

### Next

- Play it as a team: is it fun now? Then tune `PAPER_FOCUS_TIME`, the
  teacher's times and the score numbers.
- Levels (Quiz → Midterm → Final) and teacher personalities (PLAN.md 8.5).
- Tell Emre what was taken from his branch, so the two branches do not
  drift further apart.

(Also in this change: the unused `assets/images/Antigravity_CLI.webp`, never
committed, was deleted at the team's request; and `PLAN.md` got section 11,
the draft plan of the next update: three quizzes per run, the teacher's
moods, controlled randomness. And after losing, the end menu now appears
under the finished game over chat instead of on a different screen
(`chat_screen()` in `render.py`; the chat moved up to make room:
`CHAT_TOP`, `CHAT_ROW`, `CHAT_MENU_TOP`, `CHAT_MENU_GAP`).)

---

## Commit #25 — Guessing and blank answers, the paper collected at time up, a Balatro-style score count, the code in folders

- **Date:** 7 Oct 2026

### Summary

A player reported that after the first question the next answers could
not be written. The rules, the real loop (with a fake head direction) and
the pictures were all checked and worked; the bug could not be reproduced
without a webcam. The cause is most likely the rule "write only after the
knowing neighbour's paper was read" together with the real head tracking
(one jittery frame restarts the 2.5 s focus, and the "?" side does not
count). The team wanted that rule gone anyway: **any letter can be written
at any time**, read or not. A question can also be left **blank** (S).
Grading: right **+1**, wrong **−0.5**, blank **0**, so a blind guess is a
gamble. **When the clock runs out the paper is collected** and graded
(blanks for the rest) instead of being a loss. After a graded exam the
score is **counted up part by part like in Balatro**; a failed one (caught,
3 warnings) still gets the game over chat.

The code had grown long: `game.py` (323 lines) and `render.py` (1456 lines)
were split into small files with one job each, and the files were sorted
into folders: `logic/` (rules, no drawing), `tracking/` (webcam, head),
`ui/` (drawing, sounds). The game itself did not change in that part.

### Added

| File | Change |
|---|---|
| `logic/exam_paper.py` | `ExamPaper`: answer key, `written` (letters or `BLANK`), `says()`, `results()` (`CORRECT` / `WRONG` / `EMPTY`), `count()`, `points()`. From `game.py`. |
| `logic/neighbours.py` | `NeighbourPapers`: `focus_time`, `read_sides`, `clarity()`, `has_read()`, `reset_focus()`, `new_question()`, `update()`. From `game.py`. |
| `logic/suspicion.py` | `SuspicionBar`: `level`, `seen_copying`, close calls, `update()`, `is_full()`, `start_over()`; `WARNING_TIME`, `GRACE_PART`, `FULL`. From `game.py`. |
| `logic/tally.py` | The score count: `appear_time()`, `parts_shown()`, `running_score()`, `is_done()`. |
| `logic/game.py` | `leave_blank()`, `knows_answer()`, `collect_paper()`, `time_ran_out`, `update_scene()`, `show_popup()`. |
| `ui/style.py` | Colours, fonts, `NeonStyle` (text, shadow text, bars, neon text, shout, wrap, preview). From `render.py`. |
| `ui/draw_game.py`, `ui/draw_scenes.py`, `ui/draw_menus.py`, `ui/draw_notice.py` | The drawing of each kind of screen, as mixin classes of `Renderer`. From `render.py`. |
| `ui/draw_menus.py` | `draw_tally()` (moved to `draw_results.py` in #26): the question cards pop in with their points, the grade, the bonuses, the score counting up and thumping. |
| `ui/sounds.py` | `tally0` … `tally15` (a semitone higher each), `tally_done`, `tally_sound()`. |
| `main.py` | S key (`BLANK_KEY`), `count_score()` (a tick per new part), Space skips the count. |
| `settings.py` | `POINTS_CORRECT` (1), `POINTS_WRONG` (−0.5), `POINTS_BLANK` (0), `SCORE_PER_POINT` (1000), `TALLY_START` (0.8 s), `TALLY_STEP_TIME` (0.45 s), `TALLY_COUNT_TIME` (0.3 s). |
| `logic/__init__.py`, `tracking/__init__.py`, `ui/__init__.py`, `old/__init__.py` | The folders, with a docstring saying what is in each. |
| `tests/test_exam_paper.py`, `tests/test_tally.py` | 7 + 5 tests. |

### Changed

| File | Change |
|---|---|
| `logic/game.py` | Half as long: uses the three files above. `write()` only needs DOWN (and no scene), not a read paper. Time up → `collect_paper()`, `WON`, `"time_up"` event (not a loss). `score_parts()` lists every question (`Q1`…) so the count can show them one by one. |
| `ui/render.py` | Only the `Renderer` (fonts, pictures, layers); it inherits the drawing from the `draw_*.py` files. |
| Everything | Moved into `logic/`, `tracking/`, `ui/` (with `git mv`, history kept); imports are `from logic.game import Game` etc. `tracker.py` → `old/tracker.py`. |
| `ui/draw_game.py` | Blank answers show as "-" (grey). Looking down: "Answer 2: guess with A-D, or S = blank" / "Press A-D to write answer 2 (S = blank)", "Wrong -0.5, blank 0". |
| `ui/sounds.py` | `lost_time` → `time_up`. |
| `tests/test_game.py` | For the split, guessing, blanks, the collected paper. |

### Removed

| Item | Why |
|---|---|
| "Read before you write" (`can_write()` needing the read paper) | Guessing is part of the game now; also the likely cause of the reported bug. |
| Losing by time (`lost_time`, the "time" game over chat) | The paper is collected and graded instead. |
| `correct_count()`, `paper_says()`, `paper_clarity()`, `reset_paper_focus()`, `suspicion()` on `Game` | Now `game.paper.count(CORRECT)`, `game.paper.says()`, `game.neighbours.clarity()`, `game.neighbours.reset_focus()`, `game.suspicion.level`. |

### Details worth knowing

- `Renderer` inherits from `NeonStyle, NoticeDrawing, MenuDrawing,
  GameDrawing, SceneDrawing` (and `ResultsDrawing`, #26): one object, its
  methods spread over files; any method can still call any other with
  `self.`.
- The split was done by moving the code as it was (line ranges), then
  checked with a small script for names used but never defined, and by
  drawing every screen with a fake camera (`SDL_VIDEODRIVER=dummy`).
- The first tries of that check wrote a test score into the real
  `highscore.json` (1979 points); it was deleted. Checks now use a
  temporary file.
- Tests: 138, all pass.

### Next

- With the webcam: the reported bug should be gone (any letter is written
  while looking down). If it ever happens again, check whether the game
  thinks you look down (your paper is shown) when you press the key.

---

## Commit #26 — Three exams per run (phase A), early bonus and close calls, top scores

- **Date:** 7 Oct 2026

### Summary

Phase A of PLAN.md 11.8. A run is now **three exams**: the Quiz (3
questions, 150 s), the Midterm (4, 130 s), the Final (5, 120 s). Each exam
the teacher is in a **mood**, picked from two per exam; for now a mood is
only numbers (how long he is busy and watching, how often he moves), and
the loading screen tells it as **hallway gossip** ("He is on his third
coffee."). A failed exam scores 0 and the run goes on. The run's score is
the total; after the Final the **results** count it up next to the **top 5
scores**, which are also on the main menu. A new top score lights up with
"NEW HIGH SCORE! #2", confetti and a fanfare. Scoring: the time bonus is
now the **early bonus**, and a **close call** is worth more the fuller the
suspicion bar was when you got away (100–500, +300 above 80 %: "RAZOR
CLOSE!"). The open decisions of PLAN.md 11.9 were taken (see there).

### Added

| File | Change |
|---|---|
| `logic/run.py` | `Run`: the exams in order, each exam's mood, `new_game()`, `finish_quiz()`, `is_over()`, `total()`, `score_parts()`, `gossip()`. |
| `logic/teacher.py` | `Teacher(rng, mood)`, `set_mood()`: a mood's busy/watching durations and move chance. |
| `logic/suspicion.py` | `close_call_points(level)`, `close_call_score`, `last_close_call`. |
| `logic/highscore.py` | `load_top()`, `add_score()`, `save_top()`: the best 5 runs with their dates; an old `{"best": …}` file still loads. |
| `ui/draw_results.py` | `ResultsDrawing`: `draw_end()` and `draw_tally()` (from `draw_menus.py`), `draw_run_end()` (each exam, the total counted up, the top scores), `top_scores()`, `confetti()`, `thumped()`. |
| `ui/style.py` | `panel()`: the dark purple box with a pink edge, used by every box. |
| `ui/sounds.py` | `new_top` (a run up the notes and a chord). |
| `main.py` | `RUN_END` screen, `start_run()`, `start_exam()`, `record_run()`, `counted_parts()`, `count_done()`. |
| `settings.py` | `QUIZZES`, `MOODS`, `CLOSE_CALL_MIN` (100), `CLOSE_CALL_PER_BAR` (400), `CLOSE_CALL_EDGE` (0.8), `CLOSE_CALL_EDGE_BONUS` (300), `TOP_SCORES_KEPT` (5). |
| `tests/test_run.py` | 7 tests. `tests/test_teacher.py`: 3 mood tests. `tests/test_highscore.py`: rewritten for the top list (9). `tests/test_game.py`: close calls, fewer questions. |

### Changed

| File | Change |
|---|---|
| `logic/game.py`, `logic/exam_paper.py` | `Game(rng, exam_time, questions)`; `ExamPaper(rng, questions)`, `size()`. `"TIME"` → `"EARLY BONUS"`, close calls from the bar. |
| `ui/draw_menus.py` | Loading: "Chapter 1/3", the exam's title, "HALLWAY GOSSIP:" and the mood's line (instead of a random funny line). Main menu: the top scores box (instead of "BEST SCORE"). How to play: the run and the grading. |
| `ui/draw_results.py` | After an exam: "RUN TOTAL" under the score; the menu is "Next exam" / "Main menu", or "See results" after the Final. |
| `ui/draw_game.py` | The answer boxes follow the exam's number of questions. |
| `main.py` | Play starts a run; R restarts the run; Settings has no exam time. |

### Removed

| Item | Why |
|---|---|
| The "Exam time" setting, `EXAM_TIME_CHOICES`, `menu.next_choice()` | Each exam has a fixed time, so top scores are fair. |
| `LOADING_TIPS`, `LOADING_CHAPTER`, `LOADING_TITLE` | The loading screen shows the exam and the gossip. |
| `load_best()`, `save_best()`, `check_best()`, "NEW BEST!" | Replaced by the top scores. |

### Details worth knowing

- `QUIZZES` and `MOODS` are only data: a new exam or mood is a few lines in
  `settings.py`. An exam may have at most `ANSWERS_NEEDED` (5) questions,
  because the paper picture has 5 lines (a test checks it).
- A close call is worth what the bar showed at the end of being seen (the
  frame before getting away), so escaping just before being caught pays
  the most.
- The new top score stays hidden in the list while the total is still
  counting, then appears lit up, so the count is not given away.
- A tie with an older top score goes under it.
- The run is kept in `App.current_run`, not `App.run`: an attribute called
  `run` hid the main loop `App.run()`, and the game closed at once
  ("'Run' object is not callable"). The fake-camera checks drove the
  screens directly and never called `App.run()`, so they missed it; the
  real `main.py` was started afterwards and runs.
- Tests: all 152 pass. Played a whole run with a fake camera and drew
  every new screen (loading with gossip, the count after each exam, a
  failed exam, a collected paper, the results with a new top score, the
  main menu with the list) and checked them by eye. A person should try,
  with the webcam: a whole run (does it take 4–8 minutes?); do the moods
  feel different; is the count too slow or too fast (`TALLY_STEP_TIME`);
  is guessing too cheap or too expensive (`POINTS_WRONG`); is the close
  call bonus worth the risk.

### Next

- Phase B (PLAN.md 11.4): bluffs, sneaky glances, sign sounds, fairness
  rules, the teacher getting faster within an exam.
- Letter grades (AA–FF), the canteen and the cards (11.6).
- Background music (Suno) once the file is in `assets/sounds/`.

---

## Commit #27 — The hallway gossip gets its own screen, button sounds

- **Date:** 7 Oct 2026

### Summary

The team wanted the teacher's mood told on a real screen, not as one line
on the loading screen. Before each exam there is now a **hallway gossip**
screen: the gossip, a short story of what happened to the teacher, and
**what it means** for the exam, then "I'M READY", chosen like any menu item
(turn right and hold, or Enter). Only then comes the loading screen. The
buttons also got **sounds** in an 80s synth style: a tick when the
selection moves (also when the mouse moves onto another item), three notes
up when something is chosen (also the Calibrate button), two notes down
for back.

### Added

| File | Change |
|---|---|
| `settings.py` | `"story"` (up to 3 lines) and `"hint"` for every mood in `MOODS`. |
| `ui/draw_menus.py` | `draw_briefing()`; `BRIEFING_CHAPTER_Y`, `BRIEFING_TITLE_Y`, `BRIEFING_PANEL`, `BRIEFING_ITEM_Y`. A long gossip line is shrunk to fit the box. |
| `ui/sounds.py` | `synth()` (a sine with its 3rd and 5th harmonics, quick decay); `menu_back`. |
| `main.py` | `BRIEFING` screen (a menu screen with "I'M READY"), `start_loading()`. Sounds for mouse hover, Calibrate, back. |
| `tests/test_run.py` | Every mood has a gossip, 1–3 story lines and a hint, each at most 70 letters. |

### Changed

| File | Change |
|---|---|
| `main.py` | "Play" / "Next exam" → BRIEFING → (I'm ready) → LOADING → GAME. Turning left on the gossip screen goes back to the main menu. |
| `logic/run.py` | `gossip()` returns the whole mood entry (gossip, story, hint). |
| `ui/draw_menus.py` | The loading screen: chapter, title, date, "Sharpening pencils..." and the bar (no gossip). |
| `ui/sounds.py` | `menu_move`, `menu_select` are synth notes now (were plain beeps). |

### Details worth knowing

- The story and hint texts are data in `settings.py`, next to each mood's
  numbers: a new mood is still only new settings.
- The hints say what the numbers do today (e.g. "long angry stares" = long
  watching times); when phase B adds bluffs and signs, the hints should
  name the sign to listen for.
- Tests: all 153 pass. Drew the gossip screen for all six moods and checked
  that nothing leaves the box; ran the whole run with a fake camera, and
  the real `main.py` for a few seconds. A person should try: do the sounds
  feel right (not too loud next to the teacher's "hmm"); is the gossip
  screen read, or skipped at once.

### Next

- Phase B (PLAN.md 11.4), then hints that name each mood's sign.

---

## Commit #28 — Background music

- **Date:** 7 Oct 2026

### Summary

The team made an 80s Miami theme with Suno (`theme.mp3`, 190 s). It loops
in the background from the moment the official notice is stamped and
signed (not during the intro or the notice, which have their own sounds): normal volume in
the menus and between exams, quiet during an exam, so the teacher's "hmm"
and the alarm are still heard. Sound OFF in the settings turns it off too.

### Added

| File | Change |
|---|---|
| `assets/sounds/theme.mp3` | The music (uploaded as `theme_[cut_190sec].mp3`, renamed). 7.6 MB. |
| `ui/sounds.py` | `MUSIC_FILE`, `start_music()` (streamed with `pygame.mixer.music`, looping), `music(in_exam, dt)` (fades the volume to where it should be). |
| `settings.py` | `MUSIC_VOLUME_MENU` (0.6), `MUSIC_VOLUME_GAME` (0.2), `MUSIC_FADE_TIME` (1.0 s). |

### Changed

| File | Change |
|---|---|
| `main.py` | Starts the music when the notice is done; every frame tells it whether an exam is being played (not its scenes, not after it). |

### Details worth knowing

- Streaming: the file is read while it plays, so the 7.6 MB do not slow
  down the start. The other sounds stay as they were.
- No sound device, no file or a broken file: no music, and the game runs
  as before (checked with a missing file).
- While the camera is reconnecting the volume stays where it was.
- Checked with a dummy sound driver: the music loads and plays, the volume
  fades to 0.6 in the menus, 0.2 in an exam and 0 when muted; tests (153)
  pass; the real `main.py` starts. A person should listen: is 0.2 quiet
  enough to hear the "hmm" over it, is 0.6 too loud next to the buttons.

### Next

- Maybe a second, tenser track for the exam.

---

## Commit #29 — Music only in the menus, smooth screen changes, new game over jokes

- **Date:** 7 Oct 2026

### Summary

The music now plays only in the menus: it fades out (1.5 s) on the loading
screen, the exam is silent, and it fades back in on the results. Every
screen change is a 0.4 s crossfade (the old screen's last picture fades out
over the new one), so menus appear smoothly. The game over chat has 8
conversations per way of failing instead of 1, drawn from a `Bag` (every
joke once before any repeats, never the same twice in a row).

### Added

| File | Change |
|---|---|
| `logic/bag.py`, `tests/test_bag.py` | `Bag`: Tetris-style random order (4 tests). Also planned for phase B's teacher moves. |
| `ui/draw_scenes.py` | `GAME_OVER_CHAT`: 8 + 8 conversations; `{exam}` becomes the exam's name. |
| `main.py` | `SILENT_SCREENS`, `pick_chat()`, `crossfade()`. |
| `settings.py` | `MUSIC_VOLUME` (0.6), `SCREEN_FADE_TIME` (0.4 s); `MUSIC_FADE_TIME` 1.0 → 1.5 s. |

### Removed

| Item | Why |
|---|---|
| `MUSIC_VOLUME_MENU`, `MUSIC_VOLUME_GAME` | No music during the exam any more. |

### Details worth knowing

- Also fixed on the way: a "How to play" line ran past its box, and the
  "HEAD CONTROL" box covered a line there (it now sits low when the screen
  has no webcam preview).
- Tests: 157 pass. Every chat line fits in two bubble lines (measured).

---

## Commit #30 — A slot machine for the mood, moods with good and bad sides, the teacher keeps an eye on you, ninja and sharp-eye bonuses

- **Date:** 7 Oct 2026

### Summary

The team's ideas after playing:
- The mood is drawn on the gossip screen by a **slot machine** ("Spin" with
  the head), so the player sees it is random. Each exam has 4–5 moods now
  (13 in all). The **Quiz's are good days** (or a plain one), the
  **Midterm's have good and bad sides**, the **Final's are bad days**; the
  screen lists them as green + and red − lines.
- **He keeps an eye on you:** above a hidden point on the suspicion bar
  (60 % / 45 % / 30 %), the teacher keeps watching until the bar drains
  back under it, so you must look at your paper.
- Bonuses: **NINJA!** +1500 (every answer right, no warning), **ALMOST
  NINJA** +500 (one warning), **SHARP EYE** +100 (the first paper read for
  a question is the one that knows; a popup at once).
- The caught scene says **"SO... YOU'RE CHEATING, HUH?"** instead of "Your
  exam: 0/5 - see you next semester".

### Added

| File | Change |
|---|---|
| `logic/slot.py`, `tests/test_slot.py` | The reel: `reel_position()`, `mood_in_middle()`, `has_stopped()`, `passed()` (5 tests). |
| `ui/draw_briefing.py` | `BriefingDrawing` (moved out of `draw_menus.py`): the slot window and reel, the story, the +/− lines. |
| `logic/game.py` | `suspicious_at`, `under_suspicion()`, `sharp_eyes` (`"sharp_eye"` event, popup), `ninja_bonus()`. |
| `logic/teacher.py` | `update(dt, keep_watching)`. |
| `logic/run.py` | `pool()`, `chosen()`. |
| `main.py` | `spin_time`, `spinning()`, `reel()`, `turn_reel()`; "SPIN" then "I'M READY"; `keep_watching` passed to the teacher. |
| `ui/sounds.py` | `slot_tick`, `slot_stop`, `sharp_eye`. |
| `settings.py` | 7 new moods (`birthday`, `new_phone`, `normal_day`, `diet`, `traffic`, `dean_visit`, `lost_bet`); `"suspicious"` per exam, `SUSPICIOUS_AT`; `SCORE_NINJA`, `SCORE_ALMOST_NINJA`, `SCORE_SHARP_EYE`; `SLOT_SPIN_TIME` (2.5 s), `SLOT_TURNS` (3). |
| Tests | Bonuses, the hidden point, keeping watching, moods per exam (good / mixed / bad), the chosen mood in the pool. 177 tests. |

### Changed

| File | Change |
|---|---|
| `settings.py` | `MOODS`: `"hint"` → `"good"` and `"bad"` lists; the numbers of the old moods adjusted so they match their lines. |
| `logic/game.py` | `score_parts()` lists only the bonuses you got (no row of zeros). |
| `ui/draw_results.py` | More than three bonuses go on two rows; the score, run total and menu moved down a little. |
| `ui/draw_scenes.py` | `CAUGHT_TEXTS`. |

### Details worth knowing

- The mood is still picked by `Run` at the start; the reel only shows it
  (it is built to stop on it).
- Sharp eye is a coin flip (nothing tells which side knows), so it is kept
  small: +100.
- The hidden point is not drawn on the bar on purpose. A warning empties
  the bar, so staring through it ends the watching too, with a warning.
- Checked: a teacher whose watching should end after 0.5 s kept watching
  for 3 s, until the bar drained from 90 % to under 60 %. Drew the slot
  spinning, every exam's gossip, five bonuses at once, the caught text.
  A person should try: is 2.5 s of spinning too long the third time; do
  the hidden points feel fair (`"suspicious"` in `QUIZZES`).

### Next

- Phase B (PLAN.md 11.4): bluffs, sneaky glances, sign sounds.

---

## Commit #31 — The slot machine looks like a slot machine

- **Date:** 7 Oct 2026

### Summary

The gossip screen's reel is now a real-looking slot machine, the
"MOOD-O-MATIC": a gold cabinet with bulbs that blink while waiting, chase
round while spinning and flash when it stops; a paper-white drum, darker at
the top and bottom, with the moods smaller away from the middle and blurred
while spinning fast; a lever with a red ball that the head pulls down (it
follows the "turn right and hold" bar) and that springs back when the
spin starts; and a reel that goes a little too far and settles back, like
a real one. Today's mood stops in the middle in red.

### Changed

| File | Change |
|---|---|
| `ui/draw_briefing.py` | Rewritten: `slot_cabinet()`, `bulb_spots()`, `slot_reel()` (drum, blur), `drum_shade()` (made once), `slot_lever()`. `draw_briefing()` takes `spin_time` instead of the reel position. |
| `logic/slot.py` | The overshoot (`SETTLE_PART`, `SLOT_BOUNCE`), `reel_speed()`. 2 more tests. |
| `settings.py` | `SLOT_BOUNCE` (0.35 moods), `SLOT_LEVER_TIME` (0.4 s). |

### Details worth knowing

- The overshoot stays under half a mood, so the mood in the middle never
  changes while it settles, and no extra tick plays.
- Drew it waiting (lever half pulled), spinning fast (blur), slowing, and
  stopped; tests (179) pass; the real `main.py` starts.
  A person should check: does the crossfade feel smooth; is the silence in
  the exam better than quiet music.

---

## Commit #32 — The Windows branches merged into main; main is the working branch

- **Date:** 7 Oct 2026

### Summary

The team wanted every branch in `main`. `dont-get-caught` (the game, NOTES
#25–#31) was already in it (fast-forward). The two Windows branches were
merged with real merges: `windows` (NOTES "#8 — Windows launcher" there,
3 Oct) and `windows-support` (NOTES "#7 — Windows support" there, 1 Oct).
Both started before the code was moved into folders, so their changes were
carried over by hand. Emre's branch was **not** merged: his ideas (gradual
focus, camera reconnecting) were brought in earlier (NOTES #24), and the
team chose not to take the rest. From now on the game is developed on
`main`.

### Added

| File | Change |
|---|---|
| `run.bat` | The Windows launcher, from `windows-support` (the fuller one of the two): creates `.venv` with `py -3` (or `python`), refuses 32-bit Python with a clear message (MediaPipe needs 64-bit), installs `requirements.txt` when it changed, starts the game, keeps the window open after a crash. |
| `.gitattributes` | `*.bat` with Windows line endings (CRLF), `*.sh` with Linux ones (LF), on every computer. |
| `tracking/camera.py` | `open_device()`: DirectShow on Windows (Media Foundation can take 10+ s to open a webcam). |
| `settings.py` | `WINDOWS_DIRECTSHOW = True`. |
| `README.md` | Windows in Requirements and Setup (64-bit Python, 3.12 safest, not in WSL), `run.bat` in Run, "If the webcam doesn't work" (7 steps, from `windows-support`'s NOTES, updated for the camera that now waits and reconnects). |

### Changed

| File | Change |
|---|---|
| `tracking/head_tracker.py` | The face model is read by us and given to MediaPipe as bytes (`model_asset_buffer`): with a file name it fails on Windows in folders with letters like ç, ş, ı. |
| `CLAUDE.md`, `PLAN.md` | The working branch is `main`. |
| `LEARN.md` | DirectShow and the model as bytes. |

### Removed

| Item | Why |
|---|---|
| `STEPS.md`, the root `camera.py` from `windows-support` | Already gone or moved (`tracking/camera.py`); the change was carried over by hand. |
| The two Windows NOTES entries numbered #7 and #8 | They clashed with this file's #7 and #8; they are summed up in this entry instead (the originals stay in the branches' history). |

### Details worth knowing

- `git log` keeps both Windows commits, so their original notes can still
  be read (`git show f56b2b9`, `git show 9c73a4b`).
- This computer only fetched `dont-get-caught` from GitHub, so its copy of
  `origin/main` was old; `remote.origin.fetch` now fetches every branch.
- Tests: 179 pass. The real game starts on Linux with the model loaded as
  bytes. **Not tried on Windows**: a person should double-click `run.bat`
  on a fresh clone on Windows, check that it installs, that the webcam
  opens quickly (DirectShow) and that the game runs.

---

## Commit #33 — Exam music, talking blips in the game over chat, the Metal Gear joke removed

- **Date:** 7 Oct 2026

### Summary

The team added `assets/sounds/thrilling.mp3` for the exam. It now plays
during an exam (quieter than the menu theme, so the teacher's sounds are
still heard) and stops when you fail. The game over chat's speech bubbles
now make little talking blips while they are typed, a different voice for
each logo. The chat about Metal Gear Solid ("You are not Solid Snake") was
removed, as the team asked.

### Added

| File | Change |
|---|---|
| `assets/sounds/thrilling.mp3` | The exam music (11 s, looped), added by the team. |
| `ui/sounds.py` | `MUSIC_FILES` / `MUSIC_VOLUMES` (two tracks, `"menu"` and `"exam"`), `load_track()`; `TALK_PITCHES`, `talk_sound()` and six `talk_*` blips. |
| `ui/draw_scenes.py` | `typed_letters()`, `CHAT_BLIP_LETTERS` (2 letters per blip). |
| `main.py` | `music_track()`, `typed_chat()`, `chat_blips()`. |
| `settings.py` | `EXAM_MUSIC_VOLUME` (0.35). |

### Changed

| File | Change |
|---|---|
| `ui/sounds.py` | `start_music()` only allows the music to start; `music(track, dt)` takes the track instead of on/off, and switches tracks with a fade out and a fade in. |
| `main.py` | `GAME` is no longer in `SILENT_SCREENS`. |
| `README.md`, `LEARN.md`, `PLAN.md` | The exam music and the blips. |

### Removed

| Item | Why |
|---|---|
| The "Solid Snake / Evaporated Snake" chat in `GAME_OVER_CHAT["caught"]` | The team asked for the Metal Gear Solid messages to go. The MGS alert sound and the red "!" stay. |

### Details worth knowing

- pygame streams only one music file at a time, so a new track waits
  until the old one has faded to silence, then starts from its beginning.
  The menu theme therefore starts over after every exam (before, it kept
  running silently through the exam).
- The blips play at most one a frame and never on a space, so words are
  heard as little groups. Skipping the chat (Space) stops them.
- Checked: tests (179) pass; with a dummy display the tracks switch
  (menu → exam → silence → menu at the right volumes) and the blips are
  made. **A person should try:** is the exam music too loud or too quiet
  against the Luigi "hmm" (`EXAM_MUSIC_VOLUME`); does the 11 s loop get
  annoying over a whole exam; are the blips pleasant or too many
  (`CHAT_BLIP_LETTERS` 2 → 3).

### Next

- Phase B (PLAN.md 11.4): bluffs, sneaky glances, sign sounds.

---

## Commit #34 — How to play is a hands-on guide with Gemini and Claude

- **Date:** 7 Oct 2026

### Summary

The "How to play" screen was a list of nine lines of text. Now it is a
guide: Gemini and Claude take turns talking (typed out, with the talking
blips from #33), finishing each other's sentences, and the player tries
each thing with their head as it is explained. Behind them is what the
player would see in the game: looking down shows the paper with what they
wrote, turning right shows the neighbour with "?" getting sharper, turning
left the one with "B", looking at the screen the teacher (busy, then
watching with the "hmm"). A banner says what to do, with a bar while the
direction is held, and "NICE!" when it is done. 12 steps cover the whole
game: the paper, writing and blanks, guessing and grading, the two
neighbours, the teacher, the "hmm", being caught, close calls, warnings,
handing in early, the bonuses and the three-exam run. The menu item is
still called "HOW TO PLAY"; at the end it offers Play, Start over and
Main menu.

### Added

| File | Purpose |
|---|---|
| `logic/guide.py` | `GUIDE_STEPS` (the script and tasks), `GUIDE_PAPERS`, `Guide`: `update()`, `press()`, `skip()`, `letters()`, `waiting()`, `progress()`, `clarity()`, `finished()`. No pygame. |
| `ui/draw_guide.py` | `GuideDrawing.draw_guide()`, `guide_view()`, `task_banner()`. |
| `tests/test_guide.py` | 13 tests: typing, blips, look / read / write tasks, the task waits for the lines, step sounds, Space, finishing, the real guide played through, line lengths. 192 tests in all. |
| `settings.py` | `GUIDE_TYPE_SPEED` (40 letters/s), `GUIDE_LINE_PAUSE` (1.6 s), `GUIDE_STEP_PAUSE` (1.0 s), `GUIDE_HOLD_TIME` (0.8 s), `GUIDE_BLIP_LETTERS` (2). |
| `main.py` | `guide_screen()`, `guide_key()`, `play_guide_sounds()`; `self.guide`, `self.guide_direction`. |

### Changed

| File | Change |
|---|---|
| `main.py` | HELP runs the guide until it is finished, then is a menu (`PLAY`, `START OVER`, `MAIN MENU`); `go_to(HELP)` starts a new guide. HELP has no entry in `TITLES` any more. |
| `ui/draw_menus.py` | `draw_menu()` lost its `lines` parameter (only the old help used it). |
| `ui/render.py` | `Renderer` also inherits `GuideDrawing`. |
| `README.md`, `LEARN.md`, `PLAN.md` | The guide. |

### Removed

| Item | Why |
|---|---|
| `HELP_LINES` in `ui/draw_menus.py` | Replaced by the guide. |

### Details worth knowing

- A task only counts once all lines of its step are typed, so the
  player reads what to do first. Writing only works while looking down,
  and the "write B" step only takes B (any other key: the "back" sound).
- In the guide the neighbours are fixed (right "?", left "B"), so the
  lines can talk about them; the real game picks at random.
- While looking at the screen the chat shows the last two lines at the
  bottom; looking away it shows only the newest one, under the banner,
  and hides the webcam preview: the papers are in the bottom half and
  Claude's logo would cover the preview.
- Losing the face does not pause the guide; the last direction is kept.
- Space finishes the line, then does the task for the player; Esc goes
  back to the menu. During the guide the head does not control a menu
  (turning right is a task, not "select").
- Checked: tests (192) pass; drew the steps with a dummy display (intro,
  look down, the right "?", the left paper, writing B, the watching
  teacher, the end menu) and moved texts that covered the papers.
  **A person should try:** play the whole guide with the webcam; is it
  too long (12 steps, about 2 minutes); does the chat jumping up when you
  look away feel odd; are the lines funny; does the "look at the screen"
  step pass easily after turning back.

### Next

- Phase B (PLAN.md 11.4): bluffs, sneaky glances, sign sounds.

---

## Commit #35 — After the guide, back to the main menu (it crashed)

- **Date:** 7 Oct 2026

### Summary

The team found that the game closed when the "How to play" guide ended.
On the frame the guide finished, `draw_guide()` still asked for the
current step's task, but there was no step left (`IndexError`), and the
game crashed. Now the guide goes straight back to the main menu when it
ends, as the team asked, and the end menu (Play / Start over / Main menu)
is gone.

### Changed

| File | Change |
|---|---|
| `main.py` | `guide_screen()` goes to MENU when the guide is finished, before drawing. HELP is no longer in `MENU_SCREENS` and has no `Menu`; "START OVER" removed. |
| `ui/draw_guide.py` | `draw_guide()` lost its `menu` parameter and the end menu. |
| `logic/guide.py` | `task()` and `teacher()` work after the end too (None / "busy"), so asking never crashes. |
| `tests/test_guide.py` | `test_it_finishes` asks about the step after the end. |
| `README.md`, `LEARN.md` | Back to the main menu after the guide. |

### Details worth knowing

- Reproduced the crash with a dummy display (`IndexError: list index out
  of range` in `task_banner()`), then ran the real `App` through the whole
  guide: it ends on MENU and the main menu draws. Tests (192) pass.
  **A person should try:** listen to the whole guide with the webcam and
  check that it lands on the main menu.

---

## Commit #36 — Three-letter names for top scores, the score boxes no longer cover texts, no quitting with q or X

- **Date:** 7 Oct 2026

### Summary

A run that gets into the top scores now asks for a three-letter name, like
an arcade machine: after the count, "NEW HIGH SCORE! #2", "ENTER YOUR
NAME" and three letter boxes. Tilt up/down rolls the chosen letter, turn
right goes to the next one (after the last: done), turn left goes back; or
type the letters, Enter finishes. The name shows in the top scores ("1.
EFE 12808 7 OCT"), live while it is typed. The team said the top scores
box covered texts: on the main menu the selected "HOW TO PLAY" (bigger
and rocking) reached the box, and on the results "NEW HIGH SCORE!" sat on
the total and the menu items touched each other. Also, as the team asked,
`q` and the window's X button no longer quit; Esc (main menu, game,
start screen) and the menu's QUIT do.

### Added

| File | Purpose |
|---|---|
| `logic/name_entry.py` | `NameEntry`: `roll()`, `next()`, `back()`, `type()`, `finish()`, `name()`; `ALPHABET`. No pygame. |
| `tests/test_name_entry.py` | 9 tests. |
| `logic/highscore.py` | A `"name"` on each entry; `set_name()`; `add_score(..., name="")`. |
| `tests/test_highscore.py` | 3 more tests (old files without names, long names cut, the name set later). 204 tests in all. |
| `settings.py` | `NAME_LETTERS` (3). |
| `main.py` | `name_entry`, `last_name` (the next entry starts with it), `naming()`, `name_action()`, `name_key()`, `save_name()`. |
| `ui/draw_results.py` | `name_boxes()`; a name column in `top_scores()` (`---` when there is none). |

### Changed

| File | Change |
|---|---|
| `ui/draw_menus.py` | `menu_items()` takes the middle `cx`; on the main menu the items move right just enough that the widest one, selected, keeps `TOP_PANEL_GAP` (24 px) from the scores box (measured, so any font fits). `TOP_PANEL` 20 px wider for the names. |
| `ui/draw_results.py` | Run results: the exams' box and the total moved up, the menu items 56 px apart (were 44, they touched), "NEW HIGH SCORE!" only while the name is typed and centred, the menu hidden until then. |
| `main.py` | `q` no longer quits; the window's X button is ignored (`pygame.QUIT` not handled). `SDL_NO_SIGNAL_HANDLERS` and a `try / except KeyboardInterrupt` in `run()` keep Ctrl+C in the terminal working and closing the camera properly. |
| `ui/draw_menus.py` | Footers: "Esc = quit" on the start screen, "Esc = back / quit" while waiting for the camera. |
| `README.md`, `LEARN.md` | Names, quitting. |

### Details worth knowing

- The new score is saved at once without a name and again with it, so
  quitting while typing never loses the score.
- While typing, all keys go to the name first: R, M, T, K type letters
  instead of restarting, the menu, testing or calibrating. Esc finishes the
  name as it is.
- The menu does nothing until the name is done, so a head turn meant for
  the last letter cannot also choose "PLAY AGAIN" (the head must be
  straight once again after the name).
- `ui/glitch_intro.py` still returns on the window's X button during the
  3 s intro: it is our shared intro file for every project, so it was left
  as it is.
- Checked: tests (204) pass; drew the main menu with "HOW TO PLAY"
  selected, the results while typing and after it; ran the real `App`:
  Space skips the count, `q`, `r`, `m` typed "QRM" (the game did not
  quit), the file got the name, then the menu worked. The X button and `q`
  leave the game running; Esc on the main menu quits.
  **A person should try:** type a name with the head (is 0.8 s per
  letter to go on too slow?); check on your own screen that nothing
  overlaps any more; Ctrl+C in the terminal stops the game.

---

## Commit #37 — The semester's letter grade, on a curve like a real teacher

- **Date:** 7 Oct 2026

### Summary

The run now ends with a METU-style letter grade (AA, BA, BB, CB, CC, DC,
DD, FD, FF), stamped on a moment after the count with the "stamp" sound.
The team asked for it to be given the way real teachers do: **on a curve
over all the earlier plays**, not over the top scores. So there is no
letter for a single exam (after it you see the class average of that
exam); the letter is for the semester, from the run's total against every
earlier run on this computer: how many standard deviations above their
average it is (z). An average run is a CC. For the first 5 runs there is
no class yet, so a fixed table on the share of the exam points is used
(90 % = AA, 50 % = CC). A total of 0 is always FF. Gemini also tells it in
the guide.

### Added

| File | Purpose |
|---|---|
| `logic/grade.py` | `curve()`, `z_score()`, `letter_for_z()`, `letter_for_share()`, `semester_grade()`, `class_average()`. No pygame. |
| `tests/test_grade.py` | 10 tests (no curve with too few runs, average = the z-0 letter, better total never a worse grade, thresholds, all-equal class, 0 = FF). |
| `logic/highscore.py` | The history of every play: `load_history()`, `remember()`, `empty_history()`; `save_top()` takes the history too. 3 more tests. 217 tests in all. |
| `logic/run.py` | `share()`: the share of all exam points got. |
| `logic/tally.py` | `done_time()`. |
| `settings.py` | `GRADES` (letter, least z, least share), `GRADE_CURVE_MIN` (5 runs), `GRADE_HISTORY_KEPT` (200), `GRADE_STAMP_DELAY` (0.5 s). |
| `main.py` | `history`, `record_exam()`, `exam_average`, `semester`, `stamped`; `record_run()` grades the run. |
| `ui/draw_results.py` | `grade_stamp()` (turned, lands from bigger, in the grade's colour, with the class average or "NO CLASS CURVE YET"); "CLASS AVERAGE" next to the run total after an exam. |

### Changed

| File | Change |
|---|---|
| `highscore.json` | Gets a `"history"` part on the next save; files without it still load (empty history). |
| `logic/guide.py` | One more line in step 11 about the curve. |
| `README.md`, `LEARN.md`, `PLAN.md` | The grade. |

### Details worth knowing

- The class average and the curve are read *before* the new score is
  added, so a run is never curved against itself.
- Failed exams (0) count in an exam's class average and a run's total
  counts in the class whatever it is, like everyone in a real class.
  Runs left half-way (main menu) add their exams but not a run total.
- The z limits (+1.3 AA ... −1.5 FD) and the fixed table are in
  `GRADES` in `settings.py`.
- The grade is from the total, which already has the bonuses and the
  −300 per warning, so warnings need no extra rule.
- Checked: tests (217) pass; drew the results with a curved BA (while
  typing a name) and an uncurved FD, and the class average after an
  exam; ran the real `App` through 7 fake runs into a scratch file: the
  history was written, the curve started at the 6th run, and the stamp
  sound played every time, also when Space skipped the count.
  **A person should try:** play a few runs and check the letters feel
  fair (too easy or too hard: change the z limits); this computer's
  `highscore.json` starts with no history, so the first 5 runs are
  graded without a curve.

---

## Commit #38 — Chalk, footsteps and a real tear; mood pictures; new phone stays at the desk; gossip lines fit

- **Date:** 7 Oct 2026

### Summary

The team asked for three sounds: the board being erased, walking, and the
exam being torn up. The chalk file (`Erasing Chalk On Chalkboard Sound
Effect.mp3`, in the folder since the start) now loops while the teacher
erases the board and stops the moment he starts to turn, so silence is a
warning too. Footsteps play when he walks between the board and the desk
and when he comes to your desk after a warning. The tear is two pulls
(rrrip... rrrrip!) instead of a short hiss. Footsteps and the tear are made
in code until the team adds files. The team also wants mood pictures
(party hat on his birthday, a suit when the dean visits, head in the phone
with a new phone): the code now shows `<picture>_<mood>` when that file
exists; the pictures are still to be made (PLAN.md 11.5 lists them). With
a new phone he now never leaves his desk. And the team saw gossip texts
running out of their box: the third +/- line of five moods was under the
box's edge.

### Added

| File | Purpose |
|---|---|
| `ui/sounds.py` | `loop()` (looping sounds, faded), `footsteps()`, `step()`, `tear()`, `chalk()` (stand-in); `"chalk"`, `"footsteps"`, `"rip"` in `SOUND_FILES` (the last two optional files); `SOUND_VOLUMES`. |
| `logic/teacher.py` | `erasing()`; `update()` also returns `"footsteps"` when he changes place; `home` (a mood's `"place"`). |
| `logic/game.py` | `warn()` also returns `"footsteps"`. |
| `main.py` | `chalk_heard()`, `self.paused`; the chalk loop every frame (off while waiting for the camera); `renderer.mood` before each exam. |
| `ui/render.py` | Mood pictures loaded if they exist; `picture(name)`. |
| `settings.py` | `CHALK_VOLUME` (0.5), `LOOP_FADE_TIME` (0.15 s); `new_phone`: `"place": "DESK"`, `"move": 0.0`, one more + line. |
| Tests | Footsteps only when he moves; erasing only busy at the board; a mood can keep him at one place; mood texts fit (3 story, 3 +/- lines). 222 tests. |

### Changed

| File | Change |
|---|---|
| `ui/sounds.py` | `rip()` rewritten: two tearing pulls, 0.9 s. |
| `ui/draw_game.py`, `ui/draw_scenes.py` | Every picture through `self.picture()`. |
| `ui/draw_briefing.py` | `LINE_GAP` 28 → 26, `EFFECTS_TOP` 234 → 222: three +/- lines fit in the box. |
| `README.md`, `LEARN.md`, `PLAN.md` | Sounds, mood pictures (the list of pictures wanted is in PLAN.md 11.5). |

### Details worth knowing

- Like every teacher sound, the chalk is not heard while looking down.
- The gossip on the reel was never cut: it shrinks to fit (down to 63 %
  for "He is fighting with someone on the phone."). Only the +/- lines
  ran over the box (`coffee`, `diet`, `paranoid`, `lost_bet`, and
  `new_phone` after its new line). All 13 moods were measured: they fit.
- Checked: tests pass; a fake `classroom_board_busy_birthday` in a scratch
  folder was loaded and shown only on the birthday; the gossip screen
  drawn for every mood. **Not heard by anyone yet:** a person should
  listen to the chalk loop (is it seamless, is 0.5 too loud), the
  footsteps and the new tear.

---

## Commit #39 — Gemini prompts for the mood pictures

- **Date:** 7 Oct 2026

### Summary

The team will make the mood pictures (NOTES #38) with Gemini, on another
computer. `IMAGE_PROMPTS.md` has every prompt complete, ready to paste:
for each picture which image(s) to upload, the prompt, and the file name
to save it as. 16 prompts: birthday B1–B8 (B8 is one prompt for the 10
optional side views), the dean's visit D1–D6, the new phone N1–N2.

### Added

| File | Purpose |
|---|---|
| `IMAGE_PROMPTS.md` | The prompts, how to use them, the order and how to check the results. |

### Changed

| File | Change |
|---|---|
| `README.md`, `PLAN.md` | Point to `IMAGE_PROMPTS.md`. |

### Details worth knowing

- Every prompt of a group repeats the same fixed description of the
  hat, cake, balloons and banner (BIRTHDAY SET), the suit and the dean
  (DEAN SET) or the phone (NEW PHONE SET): the team saw the cake in some
  birthday pictures and not in others in a first draft.
- B1, D1 and N1 are made first; the rest upload them as a second,
  reference image, so the look is the same everywhere.
- There is no cake in B5 and the side views on purpose: the teacher's
  desk is not in those pictures.
- Each prompt asks Gemini to keep the camera angle and the teacher's head
  in place: the warning scene zooms in on fixed spots of his face.

---

## Commit #40 — Calibration with four poses: screen, left, right, down

- **Date:** 8 Oct 2026

### Summary

First item of update 2 (PLAN.md section 12). Calibration only measured
"looking at the screen", and every player had to turn 18° to copy and tilt
23° to look down, whoever they were. Now it asks for four poses, one after
the other, each with a big arrow and one line saying what to do: look at
the screen, turn left, turn right, look down, each only *as far as you
would in the game while still seeing the screen*. The player gets into the
pose and presses Space; it is measured for a second (ding). The thresholds
are then 60 % of the way to each pose, so the game fits how this player
sits and moves. The menus use the same left/right turn.

### Added

| File | Purpose |
|---|---|
| `tracking/head_tracker.py` | `CALIBRATION_POSES`, `pose_threshold()`; `HeadTracker.left_threshold` / `right_threshold` / `down_threshold` and `set_thresholds()`. |
| `logic/menu.py` | `HeadMenuInput.set_turns()`; `pose()` takes the turns (defaults: the old fixed one). |
| `main.py` | `calibration_space()`: Space / Enter / a click on the button measures the pose; `calibrate_then(..., start_now)`. |
| `ui/draw_menus.py` | `POSE_TEXTS`, `READY_TEXT`, `pose_arrow()` (an arrow beside the preview, or a target for the screen). |
| `settings.py` | `CALIBRATION_SAMPLE_TIME` (1 s), `CALIBRATION_SHARE` (0.6), `CALIBRATION_MIN_ANGLE` (8°), `CALIBRATION_MAX_ANGLE` (35°). |
| Tests | The screen pose averages, nothing before Space, four poses set the thresholds and the game uses them, a lost face repeats the pose, looking down survives a hidden face, wrong way keeps the default, the limits; calibrated menu turns. 229 tests. |

### Changed

| File | Change |
|---|---|
| `tracking/head_tracker.py` | `Calibration` rewritten: poses in turn, `start()`, `restart_pose()`, `progress()`; `raw_direction()` uses the tracker's thresholds. |
| `main.py` | The start screen's Space measures the screen pose at once (it already asked for it); Recalibrate and K wait for Space. A camera gap repeats only the current pose. After calibrating, the menus get the turns. |
| `ui/draw_menus.py` | `draw_start()` takes the calibration: step "2/4", the pose, the hint, "READY (SPACE)" or the bar. |
| `README.md`, `LEARN.md`, `PLAN.md` | Calibration. |

### Removed

| File | What |
|---|---|
| `settings.py` | `CALIBRATION_TIME` (now `CALIBRATION_SAMPLE_TIME`, per pose). |

### Details worth knowing

- The screen pose is measured first, because the others are measured
  from it.
- `YAW_THRESHOLD` and `PITCH_DOWN_THRESHOLD` are still used before
  calibration and for a pose that went the wrong way or moved less than
  `CALIBRATION_MIN_ANGLE / CALIBRATION_SHARE` (13°).
- Looking down often hides the face from MediaPipe, so the down pose keeps
  measuring with the last angles seen instead of starting over.
- The menus never ask for more than `MENU_YAW_THRESHOLD`, but a player who
  turns little gets a smaller menu turn too.
- **A person should try:** calibrate with small turns (only the eyes off
  the screen's edge) and with big ones, and check that copying, looking down
  and the menus all feel right; if the game reacts too early, raise
  `CALIBRATION_SHARE` (e.g. 0.7), too late, lower it.

### Next

The score count as a table (PLAN.md 12, item 2).

---

## Commit #41 — The score count as a table

- **Date:** 8 Oct 2026

### Summary

Item 2 of update 2 (PLAN.md 12). The score count after an exam was a row
of question cards with the points floating over them and the bonuses
spread over one or two lines; the team found it hard to read. Now it is
two tables, still counted up like Balatro: on the left one row per
question (Q1, what you wrote, the answer key, RIGHT / WRONG / BLANK, the
points), and under them the grade; on the right one row per bonus. A row
glows in its colour when its turn comes and its points pop in, while the
big score counts up and thumps as before. The answer key of a row stays
"?" until its turn.

### Added

| File | Purpose |
|---|---|
| `ui/draw_results.py` | `question_table()`, `bonus_table()`, `table_frame()`, `table_row()`, `row_points()`, `aligned()`; `QUESTION_TABLE`, `BONUS_TABLE`, `TABLE_HEADER`, `TABLE_ROW`, `QUESTION_COLUMNS`, `RESULT_NAMES`, `ROW_FLASH_TIME`, `ROW_POP`. |

### Changed

| File | Change |
|---|---|
| `ui/draw_results.py` | `draw_tally()` draws the two tables; the score, the run total and the menu moved down a little (`TALLY_SCORE_Y` 352, `TALLY_RUN_Y` 400, `END_MENU_TOP` 450, `END_MENU_GAP` 50). |
| `README.md`, `LEARN.md` | The tables. |

### Removed

| File | What |
|---|---|
| `ui/draw_results.py` | The cards: `TALLY_CARDS_TOP`, `TALLY_CARD`, `TALLY_CARD_GAP`, `TALLY_POP`, `TALLY_POP_TIME`, `TALLY_BONUS_Y`, `TALLY_BONUS_ROW`, `TALLY_BONUS_GAP`. |

### Details worth knowing

- The timing did not change (`logic/tally.py`), so the tests did not.
- The tables have room for 5 questions + the grade and 7 bonuses (the
  characters, item 6, add one or two).
- The small points are plain text with a shadow, not neon: the pink and
  cyan ghosts made "+333" look like "#333".
- Checked: tests pass; drew the screen mid-count and at the end.

### Next

The practice exam after How to play (PLAN.md 12, item 3).

---

## Commit #42 — A practice exam after How to play

- **Date:** 8 Oct 2026

### Summary

Item 3 of update 2 (PLAN.md 12). After the guide, the player went back to
the main menu having never played a real exam. Now the guide leads into a
**practice exam**: two questions, 60 seconds, the teacher in a new
"practice" mood (reading the paper with his tea: busy 6–9 s, looks of
2.5–3.5 s, never leaves the board). It is a normal exam in every way
(loading screen saying "ME461 - PRACTICE", the classroom, the score
table), but it counts for nothing: no top score, no class average, no
grade. The end menu offers "Play for real" (a new run) or "Main menu".

### Added

| File | Purpose |
|---|---|
| `settings.py` | `PRACTICE_QUIZ` (2 questions, 60 s, hidden point 0.8); the `"practice"` mood. |
| `logic/run.py` | `Run(practice=True)`, `Run.quizzes`, `chapter()`. |
| `main.py` | `start_practice()`, `restart()` (R: the practice again, or a new run); "PLAY FOR REAL". |
| Tests | The practice is one short exam with the practice mood; it is at least as easy as the Quiz; chapters. 232 tests. |

### Changed

| File | Change |
|---|---|
| `main.py` | The finished guide starts the practice instead of going to the menu; END after the practice does not record the exam. |
| `logic/run.py` | `quiz()` and `is_over()` use the run's own list of exams. |
| `logic/guide.py` | The last step announces the practice exam. |
| `ui/draw_menus.py` | `draw_loading()` takes the chapter text (`run.chapter()`). |
| `ui/draw_results.py` | After the practice: "PRACTICE - NOT COUNTED" instead of the run total. |
| `README.md`, `LEARN.md`, `PLAN.md` | The practice exam. |

### Details worth knowing

- The practice skips the gossip slot machine: it would be a one-mood reel.
- Esc in the guide still goes straight back to the menu, without the practice.
- **A person should try:** finish How to play and play the practice; is it
  easy enough to win the first time, and short enough not to bore?

### Next

Answer keys without streaks (PLAN.md 12, item 4).

---

## Commit #43 — Answer keys without streaks

- **Date:** 8 Oct 2026

### Summary

Item 4 of update 2 (PLAN.md 12). Each right letter was drawn on its own,
so "A A A B" came often enough that the team thought it was a bug. The key
is still random, but now never has the same letter twice in a row, and no
letter more than twice in one exam. The neighbour who knows the answer is
also never the same side three times in a row.

### Added

| File | Purpose |
|---|---|
| `logic/exam_paper.py` | `answer_key()`, `knowing_sides()`. |
| `settings.py` | `MAX_SAME_LETTER` (2), `MAX_SIDE_STREAK` (2). |
| Tests | 500 seeds: no letter twice in a row, none too often, no long side streaks; every letter and both sides still come. 236 tests. |

### Changed

| File | Change |
|---|---|
| `logic/exam_paper.py` | `ExamPaper` uses them. |
| `LEARN.md`, `PLAN.md` | The rule. |

### Details worth knowing

- Why not a Tetris bag (each letter once)? With 4 questions the last
  letter could then be worked out from the first three without copying.
  "At most twice" leaves it open.
- If the limits are set so low that an exam cannot be filled, it falls
  back to "anything but the last letter" instead of crashing.

### Next

The slot-machine score (PLAN.md 12, item 5).

---

## Commit #44 — The slot-machine score

- **Date:** 8 Oct 2026

### Summary

Item 5 of update 2 (PLAN.md 12). The team wanted the score to feel like a
slot machine while it counts, more so the bigger it is (Balatro). The big
number is now a row of reels, one per digit, in the same gold frame with
bulbs as the MOOD-O-MATIC: while a part counts up every reel spins (the
units fastest, blurred), and when it stops each reel clunks onto its
digit. How wild it gets grows with the score as it climbs: the reels
shake harder, the bulbs chase faster, more sparks fly out with every
part, and the digits glow pink. A huge score (70 % of
`TALLY_FX_FULL_SCORE`, 4200 for an exam) ends with "JACKPOT!" flashing,
the digits flashing red and the fanfare. The run's total uses the same
machine (its jackpot needs three times as much).

### Added

| File | Purpose |
|---|---|
| `logic/tally.py` | `running_value()` (the score with its fraction), `is_counting()`, `strength()`, `jackpot()`. |
| `ui/draw_results.py` | `slot_score()`, `reel_frame()`, `reel_cell()`, `sparks()`; `REEL_*`, `DRUM_*`, `SPARK_*`, `JACKPOT_FLASH`, `RUN_TOTAL_SHIFT`. |
| `settings.py` | `TALLY_FX_FULL_SCORE` (6000), `TALLY_JACKPOT_SHARE` (0.7), `TALLY_SHAKE` (7 px), `TALLY_SPARKS` (36). |
| `main.py` | The fanfare for a jackpot. |
| Tests | The value rolls smoothly, counting only while a part counts, the strength grows with the score (and needs more for a run), the jackpot. 240 tests. |

### Changed

| File | Change |
|---|---|
| `logic/tally.py` | `running_score()` is `running_value()` as a whole number. |
| `ui/draw_results.py` | The exam's score and the run's total use `slot_score()`; a little more room under the tables (`TALLY_SCORE_Y` 356, `TALLY_RUN_Y` 412, `END_MENU_TOP` 460, `RUN_TOTAL_Y` 302). |
| `README.md`, `LEARN.md` | The slot machine. |

### Removed

| File | What |
|---|---|
| `ui/draw_results.py` | `thumped()` (the label still thumps, inside `slot_score()`). |

### Details worth knowing

- While counting, every reel shows `value / 10^place` with its fraction,
  so all reels spin, the higher ones slower: that is what makes it look
  like a slot machine rather than a car's odometer. Stopped, they snap to
  the whole digits.
- The sparks of a part always come out the same (`random.Random(part)`),
  so they do not flicker from frame to frame.
- The label's room is as wide as "JACKPOT!", so the reels do not jump
  when it flashes.
- Checked: drew the count mid-way (spinning, sparks) and at the end
  (jackpot), and the run's total. **A person should try:** is the shake too
  much? (`TALLY_SHAKE`); does a normal exam (2000–3000) feel calm and a
  great one wild? (`TALLY_FX_FULL_SCORE`).

### Next

Characters (PLAN.md 12, item 6).

---

## Commit #45 — Characters

- **Date:** 8 Oct 2026

### Summary

Item 6 of update 2 (PLAN.md 12.2). Before a run the player now picks who
they are on a new "WHO ARE YOU?" screen: a list on the left, and a card
with a neon portrait drawn in code, a one-line story and the + and −
lines. Each character bends one rule with an advantage and a price:

- **NPC with a Monster bag** — the plain game.
- **The guy with the cap** — staring and copying fill the suspicion bar
  slower (×0.75 / ×0.8), but while he is not looking at his paper the bar
  creeps up (full in 45 s), even when the teacher is busy.
- **Glasses** — reads a neighbour's paper 25 % faster, but every time he
  looks at the teacher the classroom is blurry and takes 0.9 s to get sharp.
- **The nerd** — one joker per exam (J while looking down writes the right
  answer), but must hand in with 30 % of the time left or lose 1000 points
  ("TOO SLOW FOR A NERD!" when the moment passes, "NERD WAS LATE" in the
  score table).
- **Energy drink addict** — a coin toss every exam: a sugar rush (the
  teacher, the clock and the bar run at 85 %, his eyes at full speed) or a
  crash (every 8–14 s a sleepy spell of 3.5 s: eyelids close, "Z z z",
  reading at 40 %).
- **The teacher's buddy** — the teacher is busy 35 % longer, but watches
  35 % longer too.
- **Lazy but funny** — both neighbours show him the answer, but the bar
  fills faster when the teacher sees him (×1.4 copying, ×1.3 staring), and
  there is no sharp-eye bonus.

All the numbers are one table, `CHARACTERS` in `settings.py`; the rules
read them through `logic/character.py`, so tuning a character, or adding
one, needs no new code. In the game a badge at the top left says who you
are, with the nerd's jokers and deadline or the energy drink's day; the
loading screen says "PLAYING AS". "Play again" keeps the character; the
practice exam is always the NPC. The guide mentions the characters.

### Added

| File | Purpose |
|---|---|
| `logic/character.py` | `DEFAULTS`, `rules()`, `names()`, `screen_clarity()`, `Energy` (`RUSH` / `CRASH`). |
| `ui/draw_characters.py` | The character screen: `draw_characters()`, `character_list()`, `character_card()`, `portrait()` and one `portrait_<key>()` per character. |
| `settings.py` | `CHARACTERS` (with what each rule means), `DEFAULT_CHARACTER`. |
| `logic/game.py` | `character`, `rules`, `jokers`, `use_joker()`, `deadline()`, `missed_deadline`, `energy`, `world_speed()`, `focus_speed()`, `is_sleepy()`; the "NERD WAS LATE" part. |
| `logic/exam_paper.py` | `both_know`, `right_answer()`. |
| `ui/draw_game.py` | `character_badge()`, `eyelids()`; the classroom blurred by `clarity`; the joker hint. |
| `ui/sounds.py` | `joker`, `nerd_late`, `sleepy`, `awake`. |
| `main.py` | The CHARACTER screen, `choose_character()`, `self.character`, the J key. |
| `tests/test_character.py` | Every character's rule, its price, and that `CHARACTERS` has no unknown (misspelled) rules. 257 tests. |

### Changed

| File | Change |
|---|---|
| `logic/suspicion.py` | `SuspicionBar(seen_speed, stare_speed, creep_time)`; `update(..., away=)`. |
| `logic/neighbours.py` | `update(..., speed=)`. |
| `logic/teacher.py` | `set_mood(mood, busy_times, watching_times)`. |
| `logic/run.py` | `Run(character=)`, given to every `Game`. |
| `logic/game.py` | The clock and the bar run on `dt * world_speed()`; `knows_answer()` checks both sides; no sharp eye when both know. |
| `main.py` | PLAY and "Play for real" go to the character screen; the teacher runs on `dt * world_speed()` and gets the buddy's times. |
| `ui/draw_menus.py` | `draw_loading(..., character)`: "PLAYING AS". |
| `ui/render.py` | `CharacterDrawing` in the Renderer. |
| `logic/guide.py` | One line about the characters. |
| `README.md`, `LEARN.md`, `PLAN.md` | The characters. |

### Details worth knowing

- The cap's bar creeps up instead of draining whenever he looks at the
  screen or a neighbour without anything suspicious happening; only
  looking down drains it. A full creep is a normal warning.
- The sugar rush slows the world, not the player: the clock, the bar and
  the teacher get `dt * 0.85`, reading gets the full `dt`.
- The tables of the score count have room for the extra "NERD WAS LATE" row.
- Checked: tests pass; drew the character screen for all seven, the
  nerd's badge looking down, the glasses' blur and the sleepy eyelids;
  ran the real `App` with a fake camera through: Play → character → spin
  → exam with the joker → the score count, one exam with every character,
  and the guide → practice → "Play for real" → the character screen.
  **A person should try:** play a run with each character and say which
  feels too strong or too weak (the numbers are all in `CHARACTERS`); is
  the glasses' blur fair; are the sleepy spells annoying in a good way;
  can the nerd make the 30 %?

### Next

Play update 2 with the webcam and tune (PLAN.md 12.3).

---

## Commit #46 — The New Era guy's bar, a Monster laptop, funnier characters

- **Date:** 8 Oct 2026

### Summary

After trying the characters the team asked for four things. The cap's
creeping bar was too slow to matter: it now fills in 30 s instead of 45.
In exchange his normal bar (staring and being seen copying) fills slower
than before: ×0.6 staring (a warning after 5 s instead of 3) and ×0.65
seen (caught after 1.08 s instead of 0.7). Everyone else's bar is
unchanged. "The guy with the cap" is
**the New Era guy**: a stiff, flat-brim cap with the gold sticker still on
(the portrait was redrawn). The "Monster bag" is a bag for a **Monster
gaming laptop** (the computer brand), not energy drinks: new story and a
new portrait (a laptop bag, the laptop's edge glowing in changing colours).
And every character's lines were rewritten to be funnier. The nerd's
early bonus now counts from his 30 % line: 0 with 30 % of the time left,
growing to the full +1000 with all of it left (before, he got the normal
bonus on top of the deadline); later than 30 % is still −1000.

### Changed

| File | Change |
|---|---|
| `settings.py` | The cap: `creep_time` 45 → 30, `stare_speed` 0.75 → 0.6, `seen_speed` 0.8 → 0.65; new name, story and +/- lines for every character. |
| `logic/game.py` | The early bonus is measured from `hand_in_share` (the nerd's line; 0 for everyone else, so nothing changes for them). |
| `tests/test_character.py` | The nerd's early bonus: 0 at the line, half way between the line and the start = half the bonus. 258 tests. |
| `ui/draw_characters.py` | `portrait_cap()`: a New Era cap (tall crown with "NY", a flat brim, the gold sticker); `portrait_npc()`: a laptop bag with a glowing gaming laptop. `GREY_BAG`, `CAP_NAVY`, `GOLD_STICKER` instead of `MONSTER_GREEN`. |
| `README.md`, `PLAN.md` | The names and the cap's 30 s. |

### Details worth knowing

- The cap's key in `CHARACTERS` is still `"cap"`.
- Checked: tests pass (258); drew the two new portraits and cards.
  **A person should try:** does the New Era guy now have to look at his
  paper often enough, and is his slower bar worth it?

### Next

Play update 2 with the webcam and tune (PLAN.md 12.3).

---

## Commit #47 — Fewer sugar rushes, an easier practice, the forgotten line, no face on screen

- **Date:** 8 Oct 2026

### Summary

Four requests after playing:

- **The sugar rush came too often.** The energy drink addict's coin toss
  is now a chance: 50 % in the first exam, 15 % less after every sugar
  rush earlier in the run (50 → 35 → 20 %).
- **A joke about the hidden suspicion line, in the guide.** A new guide
  step: you don't have to empty the bar, but leave it too high and he
  keeps staring at you; how high is too high? "I put a random line in the
  code." "Where is it?" "No idea. I forgot. Good luck!" (That line is the
  exam's `"suspicious"` point in `QUIZZES`: 60 / 45 / 30 %.)
- **The practice exam at 75 %.** `PRACTICE_QUIZ` has `"ease": 0.75`:
  the suspicion bar fills at 75 % of its speed, the teacher's looks are
  75 % as long, and a paper is read in 75 % of the time.
- **No face on screen.** The webcam picture is gone from the game, the
  guide and the menus; it is only on the start screen, while calibrating
  (the poses need it). The "HEAD CONTROL" box sits at the bottom right on
  every menu.

The team also asked for the suspicion bar's drain value, to tune it:
`SUSPICION_DRAIN_TIME = 10.0` in `settings.py` (seconds for a full bar to
empty; lower = faster). Not changed: the team will try values.

### Added

| File | Purpose |
|---|---|
| `logic/character.py` | `rush_chance()`; `Energy(rng, rules, rushes_before)`; `rush_chance`, `rush_chance_drop` in `DEFAULTS`. |
| `logic/run.py` | `rushes()`; each result remembers `"rush"`. |
| `logic/game.py` | `Game(rushes_before=, ease=)`: the bar's speeds x ease, reading / ease. |
| `logic/guide.py` | The step about the forgotten line. |
| `settings.py` | The energy drink: `rush_chance` 0.5, `rush_chance_drop` 0.15; `PRACTICE_QUIZ` `"ease": 0.75`. |
| Tests | The rush chance drops, a run counts its rushes, the practice is easier; the crash test steps until the spell starts (it failed when the first spell came early). 261 tests. |

### Changed

| File | Change |
|---|---|
| `main.py` | No webcam picture in the game, the guide and the menus; `menu_screen()`, `guide_screen()`, `game_screen()` no longer take the frame; the teacher's looks x `game.ease`. |
| `ui/draw_game.py`, `ui/draw_guide.py`, `ui/draw_menus.py` | The preview is gone; the texts that sat left of it are centred. `MENU_PREVIEW_SIZE` is now `INDICATOR_WIDTH` (also used by the briefing, characters and results). |
| `README.md`, `LEARN.md`, `PLAN.md` | The above. |

### Details worth knowing

- The tracker still draws on the start screen only; the yaw/pitch numbers
  and "face lost..." stay at the top right of the game.
- **A person should try:** with no face on screen, is it still clear when
  tracking is lost? (The game pauses with "FACE NOT FOUND", as before.)
  Try `SUSPICION_DRAIN_TIME` at 6–8 s.

### Next

Play with the webcam and tune (PLAN.md 12.3).

---

## Commit #48 — A briefing timed to the character music; the sliding character screen

- **Date:** 8 Oct 2026

### Summary

The team added a song for choosing the character
(`assets/sounds/character_[cut_180sec].mp3`) and asked for a cool,
sarcastic intro timed to it, then a Hotline Miami-like sliding character
screen where the chosen one stands out.

Claude cannot hear, so the song was measured with numpy instead (decoded
with pygame): the onsets (where the sound suddenly changes) give the tempo
by autocorrelation, **147 BPM**; the strongest hits come every 1.633 s
(a bar of 4 beats) from **0.81 s**; and the loudness jumps to twice its
level at **11.84 s** (the drop), which is on the same beat grid.

- **The briefing** (new screen RUN_INTRO, after PLAY): the music starts at
  once, and on each bar's hit a new line slams in, huge and tilted, with a
  white flash and a shake, over rushing diagonal stripes whose colours
  change each line: "3 EXAMS." "1 SEMESTER." "0 HOURS OF STUDYING."
  "YOUR FAMILY EXPECTS..." "...THE MAXIMUM SCORE." "NO PRESSURE." "(A LOT
  OF PRESSURE.)". The line thumps on every beat in between. Space / Enter /
  turning right skips it; left goes back.
- **The character screen** at the drop: the row of portraits slides in
  from the right with a white flash. The chosen one is in the middle, big,
  in a yellow frame with a pink halo that flares on every bar, thumping on
  every beat; the others are smaller and darker the further away. Tilting
  up/down slides the row (smoothly, the short way round). Under it the
  name (big), the story and the + / − lines.

### Added

| File | Purpose |
|---|---|
| `logic/run_intro.py` | `INTRO_LINES`, `BEAT`, `BAR`, `line_time()`, `current_line()`, `since_line()`, `is_over()`, `since_beat()`, `beat_number()`, `since_bar()`. |
| `ui/draw_run_intro.py` | `draw_run_intro()`, `intro_line_image()`, `intro_stripes()`. |
| `ui/sounds.py` | The `"character"` track; `cut_to()` (start at once, no fade), `music_position()`. |
| `main.py` | RUN_INTRO: `start_run_intro()`, `intro_screen()`, `music_time()`; `self.carousel`, `self.character_since`. |
| `settings.py` | `CHARACTER_MUSIC_BPM` (147), `INTRO_FIRST_HIT` (0.81 s), `INTRO_DROP` (11.84 s), `CAROUSEL_SPEED`. |
| `tests/test_run_intro.py` | Lines one per bar, all before the drop, the drop on a beat, beats and bars. 266 tests. |

### Changed

| File | Change |
|---|---|
| `ui/draw_characters.py` | The list and card became the sliding row (`carousel()`, `chosen_glow()`, `portrait_image()`, `character_info()`). |
| `main.py` | PLAY and "Play for real" go to the briefing; the character music on RUN_INTRO and CHARACTER. |
| `ui/render.py` | `RunIntroDrawing` in the Renderer. |
| `README.md`, `LEARN.md`, `PLAN.md` | The briefing and the row. |

### Details worth knowing

- The intro follows the music player's position (`get_pos()`), not a timer
  of its own, so a slow frame does not knock it off the beat. Without a
  real sound device the player says 0, and `music_time()` counts by itself.
- The file name has brackets in it; the code uses it as it is. Renaming it
  means changing `MUSIC_FILES` in `ui/sounds.py`.
- Choosing PLAY with the head: the briefing waits until the head is
  straight before turning right can skip it.
- Checked: drew the briefing at several moments and the row (still,
  sliding, opening); ran the real `App` (fake camera, no sound device):
  PLAY → briefing → characters at the drop, Space skips, the row slides.
  **A person should listen:** do the lines land on the hits? If they are
  a little early or late, change `INTRO_FIRST_HIT` (and `INTRO_DROP` by the
  same amount).

### Next

Play with the webcam and tune (PLAN.md 12.4).

---

## Commit #49 — Exam title cards, the character music on the first spin, a cleaner intro

- **Date:** 8 Oct 2026

### Summary

- **Title cards.** After the loading bar fills, a quick card (1.8 s) in
  the briefing's style: the exam's name slams in with a flash and a thud,
  then its sarcastic line: "THE QUIZ — This gotta be easy... right?",
  "THE MIDTERM — I can handle this. Probably. Maybe not.", "THE FINAL —
  God, please help me.", and for the practice "It doesn't even count.
  Relax." Each exam has its own colours; the card fades to black into the
  exam.
- **Music.** The first exam's gossip slot machine keeps the character
  music going (it follows the character screen); from the second exam on
  it is the menu theme again.
- **The briefing.** The team liked how it sits on the rhythm, but the
  line before (small and faded above the new one) is gone: only the newest
  line is on screen.

### Added

| File | Purpose |
|---|---|
| `settings.py` | A `"tagline"` for each exam in `QUIZZES` and for `PRACTICE_QUIZ`; `EXAM_TITLE_TIME` (1.8 s), `EXAM_TAGLINE_DELAY` (0.45 s). |
| `ui/draw_run_intro.py` | `draw_exam_title()`, `EXAM_PALETTES`, `TITLE_Y`, `TAGLINE_Y`. |

### Changed

| File | Change |
|---|---|
| `main.py` | `loading_screen()`: the bar, then the title card (a `"stamp"` thud on each slam), then the exam; `music_track()`: the character music on the first BRIEFING. |
| `ui/draw_run_intro.py` | The faded line before is no longer drawn. |
| `README.md`, `LEARN.md` | The above. |

### Details worth knowing

- A long tagline is made smaller to fit (the midterm's).
- Checked: tests pass (266); drew all four cards; ran the real `App`:
  the first BRIEFING plays "character", the second "menu", and LOADING
  goes through the card into the game.
  **A person should try:** is 1.8 s too long when you just want to play?
  (`EXAM_TITLE_TIME`)

---

## Commit #50 — The school bell, a sideways character row, "Are you sure?"

- **Date:** 8 Oct 2026

### Summary

- **The school bell** (the team's file, `School Bell Sound Effect ...mp3`,
  3.4 s) rings on the title card before each exam, and only there. It is
  cut to the card's length (`EXAM_TITLE_TIME`, 1.8 s) and fades out over
  its last 0.35 s, so bell and card end together; a different card length
  cuts it to that. Without the file, a bell made in code rings instead.
- **The character row is chosen sideways:** turn left / right to go to the
  previous / next character, look down (hold) to play as him, look up
  (hold) to go back. Keys: ← → move, ↓ / Enter choose, ↑ / Esc back.
- **"ARE YOU SURE?"** for QUIT and MAIN MENU (and Esc on the main menu):
  a box over the menu; turn right *again* (the head must come straight
  first) or Enter = yes, turn left or Esc = no. A bar under each answer
  fills while the head is turned. Going to the main menu in the middle of
  a run says the run is lost.

### Added

| File | Purpose |
|---|---|
| `ui/sounds.py` | `"bell"` in `SOUND_FILES`; `SOUND_LENGTHS`, `CUT_FADE_TIME`; `fade_out()`, `cut_sound()`, `Sounds.cut()`, `school_bell()` (the stand-in). |
| `logic/menu.py` | `HORIZONTAL`, `HeadMenuInput.horizontal`. |
| `main.py` | `self.confirming`, `ask_confirm()`, `answer_confirm()`; the character row's keys. |
| `ui/draw_menus.py` | `draw_confirm()`. |
| Tests | `tests/test_sounds.py` (cutting and fading a sound, the bell's length); the sideways menu. 272 tests. |

### Changed

| File | Change |
|---|---|
| `main.py` | The title card rings the bell; `go_to()` sets the sideways head on the character screen and clears the question; clicks wait while it is asked. |
| `ui/draw_characters.py` | The hint for the sideways controls. |
| `README.md`, `LEARN.md` | The above. |

### Details worth knowing

- R and M in the game, and Esc in the game, still act at once (only the
  menu items and Esc on the main menu ask).
- **A person should try:** is looking down to pick a character easy, or
  does it fire while just looking at the keyboard? (`MENU_PITCH_THRESHOLD`,
  `MENU_SELECT_TIME`); listen to the cut bell.

---

## Commit #51 — A real slot machine for the gossip; the helicopter signature

- **Date:** 8 Oct 2026

### Summary

- **The gossip screen** was a flat rectangle with the machine and the
  story floating in it. Now it is one slot machine in the middle of the
  screen, drawn in code: a cabinet with a dome and a neon edge, a drop
  shadow, "MOOD-O-MATIC" glowing on the dome with bulbs round it
  (blinking while waiting, chasing while spinning, all flashing when it
  stops), the gold-framed reel with a glass gleam, the lever fixed to its
  side. The moods on the reel are wrapped to two lines instead of being
  shrunk. Under the reel, built into the machine, a glowing screen: before
  the spin it blinks "PULL THE LEVER"; after it, the story and the + / −
  lines light up there. "SPIN" / "I'M READY" sit on the machine's base.
  (A first try printed the story on a typewritten receipt; the team wants
  only the slot machine, so it was dropped.)
- **The disclaimer's signature** is someone trying to draw a helicopter:
  body, window, tail with its rotor, mast, the big rotor scribbled back
  and forth, skids, in a shaky hand, drawn stroke by stroke. Nothing else
  on the notice changed.

### Changed

| File | Change |
|---|---|
| `ui/draw_briefing.py` | Rewritten: `cabinet_shape()`, `cabinet()`, `marquee_image()`, `reel_frame_gold()`, `reel_line()`, `glass()`, `slot_lever()`, `info_screen()`; `draw_briefing(..., chapter)`. The box (`BRIEFING_PANEL`) and `slot_cabinet()` / `mood_story()` are gone. |
| `ui/draw_notice.py` | `signature()` draws `helicopter_strokes()`; `shaky()`, `oval()`, `line()`. |
| `main.py` | Passes `run.chapter()` to the gossip screen ("CHAPTER 1/3"). |
| `README.md`, `LEARN.md` | The machine and the helicopter. |

### Details worth knowing

- The cabinet's shape and gradient are made once (`neon_cache`); the
  outline for the neon edge comes from `pygame.mask`.
- Checked: tests pass (272); drew the gossip screen before, during and
  after a spin for every mood, and the signature half and fully drawn.

---

## Commit #52 — Fix: the gossip machine's screen stayed dark

- **Date:** 8 Oct 2026

### Summary

The team saw the story and the + / − lines hidden behind black on the
MOOD-O-MATIC's screen. `turn_reel()` in `main.py` stopped counting
`spin_time` once the reel stopped, but the screen lights up over
`INFO_LIGHT_TIME` *after* the stop (and the bulbs' win flash ends after
`WIN_FLASH_TIME`), so the screen stayed almost black and the bulbs
flashed forever. The clock now keeps going after the stop.

### Changed

| File | Change |
|---|---|
| `main.py` | `turn_reel()`: after the stop, `spin_time` keeps counting. |

### Details worth knowing

- The test drawings in #51 set `spin_time` by hand, past the light-up, so
  they did not show it. This time it was checked through the real `App`:
  spin, wait 6 s, the screen is lit.

---

## Commit #53 — Casino bulbs round the slot machine

- **Date:** 8 Oct 2026

### Summary

The team wanted small yellow bulbs all round the MOOD-O-MATIC, blinking
like a casino sign: one lit, the next dark, then the other way round. They
sit on its neon edge, one every 24 pixels along the outline; every other
one is lit and they swap every 0.35 s (three times as fast while the reel
spins), so the light seems to jump along. The old row of bulbs inside the
dome is gone: the two rows were too busy together.

### Changed

| File | Change |
|---|---|
| `ui/draw_briefing.py` | `edge_bulb_spots()` (made once from the outline), `edge_bulbs()`; `EDGE_BULB_GAP`, `EDGE_BULB_SWAP`; the dome's own bulbs removed. |
| `LEARN.md` | The bulbs. |

### Details worth knowing

- Checked through the real `App` (spin, wait, draw): the bulbs follow the
  dome and the rounded corners evenly. Tests pass (272).

---

## Commit #54 — The moods do what their gossip says

- **Date:** 8 Oct 2026

### Summary

The team asked whether the teacher really behaves as each mood's + / −
lines promise. Every line was checked against the numbers, with
`normal_day` (busy 3.5–6.5 s, looks 4–7 s, moves 40 %) as the plain
teacher. Most were right; these were not:

| Mood | Line | Was | Now |
|---|---|---|---|
| `phone_fight` | "+ Long calls, and he stays at his desk" | started at the **board**, moved 15 % of the time | starts at the desk (`"place": "DESK"`), moves 5 % |
| `phone_fight` | "− When he looks, he looks for a while" | looks 4.5–6.5 s (avg 5.5 = normal) | 5.0–7.5 s |
| `traffic` | "− Long, angry looks" | 4.5–7.0 s (+5 %) | 5.0–8.0 s (+18 %) |
| `motorcycle` | "− Long, angry stares" | 4.5–7.5 s (+9 %) | 5.0–8.0 s (+18 %) |
| `paranoid` | "− Long looks" | 4.5–7.0 s (+5 %) | line removed (it still barely works and keeps moving) |
| `lost_bet` | "− Long looks" | 4.5–7.5 s (+9 %) | line removed (short busy times, moves a lot) |

For the Final's moods the line was removed rather than the looks made
longer, because the team finds the game hard already.

### Added

| File | Purpose |
|---|---|
| `tests/test_moods.py` | Reads every + / − line, finds its promise by keywords ("long busy", "quick", "never leaves the desk", "keeps moving"...) and checks the numbers against `normal_day` (10 % longer / shorter at least); every line must be checked by some keyword; good-only days are not harder than plain, bad-only days not easier. 275 tests. |

### Changed

| File | Change |
|---|---|
| `settings.py` | The numbers and lines above; the comment over `MOODS` points to the test. |

### Details worth knowing

- The test was tried against the old numbers: it fails on `phone_fight`.
- A new mood line needs its words in `KEYWORDS` (`test_every_line_is_checked`
  says so), so a promise can never go unchecked.
- `phone_fight` at the desk means no chalk sound on that day (he is on the
  phone): that matches the story ("arguing at his desk").

---

## Commit #55 — Version 0.1 beta as a Windows .exe (branch `release-0.1-beta`)

- **Date:** 8 Oct 2026

### Summary

The team wants a version anyone can play, on computers without Python:
**0.1 beta**, as one Windows .exe that has everything inside (Python,
OpenCV, MediaPipe, pygame, the pictures, the sounds, the face model). A
.exe can only be built on Windows, so GitHub builds it on its own Windows
computers on every push to this branch, runs the tests first, and keeps
the .exe as the run's artifact. The .exe is never committed (it is about
200 MB, over GitHub's 100 MB file limit, and the team asked to keep it off
`main`). This branch is `main` (b6a7d33) plus the build.

### Added

| File | Purpose |
|---|---|
| `packaging/build_exe.py` | Runs PyInstaller: one file, no console window, `assets/` and `face_landmarker.task` inside, all of MediaPipe; named from the version (`DontGetCaught-0.1-beta`). |
| `.github/workflows/build-windows.yml` | Windows build: Python 3.14, the libraries + PyInstaller, the tests, the build, the .exe uploaded as an artifact. |
| `settings.py` | `GAME_VERSION = "0.1 beta"`. |
| `main.py` | `FROZEN`, `GAME_FOLDER`: inside the .exe it works from the unpacked folder (`sys._MEIPASS`), keeps `highscore.json` next to the .exe and writes messages and errors to `dont-get-caught-log.txt` there (there is no console). |

### Changed

| File | Change |
|---|---|
| `main.py` | The window title says the version; `HIGH_SCORE_PATH` uses `GAME_FOLDER`. |
| `ui/draw_menus.py` | "v0.1 beta" at the bottom left of the main menu. |
| `.gitignore` | `dist/`, `packaging/work/`, the log. |
| `README.md` | How to play the .exe and how it is built. |

### Details worth knowing

- PyInstaller is a build tool, not a game library: it is installed only
  to build (in the workflow), not in `requirements.txt`.
- Checked: a Linux build of the same script (211 MB) started from an
  empty folder: the face model loaded from inside, the camera opened, it
  ran without errors and wrote its log next to itself. The Windows build
  runs on GitHub. **A person should try** the .exe on a Windows computer
  without Python: does it start, does the webcam work, are scores kept?

---

## Commit #56 — No .exe: run.bat installs Python by itself; Windows camera made sturdier (branch `release-0.1-beta`)

- **Date:** 8 Oct 2026

### Summary

The team dropped the .exe (#55): Windows players use **`run.bat`**, and it
must work on a computer without Python. And the camera should be set up
properly for Windows.

- **`run.bat`** now finds a usable Python (an existing `.venv`, then
  `py -3.14` / `-3.13` / `-3.12`, then `python`): it must run (the
  Microsoft Store's `python` shortcut does not), be 64-bit and 3.10–3.14
  (MediaPipe). If there is none it installs **Python 3.14 for this user
  only, without an admin password**: with `winget` (`Python.Python.3.14`)
  if Windows has it, otherwise it downloads the installer from python.org
  with PowerShell and runs it quietly. Then `.venv`, the libraries, the
  game, as before. A `.venv` that no longer works is made again.
- **Windows camera.** Windows has two camera systems: DirectShow (opens a
  webcam fast) and Media Foundation (slow to open, works with every
  webcam). Before, only one was used and a webcam that did not work with it
  needed `WINDOWS_DIRECTSHOW = False` by hand. Now each webcam is tried with
  both (DirectShow first) before the next webcam; once one sends pictures it
  is kept. On Windows the game also asks for 640×480 and a one-picture
  buffer (less delay), and when a webcam opens but sends nothing, the
  waiting screen names the camera system and tells where Windows' camera
  privacy setting is.
- The .exe build (`packaging/`, the GitHub workflow, the code for running
  inside a .exe) is removed again; the version name "0.1 beta" stays.

### Added

| File | Purpose |
|---|---|
| `tracking/camera.py` | `camera_systems()`, `open_device(index, system)`, `describe()`, `SYSTEM_NAMES`, `PRIVACY_HINT`; `Camera.attempts` (every webcam × camera system), `selected_system`, `pending_system`. |
| `settings.py` | `WINDOWS_CAMERA_SIZE` (640×480); `WINDOWS_DIRECTSHOW` now means "DirectShow first". |
| `tests/test_camera.py` | `WindowsTests`: the systems' order, the size and buffer, the same webcam with the other system before the next webcam. The other camera tests act as on Linux everywhere (they failed on GitHub's Windows computer, which sends the extra DirectShow code). 278 tests. |

### Changed

| File | Change |
|---|---|
| `run.bat` | Rewritten as above (CRLF line endings, like before). |
| `main.py` | The .exe code (`FROZEN`, `GAME_FOLDER`, the log) removed. |
| `README.md` | "Windows: double-click run.bat"; the Windows setup and webcam tips. |
| `.gitignore` | The .exe build folders removed. |

### Removed

| File | What |
|---|---|
| `packaging/build_exe.py`, `.github/workflows/build-windows.yml` | The .exe build. |

### Details worth knowing

- **Not run on Windows by anyone yet** (this computer is Linux). Checked
  here: the python.org download link answers (HTTP 200) and winget has
  `Python.Python.3.14`; the camera logic is tested with a fake Windows.
  **A person should try**, on a Windows computer *without* Python: unzip,
  double-click `run.bat`, wait for Python and the libraries, play; then
  double-click it again (it should start at once). And a webcam that only
  works with Media Foundation.
- Installing Python per user puts it in
  `%LOCALAPPDATA%\Programs\Python\Python314`; `run.bat` uses that path
  directly, because the new PATH only reaches new windows.
