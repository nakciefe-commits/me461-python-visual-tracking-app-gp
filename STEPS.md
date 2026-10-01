# Build Steps — instructions for an AI coding agent

This file splits `PLAN.md` into small, ordered tasks. Each step is meant to be
done in **one session** by an AI coding agent (e.g. Antigravity) or a person.

**How to use it:** tell the agent

> Read `PLAN.md`, `STEPS.md` and `NOTES.md`. Do **Step N** only. Follow the
> "Rules for every step" section. Stop when the step's "Done when" list is
> complete and tell me what to test.

Do the steps **in order**. Do not start a step before the previous one is
done and tested by a person. Steps marked 👤 are done by the team, not the agent.

---

## Rules for every step

### Project facts (do not break these)

- **Linux, Python 3.14**, virtual environment in `.venv/`. Run things with
  `.venv/bin/python …` and install with `.venv/bin/pip install …`.
- Libraries: `opencv-contrib-python`, `mediapipe`, `pygame-ce`, `numpy`
  (numpy comes with mediapipe).
  - **Never** add `opencv-python` (it conflicts with `opencv-contrib-python`,
    see `NOTES.md` commit #3).
  - `pygame-ce` is imported as `import pygame`. Do **not** install plain
    `pygame` next to it; they conflict the same way.
- **MediaPipe 1.0** only has the `mediapipe.tasks` API
  (`from mediapipe.tasks.python import vision`). The old `mp.solutions.*` API
  found in most tutorials **does not exist**. Do not use it.
- MediaPipe in `VIDEO` mode needs a timestamp in milliseconds that **strictly
  increases** every frame.
- OpenCV frames are **BGR**; MediaPipe and pygame want **RGB**. Convert with
  `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`.
- Run face detection on the **unmirrored** frame. Mirror (`cv2.flip(frame, 1)`)
  only for display.
- Model files live in the project root: `face_landmarker.task` (used),
  `pose_landmarker.task` (old body tracker).
- The game must work **without** a sound device: if `pygame.mixer` fails to
  start, keep running silently.

### Code style (match `tracker.py`)

- Beginner-friendly: the team are students. Short functions, clear names.
- A docstring at the top of every file saying what it does.
- A short comment on every non-obvious step. Explain *why*, in plain words.
- All tuning numbers go in **`settings.py`** as UPPER_CASE constants with a
  comment saying the unit (seconds, degrees, pixels). No magic numbers in the
  other files.
- No new libraries beyond the four above unless the step says so.
- Keep game rules (`game.py`, `teacher.py`) free of pygame/OpenCV imports so
  they can be tested without a camera or window.

### Tests

- Rule logic gets unit tests in `tests/` using Python's built-in `unittest`
  (no pytest needed). Run with:
  ```
  .venv/bin/python -m unittest discover -s tests -v
  ```
- All tests must pass at the end of every step.
- The agent **cannot** test the webcam itself. For camera/visual behaviour,
  list exactly what the person should try.

### At the end of every step

1. Run the tests.
2. Update `requirements.txt` if a library was added.
3. Add an entry to **`NOTES.md`** in the same format as the existing ones
   (Summary, Added/Changed tables, Details worth knowing). Use the next commit
   number and today's date. Leave the hash out; it is added after committing.
4. Update `README.md` if how to run the program changed.
5. Tick the step's checkboxes in this file.
6. Suggest a commit message. **Do not commit or push** unless the person asks.

---

## Shared interfaces

Later steps rely on these names. Keep them exactly as written, so steps fit
together. Steps may **add** things, but must not rename or remove these.

```python
# head_tracker.py
DOWN, SCREEN, LEFT, RIGHT = "DOWN", "SCREEN", "LEFT", "RIGHT"
class HeadTracker:
    yaw: float; pitch: float                    # smoothed, degrees
    def read_angles(self, frame_bgr, timestamp_ms) -> bool   # True = face found
    def calibrate(self, yaw, pitch) -> None
    def raw_direction(self) -> str              # no hold time
    def update_direction(self, now_seconds) -> str            # with hold time
    def close(self) -> None

# game.py  (no pygame / cv2 imports)
class Game:
    answers: int; warnings: int
    copy_progress: float      # 0.0–1.0
    suspicion: float          # 0.0–1.0 (the filling part after the grace time)
    stare_time: float         # seconds of continuous looking at the screen
    state: str                # "PLAYING", "WON", "LOST"
    lose_reason: str | None   # "warnings", "caught", "time"
    popup_text: str | None; popup_timer: float
    def reset(self) -> None
    def update(self, direction, dt, teacher=None) -> list[str]   # returns events

# events returned by Game.update():
#   "tick", "answer", "warning", "won", "lost"

# teacher.py  (Step 4; no pygame / cv2 imports)
class Teacher:
    state: str                # "WRITING", "TURNING", "WATCHING", "WALKING", "DISTRACTED"
    time_in_state: float
    def reset(self) -> None
    def update(self, dt) -> list[str]           # e.g. ["state:TURNING"]
    def is_watching(self) -> bool               # True = sideways looking gets you caught

# sounds.py
class Sounds:
    def play(self, name) -> None                # one-shot, silent if no audio
    def loop(self, name) -> None                # start looping (Step 5)
    def stop(self, name) -> None
```

---

## Step 0 — Check the setup ✅

**Goal:** everything needed is installed and in the repository.

**Already done:** `pygame-ce` installed in `.venv`; `face_landmarker.task`
downloaded to the project root; a first draft of `head_tracker.py` written
(untested).

**Tasks:**
- [x] Add `pygame-ce` to `requirements.txt` (keep `opencv-contrib-python` and
      `mediapipe`).
- [x] Check that these imports work:
      `.venv/bin/python -c "import cv2, mediapipe, pygame, numpy; print('ok')"`.
- [x] Check that `face_landmarker.task` exists. If not, download it:
      `curl -L -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task`
- [x] Create empty folders `assets/images/`, `assets/sounds/` and `tests/`
      (put a `.gitkeep` file in each so git keeps them).

**Done when:** the import command prints `ok`, and the model file exists.

---

## Step 1 — Head tracker + test window ✅ (code done, 👤 testing left)

**Goal:** reliably turn the webcam image into `DOWN` / `SCREEN` / `LEFT` /
`RIGHT` / no face, and have a window to check and tune it.

**Files:**
- `settings.py` — **create**
- `head_tracker.py` — **review and fix** the existing draft
- `head_test.py` — **create** (a small OpenCV-only test program)

### 1.1 `settings.py`

Create it and move the tracker constants out of `head_tracker.py` into it:

```python
# --- Webcam ---
CAMERA_INDEX = 0            # 0 = first webcam; try 1 if the wrong one opens
FACE_MODEL_FILE = "face_landmarker.task"

# --- Head direction (degrees, measured from the calibrated "screen" angle) ---
YAW_THRESHOLD = 25          # turn this far left/right → LEFT/RIGHT
PITCH_DOWN_THRESHOLD = 20   # tilt this far down → DOWN
YAW_SIGN = 1                # set to -1 if LEFT and RIGHT come out swapped
PITCH_SIGN = 1              # set to -1 if looking UP is detected as DOWN
SMOOTHING = 0.4             # 0..1, lower = steadier but slower
HOLD_TIME = 0.2             # seconds a new direction must last before it counts
CALIBRATION_TIME = 2.0      # seconds the player looks at the screen at the start
```

`head_tracker.py` then does `from settings import …` instead of defining them.

### 1.2 `head_tracker.py`

Keep the interface from "Shared interfaces". How the angles are computed:

- Create the detector with `vision.FaceLandmarkerOptions(...,
  running_mode=vision.RunningMode.VIDEO, num_faces=1,
  output_facial_transformation_matrixes=True)`.
- `result.facial_transformation_matrixes[0]` is a 4×4 matrix. Its 3rd column
  `(m[0][2], m[1][2], m[2][2])` is the direction the nose points in camera
  space (x right, y up, z towards the camera).
- `yaw = degrees(atan2(m[0][2], m[2][2])) * YAW_SIGN`
- `pitch = degrees(asin(clamp(m[1][2], -1, 1))) * PITCH_SIGN`
- Smooth: `self.yaw += SMOOTHING * (new_yaw - self.yaw)` (same for pitch).
- `raw_direction()`: subtract the neutral angles, then
  `DOWN` if `pitch < -PITCH_DOWN_THRESHOLD`, else `LEFT` if
  `yaw > YAW_THRESHOLD`, else `RIGHT` if `yaw < -YAW_THRESHOLD`, else `SCREEN`.
  (`DOWN` is checked first: looking down at paper wins over a small turn.)
- `update_direction(now)`: a new direction only replaces the current one after
  it has been the raw result continuously for `HOLD_TIME` seconds.
- If the matrix list is empty, `read_angles` returns `False` and does not
  change the angles.

### 1.3 `head_test.py`

An OpenCV window (no pygame) for tuning:

1. Open the webcam (`CAMERA_INDEX`), create a `HeadTracker`.
2. **Calibration phase:** show "Look at the screen" and a countdown. While a
   face is found, collect yaw/pitch samples for `CALIBRATION_TIME` seconds
   (restart the countdown if the face is lost). Call `calibrate(avg_yaw,
   avg_pitch)`.
3. **Main phase**, every frame, on the **mirrored** frame, draw:
   - big text: the direction (`DOWN`, `SCREEN`, `LEFT`, `RIGHT`), or
     `FACE NOT FOUND` in red;
   - the yaw and pitch relative to neutral, e.g. `yaw +31.2  pitch -4.0`;
   - the raw direction (without hold time) in smaller text;
   - FPS.
4. Keys: `c` = recalibrate, `q`/`Esc` = quit. Also quit on the window's X
   button (see how `tracker.py` does it).
5. Also print the direction to the terminal **only when it changes**.

### 1.4 Tests

`tests/test_head_tracker.py`: test `raw_direction()` and
`update_direction()` **without a camera**. Build the tracker without loading
the model (e.g. `HeadTracker.__new__(HeadTracker)` and set the attributes by
hand, or give `__init__` a `load_model=True` parameter). Cases:
- neutral (0, 0) → `SCREEN`
- yaw +30 → `LEFT`; yaw −30 → `RIGHT`; pitch −25 → `DOWN`
- pitch −25 and yaw +30 → `DOWN`
- calibrated neutral yaw 10: yaw 30 → `SCREEN` (only 20° away)
- hold time: switching to `LEFT` at t=0 is still `SCREEN` at t=0.1 and
  `LEFT` at t=0.25
- a 1-frame flicker (LEFT at t=0, SCREEN at t=0.05) never changes direction

### Done when
- [x] `./run.sh` is unchanged; `.venv/bin/python head_test.py` opens the window.
- [x] Unit tests pass.
- [ ] 👤 A person checks: looking at the paper on the desk shows `DOWN`,
      at the monitor shows `SCREEN`, turning to each side shows the right
      `LEFT`/`RIGHT` (flip `YAW_SIGN` / `PITCH_SIGN` in `settings.py` if not).
- [ ] 👤 Sitting still for 30 s gives no false changes.
- [ ] 👤 Tested on at least two team members. Thresholds in `settings.py`
      adjusted if needed.

---

## Step 2 — The demo (no teacher, no art) ✅ (code done, 👤 testing left)

**Goal:** the demo from `PLAN.md` section 7. A pygame window that shows the
current option, the copy bar with tick sound, the suspicion bar with warning
popup, counters, and pauses when the face is lost.

**Files:**
- `settings.py` — **add** constants
- `game.py` — **create** (rules only)
- `sounds.py` — **create**
- `render.py` — **create**
- `main.py` — **create**
- `run.sh` — **change** to run `main.py`
- `tests/test_game.py` — **create**

### 2.1 Add to `settings.py`

```python
# --- Window ---
WINDOW_WIDTH = 960
WINDOW_HEIGHT = 600
FPS = 30

# --- Rules ---
ANSWERS_NEEDED = 5
COPY_TIME = 2.5             # seconds of looking sideways to fill one answer
STARE_GRACE_TIME = 3.0      # seconds you may look at the screen for free
STARE_FILL_TIME = 2.0       # seconds after the grace time until a warning
MAX_WARNINGS = 3            # this many warnings = game over
POPUP_TIME = 2.0            # seconds a popup stays on screen
TICK_INTERVAL = 0.3         # seconds between tick sounds while copying
```

### 2.2 `game.py` — rules

`Game.update(direction, dt, teacher=None)` returns a list of events. Exact
behaviour each call, only while `state == "PLAYING"`:

1. Count down `popup_timer` by `dt`; when it reaches 0, set `popup_text = None`.
2. **Sideways (`LEFT` or `RIGHT`):**
   - If `copy_locked` is True (an answer was just finished), do nothing.
   - Otherwise add `dt` to the copy time. `copy_progress = copy_time / COPY_TIME`.
   - Emit `"tick"` every `TICK_INTERVAL` seconds of copying (first tick right
     at the start).
   - When `copy_time >= COPY_TIME`: `answers += 1`, emit `"answer"`, reset copy
     time to 0, set `copy_locked = True`.
   - If `answers == ANSWERS_NEEDED`: `state = "WON"`, emit `"won"`.
3. **Not sideways:** copy time = 0, `copy_progress = 0`, `copy_locked = False`.
   (Interrupting resets progress. See `PLAN.md` Q2.)
4. **`SCREEN`:** add `dt` to `stare_time`.
   `suspicion = clamp((stare_time - STARE_GRACE_TIME) / STARE_FILL_TIME, 0, 1)`.
   When `suspicion` reaches 1: `warnings += 1`, emit `"warning"`, set
   `popup_text = f"The teacher noticed you staring! Warning {warnings}/{MAX_WARNINGS}"`,
   `popup_timer = POPUP_TIME`, reset `stare_time = 0` and `suspicion = 0`.
   If `warnings == MAX_WARNINGS`: `state = "LOST"`, `lose_reason = "warnings"`,
   emit `"lost"`.
5. **Not `SCREEN`:** `stare_time = 0`, `suspicion = 0`.
6. `teacher` is ignored in this step (used in Step 4).

`reset()` sets everything back to the start values. `game.py` must not import
pygame or cv2.

### 2.3 `sounds.py`

- `Sounds.__init__()`: try `pygame.mixer.init(44100, -16, 1)`. If it raises,
  set `self.enabled = False` and make every method do nothing.
- **Generate** the demo sounds with numpy (no files yet). Build a numpy
  int16 array and turn it into a sound with `pygame.sndarray.make_sound`.
  Check the real channel count with `pygame.mixer.get_init()`; if it is 2,
  stack the array into two columns.
  - `"tick"`: 1500 Hz sine, 0.03 s, fast fade out
  - `"answer"`: 880 Hz sine, 0.25 s, fade out (a "ding")
  - `"warning"`: 150 Hz square wave, 0.4 s (a "buzz")
  - `"won"`: three rising notes (523, 659, 784 Hz), 0.15 s each
  - `"lost"`: falling tone 400 → 150 Hz, 0.8 s
- `play(name)`: plays the sound. Unknown names do nothing (no crash).
- `loop(name)` / `stop(name)`: can be empty for now (used in Step 5).

### 2.4 `render.py` — drawing with shapes and text only

A `Renderer` class that receives the pygame `screen` and loads fonts once
(`pygame.font.SysFont(None, size)`). Functions:

- `draw_calibration(seconds_left, face_found)`: "Look at the screen" +
  countdown, or "Face not found" if `face_found` is False.
- `draw_game(game, direction, camera_surface, yaw, pitch)`, layout for
  960×600:
  - **Top left:** big title for the current option:
    - `DOWN` → "1 — Looking at the paper"
    - `SCREEN` → "2 — Looking at the teacher"
    - `LEFT`/`RIGHT` → "3 — Copying (left)" / "3 — Copying (right)"
  - Below it: **answers** as 5 small squares (filled = done) + "3/5";
    **warnings** as 3 circles (filled = received) + "1/3".
  - **Top right:** webcam preview 320×240, mirrored, with
    `yaw +31 pitch -4` text under it.
  - **Middle:** three option boxes side by side ("1 PAPER", "2 SCREEN",
    "3 NEIGHBOUR"); the active one is filled with a bright colour, the others
    grey outlines.
  - **Bottom:** two labelled bars, full width:
    - "Copying": green, `game.copy_progress`.
    - "Suspicion": shows the grace part and the fill part. Draw a thin
      marker line where the grace time ends; the bar before the marker fills
      in yellow with `stare_time / STARE_GRACE_TIME`, the part after fills
      red with `game.suspicion`.
  - **Popup:** if `game.popup_text`, a centred red box with white text on top
    of everything.
- `draw_paused()`: semi-transparent dark layer over the last game image +
  "Face not found — game paused".
- `draw_end(game)`: "All answers filled! You win" or "Too many warnings —
  game over", plus "R = play again   Q = quit".

Use a small colour palette defined at the top of `render.py` (pygame uses RGB,
**not** BGR like OpenCV).

**Webcam frame → pygame:** mirror with `cv2.flip(frame, 1)`, resize to
320×240, convert BGR→RGB, then
`pygame.image.frombuffer(rgb.tobytes(), (320, 240), "RGB")`.

### 2.5 `main.py` — the loop

Screens: `"CALIBRATING"`, `"PLAYING"`, `"END"` (paused is a flag inside
PLAYING, not its own screen).

Every frame:
1. Handle events: window close, `q`/`Esc` = quit, `r` = restart (reset game,
   go to CALIBRATING), `c` = recalibrate.
2. Read a webcam frame. If reading fails, show an error message on screen and
   quit cleanly.
3. `face = tracker.read_angles(frame, timestamp_ms)` (timestamp strictly
   increasing).
4. Per screen:
   - CALIBRATING: same logic as `head_test.py`; when done go to PLAYING.
   - PLAYING: if no face → draw paused, **do not** call `game.update`.
     Otherwise `direction = tracker.update_direction(now)`,
     `events = game.update(direction, dt)`, play a sound for each event,
     draw. If `game.state` is not `"PLAYING"` → go to END.
   - END: draw end screen.
5. `pygame.display.flip()`, `clock.tick(FPS)`.

`dt` = real seconds since the last frame, **capped at 0.1 s** so a slow frame
cannot fill a whole bar at once. On exit release the camera, close the
tracker, `pygame.quit()`.

### 2.6 `run.sh`

Change the last line to `.venv/bin/python main.py`. `tracker.py` stays in the
repository and can still be run directly.

### 2.7 Tests (`tests/test_game.py`)

Call `update` with small `dt` steps (e.g. 0.05) in a loop. Cases:
- 2.5 s of `LEFT` → `answers == 1`, `"answer"` emitted once.
- 2.4 s `LEFT`, then 0.1 s `DOWN`, then 0.2 s `LEFT` → `answers == 0`
  (progress reset).
- 5 s of `LEFT` without looking away → still `answers == 1` (copy lock).
- 5 × (2.5 s `LEFT` + 0.1 s `DOWN`) → `state == "WON"`.
- Ticks: 1 s of `RIGHT` emits about 1 / 0.3 ≈ 4 ticks.
- 2.9 s `SCREEN` → `suspicion == 0`; 4 s `SCREEN` → `0 < suspicion < 1`;
  5 s → `warnings == 1`, `popup_text` is set.
- 3 warnings → `state == "LOST"`, `lose_reason == "warnings"`.
- Looking down resets `stare_time`.
- `update` does nothing after `state` is `"WON"` or `"LOST"`.

### Done when
- [x] Unit tests pass.
- [x] `./run.sh` opens the demo window.
- [x] Update `README.md` (run instructions, files table) and `NOTES.md`.
- [ ] 👤 All items of `PLAN.md` section 7.3 checked by a person.

---

## Step 3 — 👤 Playtest the demo (team, no agent)

**Goal:** tune the numbers and make the open decisions before building more.

- [ ] Each team member plays 3+ rounds.
- [ ] Tune in `settings.py`: `YAW_THRESHOLD`, `PITCH_DOWN_THRESHOLD`,
      `HOLD_TIME`, `COPY_TIME`, `STARE_GRACE_TIME`, `STARE_FILL_TIME`.
- [ ] Decide `PLAN.md` open questions **Q1–Q5** and write the answers into
      `PLAN.md` section 9 (replace the question with the decision).
- [ ] Note anything that felt wrong (laggy, unfair, confusing) at the bottom
      of `PLAN.md` under a new "Playtest notes" heading. The agent reads it
      in the next steps.

**Done when:** Q1–Q5 are answered in `PLAN.md`.

---

## Step 4 — The teacher (still no art)

**Goal:** the full game rules: a teacher that can catch you, and an exam timer.
After this step the game is **complete and playable** with placeholder
graphics.

**Before starting:** read the decisions in `PLAN.md` section 9 and the
playtest notes. If Q1 was decided as "memorise then write", implement that
in `game.py` here (add a `"memorised"` step between copying and the answer,
filled by looking `DOWN` for `WRITE_TIME` seconds; lose the memorised answer
if caught). Otherwise keep the simple rule.

**Files:** `settings.py` (add), `teacher.py` (create), `game.py` (change),
`render.py` (change), `main.py` (change), `tests/test_teacher.py` (create),
`tests/test_game.py` (extend).

### 4.1 Add to `settings.py`

```python
EXAM_TIME = 90              # seconds; run out before all answers = lose
CAUGHT_GRACE = 0.3          # seconds into WATCHING before sideways looking counts
# (min, max) seconds for each teacher state, a random value in between is used
TEACHER_DURATIONS = {
    "WRITING":    (4.0, 8.0),
    "TURNING":    (1.0, 1.0),
    "WATCHING":   (2.0, 5.0),
    "WALKING":    (3.0, 6.0),
    "DISTRACTED": (3.0, 6.0),
}
STARE_ONLY_WHEN_FACING = True   # PLAN Q5: staring only counts if the teacher faces the class
```

### 4.2 `teacher.py`

- `Teacher(rng=None)`: `rng` is a `random.Random`. Use `random.Random()` if
  None. **Always** use `self.rng`, never the global `random`, so tests can
  pass a seeded one.
- Start in `WRITING`.
- Each state lasts `rng.uniform(min, max)` from `TEACHER_DURATIONS`.
- Transitions:
  - `WRITING` → `TURNING` (always, so the danger is always announced)
  - `TURNING` → `WATCHING` 60% / `WALKING` 40%
  - `WATCHING` → `WRITING` 50% / `DISTRACTED` 25% / `WALKING` 25%
  - `WALKING` → `WRITING` 60% / `WATCHING` 40%
  - `DISTRACTED` → `TURNING` (danger announced again)
- `update(dt)` advances time; when a state ends, switch and return
  `["state:<NEW_STATE>"]` (otherwise `[]`).
- `is_watching()`: True in `WALKING`, and in `WATCHING` once
  `time_in_state >= CAUGHT_GRACE`.
- `is_facing_class()`: True in `TURNING`, `WATCHING`, `WALKING`.

### 4.3 Changes to `game.py`

- New attribute `time_left`, starts at `EXAM_TIME`. Count it down in `update`.
  At 0 with answers missing: `state = "LOST"`, `lose_reason = "time"`, emit
  `"lost"`.
- If `teacher` is given and the direction is `LEFT`/`RIGHT` and
  `teacher.is_watching()`: `state = "LOST"`, `lose_reason = "caught"`, emit
  `"caught"` and `"lost"`.
- If `STARE_ONLY_WHEN_FACING` and the teacher is given and not facing the
  class: staring does not fill `stare_time` (it stays the same).
- With `teacher=None` the game must behave exactly as in Step 2, so the
  Step 2 tests still pass.

### 4.4 Rendering (placeholder teacher)

- In the area where the classroom art will go later, draw a **coloured box +
  label** for the teacher state: green "WRITING (back turned)", yellow
  "TURNING!", red "WATCHING", red "WALKING", green "ON PHONE".
- Draw the teacher box **only while the direction is `SCREEN`**. When the
  player looks away, show a dark "you can't see the teacher" panel instead. This is the
  core mechanic. **Exception:** a debug key `d` toggles always showing it.
- Show the exam timer top centre (`1:23`). Red under 15 s.
- End screen texts for each `lose_reason`: "Caught copying!", "Too many
  warnings", "Time's up".
- Pause (face not found) also pauses the teacher and the timer.

### 4.5 Tests
- `test_teacher.py`: with `random.Random(1)`, run 10 minutes of `update(0.05)`
  and check: every state appears; `WRITING` is always followed by `TURNING`;
  durations stay inside their ranges; `is_watching()` is False during
  `TURNING` and in the first `CAUGHT_GRACE` s of `WATCHING`.
- `test_game.py` additions: use a tiny fake teacher class with a settable
  `is_watching()` / `is_facing_class()`, and check caught, time-out, the
  staring rule, and that pausing (not calling update) freezes `time_left`.

### Done when
- [ ] All tests pass (old and new).
- [ ] 👤 The game can be won and lost in all three ways.
- [ ] 👤 Losing feels fair: there is always a `TURNING` warning before danger.
- [ ] `NOTES.md` and `README.md` updated.

---

## Step 5 — Real sounds

**Goal:** the player can play "by ear" while looking away from the screen.

👤 **Before the step**, the team puts sound files in `assets/sounds/` (`.wav`
or `.ogg`, free from freesound.org or recorded). Expected names:

| File | Plays | Kind |
|---|---|---|
| `tick` | each tick while copying | one-shot |
| `answer` | answer filled | one-shot |
| `warning` | warning | one-shot |
| `won` / `lost` / `caught` | end of game | one-shot |
| `chalk` | while teacher is `WRITING` | loop |
| `turn` | teacher starts `TURNING` (**most important**) | one-shot |
| `footsteps` | while teacher is `WALKING` | loop |
| `phone` | teacher becomes `DISTRACTED` | one-shot |
| `classroom` | background, quiet, whole game | loop |

**Agent tasks:**
- `sounds.py`: for each name, load `assets/sounds/<name>.wav` or `.ogg` if it
  exists, **otherwise fall back to the generated sound** (or silence for
  sounds that have no generated version). The game must still run with an
  empty `assets/sounds/` folder.
- Implement `loop(name)` / `stop(name)` using `pygame.mixer.Channel`s
  (one reserved channel per looping sound).
- Add `SOUND_VOLUMES = {"classroom": 0.2, "chalk": 0.6, …}` to `settings.py`.
- In `main.py`, react to teacher events: on `state:X`, stop the old state's
  loop and start the new one / play the one-shot. Stop all loops on pause and
  on the end screen; restart them on resume.

**Done when:**
- [ ] 👤 With eyes closed, a person can tell when the teacher turns around.
- [ ] Game works with no sound files and with no sound device.

---

## Step 6 — Art and animation

**Goal:** replace the coloured boxes with the classroom and an animated teacher.

👤 **Before the step**, the team prepares images in `assets/images/`
(see `PLAN.md` 5.2). PNG, transparent background for characters, same size
and position across frames of one animation. Naming:
`classroom_bg.png`, `teacher_writing_0.png`, `teacher_writing_1.png`, …,
`teacher_turning_*`, `teacher_watching_*`, `teacher_walking_*`,
`teacher_phone_*`.

**Agent tasks:**
- New file `animation.py` with an `Animation` class:
  - `Animation(frames, fps)` where `frames` is a list of pygame Surfaces.
  - `update(dt)` advances the frame, `current()` returns the Surface to draw,
    `reset()` goes back to frame 0. Loops forever.
  - Helper `load_frames(prefix)` loads `assets/images/<prefix>_0.png`,
    `_1.png`, … until a number is missing. Use `.convert_alpha()` after
    loading (needs the window to exist already).
  - Optional helper `load_sprite_sheet(path, frame_width)` that cuts one wide
    image into frames.
- `render.py`:
  - Draw `classroom_bg.png` scaled to the window (only while looking at
    `SCREEN`, as in Step 4).
  - Draw the teacher animation that matches `teacher.state`; reset it when the
    state changes.
  - `WALKING`: move the teacher left↔right across the room
    (`TEACHER_WALK_SPEED` pixels/second in `settings.py`); flip the image with
    `pygame.transform.flip` when walking the other way.
  - Move the HUD (bars, counters) so it does not cover the teacher; keep the
    webcam preview small in a corner (toggle with key `v`).
  - **Fallback:** if an image set is missing, draw the Step 4 coloured box for
    that state instead of crashing.
- Add `ANIMATION_FPS = 6` and image positions/sizes to `settings.py`.

**Done when:**
- [ ] Game runs with all images, with some missing, and with none.
- [ ] 👤 The teacher's state is clear from the picture alone.
- [ ] Still 25+ fps (print FPS in debug mode `d`).

---

## Step 7 — Menus and polish

**Goal:** a game someone outside the team can start and understand.

- **Main menu** screen: title, "SPACE = start", "H = how to play", "Q = quit".
- **How to play** screen: the three head directions with short explanations
  and the win/lose rules, from `PLAN.md` sections 1 and 3.
- Screen flow: `MENU → HOW_TO → MENU`, `MENU → CALIBRATING → PLAYING → END →
  MENU`.
- **Calibration screen:** a progress circle or bar, and "Sit normally and
  look at the screen".
- **End screen:** reason, answers filled, time left, warnings; "R = play again,
  M = menu".
- **Popups** fade out instead of disappearing.
- **"Face not found"** overlay with a hint: "Check the lighting and that your
  face is in the camera".
- Webcam errors (no camera, camera unplugged) show a readable message on
  screen instead of crashing.

**Done when:**
- [ ] 👤 Someone who has never seen the game can start and play it using only
      the screens.

---

## Step 8 — Difficulty and score

- **Difficulty over time:** as the exam goes on, multiply safe-state durations
  by a factor going from 1.0 down to `MIN_SAFE_FACTOR` (e.g. 0.6) and danger
  durations up to `MAX_DANGER_FACTOR` (e.g. 1.3). `TURNING` never drops below
  `MIN_TURN_TIME` (e.g. 0.6 s), so it stays fair.
- **Difficulty levels** in the menu (Easy / Normal / Hard), each a set of
  numbers in `settings.py`.
- **Score** on win: `time_left * 10 + (MAX_WARNINGS - warnings) * 100 +
  close_calls * 50`. A **close call** = finishing an answer while the teacher
  is `TURNING`.
- **High scores:** keep the top 5 in `highscores.json` (read/write with the
  built-in `json` module; a missing or broken file = empty list). Show them on
  the menu. Add `highscores.json` to `.gitignore`.
- Tests for score calculation, high-score saving/loading, and difficulty
  factors.

---

## Step 9 — Final testing and documentation

- [ ] 👤 Test on another computer and another webcam, from a fresh `git clone`,
      following only `README.md`.
- [ ] 👤 Test in different lighting (bright window behind you, dark room).
- [ ] 👤 Test with glasses / a hat / long hair.
- [ ] Remove debug prints; keep debug key `d`.
- [ ] `README.md`: description, screenshot, setup, how to play, controls,
      files table, libraries, credits for art and sounds (with licences).
- [ ] `NOTES.md` complete.
- [ ] `PLAN.md`: mark what was built, keep future ideas.

---

## Future ideas

Not part of the steps above. See `PLAN.md` section 10 (neighbours with right/
wrong answers, eye tracking mode, hand-raise distraction, levels, two-player,
settings screen, and more). Start them only after Step 9.
