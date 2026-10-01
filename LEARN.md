# How the code works

A guide for learning the "Don't Get Caught" demo, from the big picture down to
each file. Read it with the code open next to it.

Other docs: `PLAN.md` (what the game should become), `STEPS.md` (how to build
it), `NOTES.md` (what changed in each commit).

---

## 1. The big picture

The game is **one loop** in `main.py` that runs about **30 times a second**.
Each time round the loop ("one frame"):

```
   webcam ──► camera.py ──► frame (a picture)
                                │
                                ▼
                         head_tracker.py ──► direction: DOWN / SCREEN / LEFT / RIGHT
                                                 │        (or None = player gone)
                                                 ▼
                                             game.py ──► events: "tick", "answer", "warning"...
                                                 │                 │
                                                 ▼                 ▼
                                            render.py          sounds.py
                                          (draw screen)       (play sounds)
```

Every file has **one job**:

| File | Its one job | Uses |
|---|---|---|
| `settings.py` | Holds every tuning number | nothing |
| `camera.py` | Gets pictures from the webcam | OpenCV |
| `head_tracker.py` | Picture → which way the head points | MediaPipe, OpenCV |
| `game.py` | The rules (bars, answers, warnings, win/lose) | nothing! |
| `sounds.py` | Makes and plays the beeps | pygame, NumPy |
| `render.py` | Draws everything on the window | pygame, OpenCV |
| `main.py` | Runs the loop and connects the others | all of the above |

`game.py` uses **no** camera or graphics library. That is on purpose: the
rules can be tested on their own (`tests/test_game.py`), and the art can change
later without touching the rules.

---

## 2. Ideas you need first

### Frames and pictures
A webcam sends ~30 pictures ("frames") per second. In OpenCV a frame is a
NumPy array of shape `(480, 640, 3)`: 480 rows, 640 columns, 3 colour values
per pixel.

### BGR vs RGB
OpenCV stores colours as **(Blue, Green, Red)**. MediaPipe and pygame use
**(Red, Green, Blue)**. That's why you see `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`
before handing a frame to them, and why colours in `main.py` (for OpenCV) are
written in a different order than in `render.py` (for pygame).

### Mirroring
A webcam image is not mirrored: if you raise your right hand, it appears on
the left of the picture. People expect a mirror, so we flip the picture
(`cv2.flip(frame, 1)`) **for showing only**. Face finding always runs on the
real, unflipped picture.

### dt: time since the last frame
The loop does not run at exactly 30 fps. So instead of "add 1 every frame", the
game adds **real time**: `dt` is the seconds since the last frame (about
0.033). A bar that needs 2.5 s fills correctly whether the game runs at 20 or
30 fps. `main.py` caps `dt` at 0.1 s, so one frozen frame can't fill a bar at
once.

### Events
`game.update()` doesn't play sounds itself. It **returns a list of words**
like `["tick", "answer"]`, and `main.py` plays the sound with that name. The
rules say *what happened*; someone else decides *how to show it*.

### Screens (a "state machine")
The game is always on one screen, stored in the variable `screen_name` in
`main.py`:

```
START ──Space/click──► CALIBRATING ──2 s──► GAME ──win/lose──► END
  ▲                                           │                  │
  └─────────────────── r ─────────────────────┴──────── r ───────┘
```

"Face not found" is not a separate screen: it's the GAME screen while the rules
are not updated (paused).

---

## 3. File by file

### `settings.py` — the numbers
Only constants, in UPPER_CASE, each with its unit. **Want to change how the game
feels? Change a number here**, save, restart. Examples: `COPY_TIME = 2.5` (how
long to copy an answer), `YAW_THRESHOLD = 25` (how far to turn for "side").

### `camera.py` — the webcam
Reading a frame makes the program wait ~20 ms for the camera. To avoid waiting,
`Camera` starts a **thread**: a second worker that runs at the same time as the
game. That worker (`keep_reading`) reads frames forever and saves the newest one
in `self.frame`. When the game calls `read()`, it just gets `self.frame`
straight away.

- `running` is False if there is no webcam or it stopped.
- `release()` stops the thread and gives the webcam back.

### `head_tracker.py` — where is the head pointing?
The hardest file. Three parts:

**a) `read(frame, now)`: find the face, compute angles**
1. Give the frame to MediaPipe's **Face Landmarker** (the model file
   `face_landmarker.task`). It returns 478 points on the face (`landmarks`) and a
   **transformation matrix**: a 4×4 table of numbers describing how the head is
   turned.
2. The matrix's third column is the direction the **nose points**, as an
   arrow `(x, y, z)`: x = right, y = up, z = towards the camera.
3. Turn that arrow into two angles with trigonometry:
   - **yaw** (left/right) = `atan2(x, z)`; 0° = facing the camera
   - **pitch** (up/down) = `asin(y)`; 0° = facing the camera
4. **Smoothing**: `self.yaw += SMOOTHING * (raw_yaw - self.yaw)` moves the
   angle only 40% of the way to the new value each frame. One shaky frame can't
   make it jump.

**b) angles → direction**
- `calibrate(yaw, pitch)` stores your "looking at the screen" angles
  (*neutral*). Everyone sits differently, so all angles are measured from
  *your* neutral (`relative_angles()`).
- `raw_direction()` compares the angles with the limits:
  more than 20° down → `DOWN`, more than 25° left/right → `LEFT`/`RIGHT`,
  otherwise `SCREEN`.
- `update_direction(now)` adds a **hold time**: a new direction must last
  0.2 s before it's believed. While a new direction is waiting it's called the
  `candidate`.

**c) `current_direction(now, face_found)`: what if the face disappears?**
The face often vanishes from MediaPipe's view. The rules, in order:

| Situation | Result | `status` (shown under the preview) |
|---|---|---|
| Face found | the tracked direction | `""` |
| Face vanished while the head was tilting down | `DOWN` (looking at the paper hides the face) | `"head down"` |
| Face vanished less than 0.6 s ago | the last direction (mid-turn gap) | `"face lost..."` |
| Otherwise | `None` → the game pauses | `"face not found"` |

`draw_face()` draws the face outline, eyes, lips and the nose arrow onto the
frame, so you can see what the tracker sees.

**`Calibration`** collects your angles for 2 s and gives their average to
`calibrate()`. If the face is lost on the way, it starts over.

### `game.py` — the rules
`Game` holds the game's state: `answers`, `warnings`, `copy_time`,
`stare_time`, `state` (`PLAYING` / `WON` / `LOST`) and the popup.
`update(direction, dt)` runs once per frame and has two parts:

**Copying (LEFT or RIGHT):**
- `copy_time` grows by `dt`. A `"tick"` event every `TICK_INTERVAL` (0.3 s).
- At `COPY_TIME` (2.5 s): one more answer, `"answer"` event, and
  `copy_locked = True`, so you must look away before the next answer starts
  (otherwise one long look would fill everything).
- 5 answers → `WON`.
- Looking anywhere else resets `copy_time` to 0.

**Staring (SCREEN):**
- `stare_time` grows by `dt`.
- At `WARNING_TIME` (3 s grace + 2 s = 5 s): one more warning, `"warning"`
  event, a popup for 2 s, and `stare_time` starts again from 0.
- 3 warnings → `LOST`.
- Looking anywhere else resets `stare_time` to 0.

**Looking DOWN** does nothing, so it resets both. That's the safe place.

### `sounds.py` — beeps without sound files
A sound is a long list of numbers telling the speaker where to be, 44,100 times
a second. `tone(freq, seconds)` makes a sine wave with NumPy, which sounds like
a beep. `make_waves()` builds the five sounds; their names match the game's
events. If the computer has no sound device, `Sounds` stays empty and `play()`
does nothing, so the game still runs.

### `render.py` — drawing
pygame draws onto a "surface" (the window) and `pygame.display.flip()` (in
`main.py`) shows it. Everything is drawn **again from scratch every frame**;
that's also how animation will work later.

- `camera_to_surface()` turns an OpenCV frame into a pygame image (resize,
  mirror, BGR→RGB).
- `Renderer` loads fonts once and has a draw function per screen:
  `draw_start`, `draw_game`, `draw_popup`, `draw_paused`, `draw_end`.
- Helpers: `text()`, `bar()` (grey background + coloured part),
  `darken()` (see-through black layer for pause/end screens).
- `draw_game` only **reads** `game`; it never changes it.

### `main.py` — the loop
Setup: open the window, sounds, camera, tracker, calibration and game. Then
each frame:

1. **Input**: keys and mouse (`pygame.event.get()`); quit, calibrate, restart.
2. **Camera**: `camera.read()`, then `tracker.read(frame, now)`.
3. **Per screen**:
   - START / CALIBRATING: big preview, feed `calibration.add()`.
   - GAME: `direction = tracker.current_direction(...)`. If not `None`,
     `game.update(direction, dt)` and play a sound per event. Draw; on top,
     either the pause layer or the popup.
   - END: draw the game and the end layer.
4. `pygame.display.flip()` shows the frame; `clock.tick(FPS)` waits so we don't
   run faster than 30 fps.

### `tests/`
`test_game.py` and `test_head_tracker.py` check the rules and the direction
logic **without a camera**, by calling the functions with made-up angles and
times. Run them:

```
.venv/bin/python -m unittest discover -s tests -v
```

Run them after every change. If one fails, you broke a rule (or the test needs
updating because you changed the rule on purpose).

---

## 4. Follow one frame

You turn your head left for 3 seconds. One frame in the middle of that:

1. `camera.read()` returns the newest picture.
2. `tracker.read()` → MediaPipe finds the face; the nose arrow points left;
   yaw becomes, say, +31° relative to your neutral.
3. `tracker.current_direction()` → face found → `update_direction()` →
   `raw_direction()` says `LEFT` (31 > 25), and it has been `LEFT` for more than
   0.2 s → returns `LEFT`.
4. `game.update(LEFT, 0.033)` → `copy_time` is 1.20 s, which has reached the
   next tick time (ticks are at 0, 0.3, 0.6, 0.9, 1.2...) → a `"tick"` event;
   then `copy_time` grows to 1.233 s. Returns `["tick"]`.
5. `main.py` calls `sounds.play("tick")`.
6. `renderer.draw_game()` draws "3 - Copying (left)", lights the green
   NEIGHBOUR box, and fills the copy bar to 1.233 / 2.5 ≈ 49%.
7. `pygame.display.flip()`: you see it.

---

## 5. Try it yourself

Small changes to learn by doing. Run `./run.sh` after each one.

1. **Easy:** in `settings.py`, set `COPY_TIME = 1.0`. Copying is now much faster.
2. **Easy:** set `ANSWERS_NEEDED = 3`. Check that the answer boxes on screen
   update by themselves (look at how `render.py` uses `ANSWERS_NEEDED`).
3. **Medium:** in `sounds.py`, change the `"answer"` sound to two notes, like
   `"won"` is built.
4. **Medium:** in `render.py`, change the colour of the NEIGHBOUR box in
   `OPTION_BOXES`.
5. **Harder:** in `game.py`, make looking DOWN slowly *reduce* `stare_time`
   instead of resetting it to 0. Then fix the test in `tests/test_game.py`
   that now fails (`test_looking_down_resets_staring`) and explain why it failed.
6. **Harder:** print the yaw and pitch to the terminal in `main.py` every
   frame, then look left, right and down and watch the numbers change.
