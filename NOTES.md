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

## Commit #12 — Visible exam papers and keyboard answers

- **Date:** 6 Oct 2026

### Summary

Created `me461-python-visual-tracking-app2-gp` as a complete copy of the original
project. The player now sees their own paper and marked neighbour papers,
remembers A..E choices, returns to their own paper and writes with the keyboard.
All five answers must match the exam key to win. No commit was made for this update.

### Added

| File | Change |
|---|---|
| `game.py` | Stable random exam key, left/right neighbour marks, blank player marks, selected question, answer entry/revision and correct-answer score. |
| `render.py` | Full and compact paper layouts, numbered placeholder lines and A..E bubbles, selected row, wooden desk and final score. Turkish labels use DejaVu Sans. |
| `settings.py` | Answer choices and paper/desk sizes, colours and fonts. |
| `tests/test_input.py` | Tests for all answer keys, C/D conflicts, arrows and fresh head direction/paused input in the main loop. |

### Changed

| File | Change |
|---|---|
| `main.py` | Queue answer keys until current head tracking; reject them while sideways, paused or finished. F2 recalibrates and F3 shows teacher state, freeing C and D for answers. |
| `game.py` | Only manual answers write marks; five correct answers win, and incorrect completed papers remain editable. Existing suspicion, warnings, teacher risk and 90-second clock remain. |
| `render.py` | Forward view shows the teacher above a compact own paper; down/side views show a full paper without the teacher. HUD counts actual filled rows and displays writing instructions. |
| `tests/test_game.py` | Replace automatic copying tests with manual writing, neighbour stability, revision, wrong-answer recovery, reset and input guards. |
| `README.md`, `LEARN.md`, `PLAN.md` | Document the new reading/writing loop, controls and current timings; README includes Turkish playing instructions. |
| `.venv/bin/` | Update copied launchers' absolute paths to the new folder. Assets, models, original tracker and other source files are retained. |

### Removed

| Item | Why |
|---|---|
| Automatic answer filling, copy timer/lock and copy progress bar | Looking sideways reads another paper; keyboard input writes the player's answer. |
| `COPY_TIME`, `TICK_INTERVAL` settings | Timed automatic copying no longer runs. Sound assets and generated effects remain available. |

### Details worth knowing

- Both neighbours display the same correct key for this exam. The key is fixed
  during play and regenerated on restart. The player's marks are a separate list.
- A..E works while facing forward or looking down. Each answer selects the next
  blank question. Up / Down wraps through the paper to revise existing marks.
- A full but incorrect paper gives an overall review hint without showing which
  answers are wrong. The end screen reports the number of correct answers.
- Sideways keys do not secretly write; paused/calibrating/end-screen keys do not
  carry into play. Tests exercise the actual main-loop input ordering with mocks.
- Paper drawings use pygame shapes; no new dependency or generated image is needed.
  Exams longer than five questions use pages based on the selected question.
- Validation: 75 tests passed. Headless rendering checked all four directions,
  teacher views, feedback, pause and end screens. Real webcam/game feel still
  needs a person to check.

### Next

1. Run `./run.sh` in the new folder. Calibrate while facing forward; look left
   and right and check that each paper has five marked choices.
2. Return forward/down and answer with all five letter keys; check auto-advance,
   arrows and revisions. Try an incorrect full paper, then fix it to win.
3. Check F2 calibration, F3 testing overlay, R restart and F11 fullscreen.
   Leave the camera and confirm keys do not write while paused; look sideways
   during WATCHING and confirm the alarm and caught rules still work.


---

## Commit #13 — Keep the game open during camera failures

- **Date:** 6 Oct 2026

### Summary

The old reader stopped permanently after a single failed frame, and main.py
then closed the game. Camera startup and recovery now run in the background;
missing/stale pictures pause the exam while the reader retries and reconnects.

### Added

| File | Change |
|---|---|
| `camera.py` | First-frame validation, preferred-camera fallback, failed-frame retries, stale-frame limit, reconnect status and safe worker-owned capture release. |
| `settings.py` | Camera warm-up, stale/reconnect/retry/stop timings and fallback indices. |
| `render.py` | Camera waiting screen with status; quit remains available. |
| `tests/test_camera.py` | Simulated startup failures, empty frames, exceptions, retries, fallback, reconnection, frame ownership and shutdown. |

### Changed

| File | Change |
|---|---|
| `main.py` | Pause instead of exit when no frame exists; discard keys and elapsed waiting time; restart calibration after gaps. Finally release camera/tracker even if initialization or drawing fails. |
| `head_tracker.py` | Clear stale face/angle guesses after camera gaps while preserving calibration and MediaPipe timestamp order. |
| `tests/test_input.py`, `tests/test_head_tracker.py` | Verify paused camera input, recovery, quit before first picture, cleanup after initialization errors and stale direction reset. |
| `README.md`, `LEARN.md`, `PLAN.md` | Document retries, camera selection and new reader behavior. |

### Removed

| Item | Why |
|---|---|
| Fatal single-frame failure and blocking initial frame wait | A missing frame can be temporary; the window should remain responsive. |

### Details worth knowing

- Prefer camera 1; before the first valid picture, camera 0 is also tried.
  Once a working device is found, reconnection stays with it. Set
  `CAMERA_FALLBACK_INDICES = ()` to disable initial fallback.
- `isOpened()` alone does not prove that a camera produces images. Initial
  frames have a warm-up period; one missing frame is retried instead of closing.
- `read()` returns a copy so drawing face overlays does not mutate the saved
  camera frame. Images older than 0.5 seconds cause a pause.
- Only the worker releases OpenCV's capture, avoiding concurrent read/release.
  Some drivers can block in read; the window still pauses/quits, but a blocked
  driver may delay the worker's reconnection until its read returns.
- A physical camera is unavailable in this environment. Recovery is verified
  using mocks/fake time and the actual main-loop input order.

### Next

Run the game with the real camera. Check first-frame startup, camera selection
in the terminal, a short interruption and reconnection. Close other camera
apps if the device remains unavailable; Q/Esc should work while waiting.

---

## Commit #14 — Hide own paper from teacher view; focus one neighbour question

- **Date:** 6 Oct 2026

### Summary

Looking at the teacher no longer displays the own-paper overlay. Left/right
looks show only the selected question, initially question 1. The neighbour
paper starts blurred and becomes sharp over 2.5 seconds of continuous looking.

### Added

| File | Change |
|---|---|
| `game.py` | Per-neighbour focus timer, clarity property and reset helper. |
| `render.py` | Single-question neighbour layout and gradual Gaussian blur limited to the paper. |
| `settings.py` | Neighbour paper/row layout, focus duration, blur strength and working blur size. |
| `tests/test_render.py` | Actual headless checks for hidden own paper, one neighbour question, progression, sharp own paper, gradual edge contrast and read-only rendering. |

### Changed

| File | Change |
|---|---|
| `game.py` | Looking away, switching sides, answering, revisiting questions and restarting reset paper focus. Focusing never writes an answer. |
| `main.py` | Face/camera gaps and recalibration reset focus; pause time cannot make the paper sharp. |
| `render.py` | SCREEN shows only the classroom/HUD; DOWN shows the full own paper. After answering Q1, neighbour views show Q2; revisiting a question shows that row. |
| `tests/test_game.py` | Focus growth, cap, side/away reset, question changes and restart tests. |
| `README.md`, `LEARN.md`, `PLAN.md` | Describe hidden papers, sequential reading and gradual focus; document camera recovery from the previous change. |

### Removed

| Item | Why |
|---|---|
| Compact own-paper overlay and its settings | Own paper should not be visible while looking at the teacher. |
| All neighbour questions visible together | Each sideways look should show only the question currently being answered. |

### Details worth knowing

- `PAPER_FOCUS_TIME = 2.5` is the sharpness delay; `PAPER_BLUR_SIGMA = 20.0`
  controls initial blur. These can be tuned independently.
- Each look is independent: returning to a neighbour or changing sides starts
  blurry again. Written player marks remain stored.
- Both neighbours still use the same stable exam key. Looking sideways after
  answering selects the next blank question; Up/Down can revisit earlier rows.
- Existing A..E input is retained for DOWN and SCREEN, but marks are visible
  only when looking DOWN. The teacher's suspicion rules continue during focus.
- Gaussian blur uses a smaller working image for strong blur and full resolution
  as it clears, keeping the effect inexpensive. HUD and webcam remain sharp.
- Validation: 104 tests pass, including the camera recovery tests. Headless
  renders cover teacher/own-paper views and blurry, intermediate and sharp
  neighbour papers. Physical webcam feel still requires a person to try it.

### Next

1. Look forward: verify the own-paper overlay is absent. Look down: verify the
   own paper is clear and all marks are retained.
2. Look left/right: verify only Q1 appears, blurry at first and clear after
   2.5 seconds. Look away or switch sides and check that blur starts again.
3. Answer Q1, then look sideways: only Q2 should appear. Revisit Q1 with the
   arrows and verify its neighbour view returns. Check camera interruption,
   F2 recalibration and R restart reset focus correctly.
