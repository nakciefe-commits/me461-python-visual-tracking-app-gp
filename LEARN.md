# How the code works

A guide for learning the "Don't Get Caught" code, from the big picture down
to each file. Read it with the code open next to it.

Other docs: `README.md` (how to run and play), `PLAN.md` (the design and what
is next), `NOTES.md` (what changed in each commit, and why), `CLAUDE.md`
(rules for anyone, person or AI, changing the code).

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
                       teacher.py + game.py ──► events: "tick", "spotted", "state:TURNING"...
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
| `teacher.py` | The teacher: busy, turning, watching; board or desk | nothing! |
| `game.py` | The rules (bars, answers, warnings, clock, win/lose) | nothing! |
| `sounds.py` | Makes the beeps, loads the sound files, plays them | pygame, NumPy |
| `render.py` | Draws everything on the window | pygame, OpenCV |
| `main.py` | Runs the loop and connects the others | all of the above |

`game.py` and `teacher.py` use **no** camera or graphics library. That is on
purpose: the rules can be tested on their own (`tests/`), and the art can
change without touching the rules.

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
0.033). A bar that needs 3 s fills correctly whether the game runs at 20 or
30 fps. `main.py` caps `dt` at 0.1 s, so one frozen frame can't fill a bar at
once.

### Events
`game.update()` and `teacher.update()` don't play sounds themselves. They
**return a list of words** like `["tick", "answer"]` or `["state:TURNING"]`,
and `main.py` plays the sound with that name. The rules say *what happened*;
someone else decides *how to show it*.

### Screens (a "state machine")
The game is always on one screen, stored in the variable `screen_name` in
`main.py`:

```
DISCLAIMER ──Space/click──►
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
feels? Change a number here**, save, restart. Examples: `COPY_TIME = 3.0` (how
long to copy an answer), `YAW_THRESHOLD = 18` (how far to turn for "side"),
`TEACHER_DURATIONS` (how long the teacher stays busy or watching).

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
   angle only part of the way (`SMOOTHING`, 80%) to the new value each frame. One shaky frame can't
   make it jump.

**b) angles → direction**
- `calibrate(yaw, pitch)` stores your "looking at the screen" angles
  (*neutral*). Everyone sits differently, so all angles are measured from
  *your* neutral (`relative_angles()`).
- `raw_direction()` compares the angles with the limits:
  more than `PITCH_DOWN_THRESHOLD` (28°) down → `DOWN`, more than
  `YAW_THRESHOLD` (18°) left/right → `LEFT`/`RIGHT`, otherwise `SCREEN`.
- `update_direction(now)` adds a **hold time**: a new direction must last
  `HOLD_TIME` (0.1 s) before it's believed. While a new direction is waiting it's called the
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
`Game` holds the game's state: the answer key (`right_letters`,
`knowing_side`), `written`, `read_sides`, `warnings`, `copy_time`,
`suspicion_level`, `time_left`, `state` (`PLAYING` / `WON` / `LOST`) and the
popup. `update(direction, dt, teacher)` runs once per frame and has three
parts: the suspicion bar, copying, and the exam clock. `write(letter,
direction)` is called when a letter key is pressed.

**The answer key:** at `reset()` each question gets a random right letter
(`right_letters`, A-D) and a random neighbour who knows it (`knowing_side`,
LEFT or RIGHT). Like the teacher, `Game` takes a `random.Random`, and the tests
also set the key by hand so they know the answers.

**Copying (LEFT or RIGHT): reading a neighbour's paper**
- `copy_time` is a dictionary, one number per side: `copy_time[LEFT]` grows
  by `dt` while you look left. A `"tick"` event every `TICK_INTERVAL` (0.3 s).
- No progress while the teacher sees you copying (no gain, only risk).
- At `COPY_TIME`: the side goes into `read_sides`, `"read"` event.
  `paper_shows(side)` then gives the letter, or `"?"` for the neighbour who
  does not know it. A paper already read gives nothing more.
- Looking anywhere else keeps `copy_time`, so a paper can be read in pieces.

**Writing (DOWN + a letter key):** `write()` does nothing unless you look
down and `can_write()` (the knowing neighbour's paper is read). Any letter is
written into `written` (`"write"` event), and the next question starts with
nothing read. 5 written → `WON`. `answers` is just `len(written)`;
`correct_count()` compares `written` with `right_letters` for the grade.

**The suspicion bar (`suspicion_level`, 0 to 1):**
- **Seen copying** (sideways while `teacher.is_watching()`): grows by
  `dt / CAUGHT_TIME`, full in 0.9 s → `"caught"`, `LOST`. A `"spotted"` alarm
  plays each time a glance starts.
- **Staring** (SCREEN while the teacher looks at the class): grows by
  `dt / WARNING_TIME`, full after 5 s → one more warning, `"warning"` event,
  a popup for 2 s, and the bar starts again from 0. 3 warnings → `LOST`.
- Both add to the **same** bar: after being seen, staring carries on from
  there.
- Otherwise it **drains slowly** (`SUSPICION_DRAIN_TIME`, 8 s for a full bar).
  It never jumps to empty, because that would tell you the teacher looked away.

**The exam clock:** `time_left` counts down from `EXAM_TIME` (60 s); at 0 →
`LOST`.

**Losing** emits `"lost"` and `"lost_<reason>"` (`lost_caught`,
`lost_warnings`, `lost_time`), so each way of losing can have its own sound.

**Looking DOWN** is the safe place: nothing fills, the bar drains.

### `teacher.py` — the teacher
A **state machine**: the teacher is always in one state, and after a random
time (`TEACHER_DURATIONS`) moves to the next:

```
BUSY ──► TURNING ──► WATCHING ──► BUSY ...
```

- `place` is `BOARD` or `DESK`; after watching, it may switch (`MOVE_CHANCE`).
- `update(dt)` returns `["state:TURNING"]` etc. when the state changes.
- `is_watching()`: copying now fills the suspicion bar fast (after the first
  `CAUGHT_GRACE` seconds of `WATCHING`). `is_facing_class()`: staring counts.
- `image_name()` → e.g. `"classroom_board_busy"`: which picture to draw.
- `sounds(events, can_hear)` decides which teacher sounds the player hears:
  none while looking at the paper; the turning "hmm" once per turn, even if
  you look up late.
- It takes a `random.Random` so the tests can use a fixed seed and get the
  same "random" teacher every run.

### `sounds.py` — beeps and sound files
A sound is a long list of numbers telling the speaker where to be, 44,100 times
a second. `tone(freq, seconds)` makes a sine wave with NumPy, which sounds like
a beep. `make_waves()` builds the beeps; their names match the events.
`SOUND_FILES` replaces some of them with files from `assets/sounds/` (the
Luigi "hmm" for `state:TURNING`, the MGS alert for losing by being caught or
by warnings). A missing file keeps the beep. If the computer has no sound
device, `Sounds` stays empty and `play()` does nothing, so the game still runs.

### `render.py` — drawing
pygame draws onto a "surface" (the window) and `pygame.display.flip()` (in
`main.py`) shows it. Everything is drawn **again from scratch every frame**;
that's also how animation will work later.

- `camera_to_surface()` turns an OpenCV frame into a pygame image (resize,
  mirror, BGR→RGB).
- `load_classroom()` loads a classroom picture once, scales it to the window's
  width and cuts off the top (`CLASSROOM_TOP`) and bottom so it fits.
- `Renderer` loads fonts and pictures once and has a draw function per
  screen: `draw_disclaimer`, `draw_start`, `draw_game`, `draw_popup`, `draw_paused`, `draw_end`.
- `draw_game` draws the teacher's picture (fading in by `view`), or while
  you look away the picture for that direction (`LOOK_AWAY_IMAGES`: your
  paper, or the left/right neighbour's paper, never the teacher), then see-through strips: answers, warnings and the
  clock at the top, the copy and suspicion bars at the bottom.
- On your paper it writes `game.written` on the answer lines
  (`OWN_ANSWER_Y`). For a neighbour, `neighbour_picture()` picks the plain
  picture until the copy bar is full, then the one with the letter circled
  on their paper (`left_B`, `right_unknown` for "?"). If that picture is
  missing, `neighbour_note()` draws the letter in a white note instead.
  `look_away_texts()` picks the hint ("Press A, B, C or D...").
- `draw_end` shows the grade and `answer_boxes(..., graded=True)`: green =
  right, red = wrong.
- Helpers: `text()`, `bar()` (grey background + coloured part),
  `darken()` (see-through black layer, for the whole window or a strip).
- The draw functions only **read** `game` and `teacher`; they never change them.

### `main.py` — the loop
Setup: open the window, sounds, camera, tracker, calibration and game. Then
each frame:

(The window: `open_window()` always gives a 960×600 surface to draw on. The
`pygame.SCALED` flag stretches it to the real window size with black bars and
maps mouse clicks back, so no drawing code needs to know the screen size.
Normally it is a resizable window with a title bar, maximized at the start.
`pygame.FULLSCREEN` with `SCALED` is a borderless window the size of the
desktop, not a real video-mode change. F11 just calls `open_window()` again.)

1. **Input**: keys and mouse (`pygame.event.get()`); quit, calibrate, restart, F11 fullscreen,
   and A-D (`LETTER_KEYS`) → `game.write(letter, direction)`.
2. **Camera**: `camera.read()`, then `tracker.read(frame, now)`.
3. **Per screen**:
   - DISCLAIMER: the warning screen, shown once when the game opens.
   - START / CALIBRATING: big preview, feed `calibration.add()`.
   - GAME: `direction = tracker.current_direction(...)`. If not `None`:
     `teacher.update(dt)`, filtered by `teacher.sounds()` (silence while
     looking down), and `game.update(direction, dt, teacher)`; play a sound
     per event. `classroom_view()` says how visible the classroom is (0 =
     black, 1 = shown, fading in over `FADE_TIME`). Draw; on top, either the
     pause layer or the popup. Paused = nothing is updated, so the teacher
     and the clock freeze too.
   - END: the same branch as GAME, but nothing is updated: draw the game
     with the classroom always shown, and the end layer on top.
4. `pygame.display.flip()` shows the frame; `clock.tick(FPS)` waits so we don't
   run faster than 30 fps.

### `tests/`
`test_game.py`, `test_teacher.py` and `test_head_tracker.py` check the rules,
the teacher and the direction logic **without a camera**, by calling the
functions with made-up angles and times. `test_game.py` uses a `FakeTeacher`
whose watching/facing the test sets by hand. Run them:

```
.venv/bin/python -m unittest discover -s tests -v
```

Run them after every change. If one fails, you broke a rule (or the test needs
updating because you changed the rule on purpose).

---

## 4. Follow one frame

You turn your head left to copy while the teacher erases the board. One
frame in the middle of that:

1. `camera.read()` returns the newest picture.
2. `tracker.read()` → MediaPipe finds the face; the nose arrow points left;
   yaw becomes, say, +25° relative to your neutral.
3. `tracker.current_direction()` → face found → `update_direction()` →
   `raw_direction()` says `LEFT` (25 > 18), and it has been `LEFT` for more than
   0.1 s → returns `LEFT`.
4. `teacher.update(0.033)` → still `BUSY`, returns `[]`.
5. `game.update(LEFT, 0.033, teacher)` → the teacher is not watching, so the
   suspicion bar drains a little; `copy_time[LEFT]` is 1.20 s, which has
   reached the next tick time (ticks are at 0, 0.3, 0.6, 0.9, 1.2...) → a
   `"tick"` event; then it grows to 1.233 s. Returns `["tick"]`.
6. `main.py` calls `sounds.play("tick")`.
7. `classroom_view(LEFT, ...)` is 0, so `renderer.draw_game()` draws the
   left neighbour's paper with "Copying answer 1 from the left" and fills
   the copy bar to 1.233 / 5.0 ≈ 25%.
8. `pygame.display.flip()`: you see it.
9. Later, at 5.0 s, `"read"`: a note above her paper shows, say, "C". You
   look down and press C: `game.write("C", DOWN)` writes it on your paper.

Had the teacher been `WATCHING`, step 5 would instead raise the suspicion bar
by 0.033 / 0.9, not move the copy bar, and return `["spotted"]` on the first
such frame: the alarm.

---

## 5. Try it yourself

Small changes to learn by doing. Run `./run.sh` after each one.

1. **Easy:** in `settings.py`, set `COPY_TIME = 1.0`. Copying is now much faster.
2. **Easy:** set `ANSWERS_NEEDED = 3`. Check that the answer boxes on screen
   update by themselves (look at how `render.py` uses `ANSWERS_NEEDED`).
3. **Medium:** in `sounds.py`, change the `"read"` sound to two notes, like
   `"won"` is built.
4. **Medium:** in `render.py`, change the colour of the copy bar.
5. **Harder:** in `game.py`, make looking DOWN drain the suspicion bar twice
   as fast as other directions. Then add a test for it in `tests/test_game.py`.
6. **Harder:** print the yaw and pitch to the terminal in `main.py` every
   frame, then look left, right and down and watch the numbers change.
