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
   webcam ──► tracking/camera.py ──► frame (a picture)
                                        │
                                        ▼
                              tracking/head_tracker.py ──► direction: DOWN / SCREEN / LEFT / RIGHT
                                                               │        (or None = player gone)
                                                               ▼
                         logic/teacher.py + logic/game.py ──► events: "read", "spotted", "state:TURNING"...
                                                               │                 │
                                                               ▼                 ▼
                                                         ui/render.py       ui/sounds.py
                                                        (draw screen)      (play sounds)
```

The code is in **three folders**, and every file has **one job**:

| Folder | File | Its one job | Uses |
|---|---|---|---|
| | `settings.py` | Holds every tuning number (also the exams and the moods) | nothing |
| | `main.py` | Runs the loop and connects the others | all of them |
| `tracking/` | `camera.py` | Gets pictures from the webcam | OpenCV |
| | `head_tracker.py` | Picture → which way the head points | MediaPipe, OpenCV |
| `logic/` | `game.py` | The rules of one exam (clock, warnings, caught, scenes, score) | nothing! |
| | `exam_paper.py` | Your paper: answer key, what you wrote, the grade | nothing! |
| | `neighbours.py` | Reading a neighbour's paper (gradual focus) | nothing! |
| | `suspicion.py` | The suspicion bar and close calls | nothing! |
| | `run.py` | A run: three exams in a row, the total | nothing! |
| | `teacher.py` | The teacher: busy, turning, watching; board or desk; mood | nothing! |
| | `slot.py` | The gossip slot machine's reel (where it is, when it stops) | nothing! |
| | `tally.py` | The score count after an exam, one part at a time | nothing! |
| | `highscore.py` | The top scores file | nothing! |
| | `bag.py` | Random order, every item once before any repeats | nothing! |
| | `menu.py` | Menus: which item is selected; head angles → menu actions | nothing! |
| | `disclaimer.py` | The opening notice: typed, signed, stamped | nothing! |
| `ui/` | `render.py` | The `Renderer`: loads fonts and pictures | pygame, OpenCV |
| | `style.py`, `draw_*.py` | The drawing, one file per kind of screen | pygame |
| | `sounds.py` | Makes the beeps, loads the sound files, plays them | pygame, NumPy |
| | `glitch_intro.py` | Our team's intro, shown first | pygame (NumPy for its sound) |

Everything in `logic/` uses **no** camera or graphics library ("nothing!"
above; they only borrow the direction names from `head_tracker.py`). That is
on purpose: the rules can be tested on their own (`tests/`), and the art can
change without touching the rules.

**Folders and imports.** A folder of Python files is a "package"; its
`__init__.py` says what is in it. A file in a folder is imported with the
folder's name in front: `from logic.game import Game`. Python finds the
folders because `main.py` (and every test, with `sys.path.insert`) runs from
the project's top folder. Pictures and sounds are found the same way
(`assets/...` from the top folder), which is why `run.sh` first goes there.

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
written in a different order than in `ui/style.py` (for pygame).

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
**return a list of words** like `["read", "write"]` or `["state:TURNING"]`,
and `main.py` plays the sound with that name. The rules say *what happened*;
someone else decides *how to show it*.

### Screens (a "state machine")
The game is always on one screen, stored in `self.screen_name` in
`main.py`:

```
(glitch_intro.play() first, before the loop)
DISCLAIMER ──signed + stamped──► START ──Space/click──► CALIBRATING ──2 s──► MENU
                                                                         │
     HELP ◄── "How to play" ── MENU ── "Settings" ──► SETTINGS ──"Recalibrate"──► CALIBRATING
                                │                                                      (back to SETTINGS)
                              "Play" (a new run)
                                ▼
         ┌──────────────► BRIEFING ──"I'm ready"──► LOADING ──3 s──► GAME ──handed in / collected / failed──► END
         │   (next exam)                    ▲  k: CALIBRATING                         │
         │                                  └──┘                                      │
         └─────────────────────────── "Next exam" ◄───────────────────────────────────┤
                                                                                       │
                       after the 3rd exam: "See results" ──► RUN_END ── "Play again" ──► (a new run)
```

`App.go_to(name)` changes the screen. MENU, HELP, SETTINGS, BRIEFING, END
and RUN_END are the "menu screens": each has a `Menu` (a list of items) in
`self.menus`. END's items change: "Next exam" / "Main menu", or "See
results" after the last exam.

"Face not found" is not a separate screen: it's the GAME screen while the rules
are not updated (paused).

---

## 3. File by file

### `settings.py` — the numbers
Only constants, in UPPER_CASE, each with its unit. **Want to change how the game
feels? Change a number here**, save, restart. Examples: `PAPER_FOCUS_TIME = 1.5` (how
long to read a neighbour's paper), `YAW_THRESHOLD = 18` (how far to turn for "side"),
`POINTS_WRONG = -0.5` (what a wrong answer costs). At the bottom, `QUIZZES`
(the three exams: title, time, number of questions, two moods each) and
`MOODS` (each mood's gossip line and the teacher's numbers) are data too: a
new exam or a new mood is a few lines here, not new code.

### `tracking/camera.py` — the webcam
Reading a frame makes the program wait ~20 ms for the camera. To avoid waiting,
`Camera` starts a **thread**: a second worker that runs at the same time as the
game. That worker (`keep_reading`) reads frames forever and saves the newest one
in `self.frame`. When the game calls `read()`, it just gets `self.frame`
straight away.

- **Reconnecting** (Emre): the thread also opens the camera in the
  background, tries again when frames are missing, reconnects after
  `CAMERA_RECONNECT_TIME`, and before the first picture also tries
  `CAMERA_FALLBACK_INDICES`. `read()` returns a copy of the newest frame, or
  `None` if there is no fresh one; then main.py shows "WAITING FOR CAMERA"
  with the clock stopped, instead of closing the game.
  `tests/test_camera.py` checks all of that with a fake camera.
- `release()` stops the thread; the thread gives the webcam back itself.

### `tracking/head_tracker.py` — where is the head pointing?
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

### `logic/game.py` — the rules of one exam
`Game` holds one exam: `state` (`PLAYING` / `WON` / `LOST`), `time_left`,
`warnings`, the popup, the scene, and three parts that each have their own
file (below): `paper` (an `ExamPaper`), `neighbours` (`NeighbourPapers`) and
`suspicion` (a `SuspicionBar`). `update(direction, dt, teacher)` runs once
per frame and asks each part in turn; `write(letter, direction)` and
`leave_blank(direction)` are called when a key is pressed. `Game(rng,
exam_time, questions)`: each exam of the run has its own time and number of
questions (`run.py` makes them).

**Writing (DOWN + A-D, or S):** `write()` does nothing unless you look down
(and no scene plays). **Any letter goes, read or not**: a letter you never
read is a guess. `S` writes a blank. Either way the next question starts
with nothing read (`neighbours.new_question()`). All questions answered →
`WON` ("handed in"). `knows_answer()` says whether the neighbour who knows
the current answer has been read; the hint on the screen uses it.

**WON means "graded".** Handing in is `WON`, and so is the clock running
out: `collect_paper()` fills the unanswered questions with blanks and sets
`time_ran_out`. Only being caught or 3 warnings is `LOST` (0 points).

**The suspicion bar** lives in `suspicion.py`; `update()` tells it whether
you are *seen* (sideways while `teacher.is_watching()`) or *staring* (SCREEN
while the teacher looks at the class). When it is full, `game.py` decides
what that means: seen → `"caught"`, `LOST`; staring → `warn()`: one more
warning, the bar starts over, 3 warnings → `LOST`. A close call gets a popup
("CLOSE CALL! +240", or "RAZOR CLOSE!").

**Scenes:** short moments where the game is frozen and something is
shown. `game.scene` says which (`WARNING_SCENE`, `CAUGHT_SCENE`,
`GAME_OVER_SCENE`) and `scene_time` how long it still lasts. While
`in_scene()` is True, `update()` only runs `update_scene()` (counting
`scene_time` down) and returns: the clock, the bar and copying stop, and
`main.py` stops the teacher too. This check comes *before* the game-over
check, so scenes still play after losing.
- `warn()` starts the warning scene.
- `lose()` starts the caught scene (if caught). After the last warning the
  warning scene is already playing.
- When a scene ends and the game is lost, `update_scene()` starts the game
  over scene; when that ends, `main.py` shows the end menu.
- The caught scene sends a `"rip"` event at the moment the paper is torn;
  the game over scene starts with `"nooo"`.
- `skip_scene()` (Space) only works after losing.

**Losing** emits `"lost"` and `"lost_<reason>"` (`lost_caught`,
`lost_warnings`), so each way of losing can have its own sound. The clock
running out emits `"time_up"`.

**The hidden point:** `under_suspicion()` is True while the bar is at or
above `suspicious_at` (each exam's `"suspicious"` in `QUIZZES`, lower each
exam). `main.py` passes it to `teacher.update(dt, keep_watching=...)`: his
watching does not end, so you have to look down until the bar drains.

**The score:** `score_parts()` lists the points of a graded exam, as
(name, points): one per question (`"Q1"`: +1000 right, −500 wrong, 0 blank),
then the bonuses you got (zeros are left out): `"EARLY BONUS"` (the share
of the time not used), `"SHARP EYES"` (`sharp_eyes`: counted in `update()`
when the first paper read for a question is the knowing one, with a
popup), `"CLOSE CALLS"`, `"WARNINGS"` and `"NINJA!"` / `"ALMOST NINJA"`
(`ninja_bonus()`: every answer right with 0 or 1 warning). The end screen counts them up one by one (`tally.py`).
`score()` adds them up (never below 0; 0 if lost).

**Looking DOWN** is the safe place: nothing fills, the bar drains.

### `logic/exam_paper.py` — your paper and the grade
`ExamPaper(rng, questions)` makes the answer key: each question gets a
random right letter (`right_letters`, A-D) and a random neighbour who knows
it (`knowing_side`, LEFT or RIGHT). `written` is what you wrote, in order: a
letter or `BLANK` (`"-"`). `says(side)` is what that neighbour's paper says
for the current question (the letter, or `"?"`). `results()` grades every
answer: `CORRECT`, `WRONG` or `EMPTY`; `points()` adds up their worth
(`POINTS_CORRECT` 1, `POINTS_WRONG` −0.5, `POINTS_BLANK` 0), so a grade can
be 2.5 / 3, or even below 0 if you guess badly. Tests set the key by hand
so they know the answers.

### `logic/neighbours.py` — reading a neighbour's paper
Gradual focus, Emre's idea:
- `focus_time` is a dictionary, one number per side: `focus_time[LEFT]`
  grows by `dt` while you look left, up to `PAPER_FOCUS_TIME` (2.5 s).
  `clarity(side)` turns it into 0 (blurry) … 1 (sharp); `draw_game.py`
  blurs the neighbour's picture by it.
- Every look starts blurry: when the direction changes, `reset_focus()`
  sets both back to 0. Short glances do not add up.
- No focus while the teacher sees you copying (`can_focus=False`: no gain,
  only risk).
- At full focus the side goes into `read_sides` (once per question), and
  `update()` returns `["read"]`. `game.paper_shows(side)` gives what is on
  the paper only once that side is read.

### `logic/suspicion.py` — the suspicion bar
`SuspicionBar.level` goes from 0 to 1. `update(seen, staring, dt)`:
- **Seen copying:** grows by `dt / CAUGHT_TIME` (full in 0.7 s). A
  `"spotted"` alarm plays each time a glance starts; `seen_copying` makes
  the bar red.
- **Staring:** grows by `dt / WARNING_TIME` (`STARE_GRACE_TIME` free, then
  `STARE_FILL_TIME`; `GRACE_PART` is the white mark on the bar).
- Both add to the **same** bar: after being seen, staring carries on from
  there.
- Otherwise it **drains slowly** (`SUSPICION_DRAIN_TIME` for a full bar).
  It never jumps to empty, because that would tell you the teacher looked
  away.
- **Close calls:** seen last frame, not seen now (you looked away in time):
  `"close_call"`, worth `close_call_points(level)`: `CLOSE_CALL_MIN` plus up
  to `CLOSE_CALL_PER_BAR` the fuller the bar was, plus
  `CLOSE_CALL_EDGE_BONUS` above `CLOSE_CALL_EDGE` (80 %). The closer to being
  caught, the more it pays.
- `is_full()` and `start_over()` are used by `game.py`.

### `logic/run.py` — three exams in a row
`Run` puts the exams of `QUIZZES` in order: the Quiz (3 questions, 150 s),
the Midterm (4, 130 s), the Final (5, 120 s). At the start it picks each
exam's mood (one of its two, at random), so the run is known in advance.
`new_game()` makes a fresh `Game` with that exam's time and questions;
`mood()` and `gossip()` are for the teacher and the loading screen.
`finish_quiz(game)` keeps the exam's result (handed in or not, the grade,
the score: 0 if failed) and moves on, so a failed exam does not end the
run. `total()` is the run's score; `score_parts()` lists each exam's score,
for the count on the results screen.

### `logic/slot.py` — the gossip slot machine
`run.py` has already picked today's mood; the slot machine only shows that
it is random. `reel_position(target, count, elapsed)` is a number: 0 =
the first mood in the middle of the window, 1 = the second, and so on
round and round. It goes `SLOT_TURNS` times round plus up to the target, in
`SLOT_SPIN_TIME`, with an ease-out (`1 - (1 - x)³`): fast at first, then
slowing to a stop. `passed()` counts the moods rolling past the middle
(main.py plays a tick for each); `mood_in_middle()` says which one is
there. `draw_briefing.py` draws the reel: the moods at `(k - offset) *
REEL_ROW` around the middle, clipped to the window (`screen.set_clip()`).

### `logic/tally.py` — counting the score, like Balatro
After an exam the score is not just shown: each part (each question, then
each bonus) appears in turn, `TALLY_STEP_TIME` apart, and the score counts
up to include it over `TALLY_COUNT_TIME`. `parts_shown(parts, elapsed)`
says how many parts have appeared `elapsed` seconds after the screen
opened, `running_score()` what the score shows right now, `is_done()`
whether it is over. Only numbers, so it is tested; `draw_results.py` draws
it and `main.py` plays a tick (a semitone higher each time) for every new
part. The run's results use the same count, with one part per exam.

### `logic/teacher.py` — the teacher
A **state machine**: the teacher is always in one state, and after a random
time (`TEACHER_DURATIONS`) moves to the next:

```
BUSY ──► TURNING ──► WATCHING ──► BUSY ...
```

- `place` is `BOARD` or `DESK`; after watching, it may switch (`move_chance`).
- `update(dt, keep_watching=True)`: a WATCHING that is over does not end
  (the suspicion bar is above the exam's hidden point).
- **Moods:** `Teacher(rng, mood)` or `set_mood(mood)` takes a name from
  `MOODS`: it changes how long he is busy and watching and how often he
  moves (`self.durations`, `self.move_chance`). For now a mood is only
  these numbers; bluffs and sneaky glances come later (PLAN.md 11.4).
  `None` is the plain teacher (`TEACHER_DURATIONS`, `MOVE_CHANCE`).
- `update(dt)` returns `["state:TURNING"]` etc. when the state changes.
- `is_watching()`: copying now fills the suspicion bar fast (after the first
  `CAUGHT_GRACE` seconds of `WATCHING`). `is_facing_class()`: staring counts.
- `image_name()` → e.g. `"classroom_board_busy"`: which picture to draw.
- `sounds(events, can_hear)` decides which teacher sounds the player hears:
  none while looking at the paper; the turning "hmm" once per turn, even if
  you look up late.
- It takes a `random.Random` so the tests can use a fixed seed and get the
  same "random" teacher every run.

### `logic/menu.py` — menus and head control
- `Menu(items)`: a list of item names and `selected`, the index of the
  chosen one. `move(-1)` / `move(1)` moves up/down and wraps around.
- `HeadMenuInput` turns the head angles of each frame into one of four
  actions: `UP`, `DOWN` (tilt the head past `MENU_PITCH_THRESHOLD`),
  `SELECT` (turn right past `MENU_YAW_THRESHOLD`), `BACK` (turn left).
  - A tilt moves after `MENU_MOVE_HOLD`, then again every
    `MENU_REPEAT_TIME` while held, so you can scroll.
  - A turn must be held for `MENU_SELECT_TIME`; `progress()` says how far
    (0..1) for the bar on the screen. A short glance does nothing.
  - After `reset()` (a new menu opened) and after every choice, nothing
    happens until the head has been **straight** once ("armed"). Otherwise
    one long turn right would choose on the next menu too.
- `pause()`: a key press or click in a menu (main.py calls it) turns head
  control off for `HEAD_PAUSE_AFTER_KEYS`; `paused_part()` (1 → 0) is
  drawn as the "KEYBOARD" / "HEAD CONTROL" box above the webcam
  (`head_indicator()` in `draw_menus.py`). After the pause the head must be straight
  once again, like after opening a menu.
- `loading_steps()` / `loading_progress()`: the loading bar's uneven fill
  (see `draw_loading` below). Here because it is plain maths that can be
  tested.
- The keyboard and mouse give the same four actions (`MENU_KEYS` in
  `main.py`), so the menu code does not care where an action came from.

### `logic/disclaimer.py` — the opening notice
`Disclaimer` keeps track of the notice like `Game` keeps track of the rules:
`letters()` typed so far (from `time`, `NOTICE_TYPE_DELAY` and
`NOTICE_TYPE_SPEED`), `press()` for Space (show all, then sign, then go on
after the stamp), `sign_progress()`, `stamp_age()` and `done()`. `update(dt)`
returns `"type"`, `"stamp"`; `press()` returns `"sign"`. `draw_disclaimer()`
(in `ui/draw_notice.py`) draws it: a wooden desk (`make_desk()`: a gradient with wavy grain lines),
the paper sliding in, the typed lines in a typewriter font, a signature
drawn from two sine waves, and the red stamp (`make_stamp()`) slamming down.

### `ui/glitch_intro.py` — our team's intro
A separate, self-contained file (only pygame, and NumPy for the sound), so it
can be copied into any project: `glitch_intro.play(screen)` runs its own
little loop for about 3 s and returns. The name is drawn twice, in red and
in cyan, *added* onto the black screen (`BLEND_ADD`): where the two copies
overlap they make white, where they are apart you see red and cyan edges
(like a broken screen). `glitch_blit()` also cuts the picture into strips
that jump sideways. A new random pattern each frame (`random.Random(frame)`)
makes it flicker. Then it settles, the "GP" mark (with a strip cut out and
moved) and "presents" fade in, and everything fades to black.

### `logic/bag.py` — random, but no repeats
`Bag(items).draw()` hands the items out in a shuffled order; when all are
used it refills and shuffles again, like the pieces in Tetris. The first
of a new round is never the last one handed out, so nothing comes twice in
a row. `main.py` keeps one bag per way of failing and picks the game over
conversation with it (`pick_chat()`, when the `"lost"` event comes), so the
two logos do not tell the same joke again soon.

### `logic/highscore.py` — the top scores
`load_top(path)` reads the best runs from a small JSON file, best first
(`[]` if it is missing or broken; an old file with only a best score still
works). `add_score(top, score, date)` puts a run's total into the list if it
is good enough and says where (0 = first), or `None`; only
`TOP_SCORES_KEPT` (5) are kept. `save_top(path, top)` writes it (and only
prints a message if it can't). main.py keeps the file next to itself
(`HIGH_SCORE_PATH`), so it works wherever the game is started from.

### `ui/sounds.py` — beeps and sound files
A sound is a long list of numbers telling the speaker where to be, 44,100 times
a second. `tone(freq, seconds)` makes a sine wave with NumPy, which sounds like
a beep. `make_waves()` builds the beeps; their names match the events.
`SOUND_FILES` replaces some of them with files from `assets/sounds/` (the
Luigi "hmm" for `state:TURNING`, the MGS alert for losing by being caught or
by warnings). A missing file keeps the beep. If the computer has no sound
device, `Sounds` stays empty and `play()` does nothing, so the game still runs.
`muted = True` (the Sound setting) also makes `play()` do nothing.
**Music:** `theme.mp3` is too long to load like the other sounds, so
`start_music()` plays it with `pygame.mixer.music`, which reads the file a
bit at a time while it plays ("streaming"), looping forever. Every frame
`main.py` calls `music(on, dt)`, which moves the volume a little towards
`MUSIC_VOLUME` (in the menus) or 0 (loading, the exam, or muted): a fade,
not a jump. `SILENT_SCREENS` in `main.py` says where it is off.
The buttons use `synth()`: a sine plus some of its 3rd and 5th harmonics,
which sounds brighter, like an old synthesizer (`menu_move`, `menu_select`,
`menu_back`). The score count's ticks (`tally0`, `tally1`, …) go up a semitone each:
the frequency times `2 ** (i / 12)`, which is how musical notes work.

### `ui/` — drawing
pygame draws onto a "surface" (the window) and `pygame.display.flip()` (in
`main.py`) shows it. Everything is drawn **again from scratch every frame**;
that is how all the animation works.

**One `Renderer`, six files.** `render.py` has the `Renderer` class, but
most of its drawing methods are in other files, one per kind of screen:

| File | Class | Draws |
|---|---|---|
| `style.py` | `NeonStyle` | helpers: `text()`, `shadow_text()`, `darken()`, `panel()`, `bar()`, `neon_text()`, `shout()`, `wrap()`, `preview()` |
| `draw_notice.py` | `NoticeDrawing` | the opening notice |
| `draw_menus.py` | `MenuDrawing` | start, loading, camera wait, the menus |
| `draw_briefing.py` | `BriefingDrawing` | the hallway gossip with the slot machine |
| `draw_game.py` | `GameDrawing` | the game screen, popup, pause |
| `draw_scenes.py` | `SceneDrawing` | warning, caught and game over scenes |
| `draw_results.py` | `ResultsDrawing` | the score count after an exam, the run's results, the top scores |

`class Renderer(NeonStyle, NoticeDrawing, MenuDrawing, GameDrawing,
SceneDrawing, ResultsDrawing)` inherits from all of them (these helper
classes are called "mixins"). So there is still one `renderer` object, and
any method can call any other with `self.`, whichever file it is in.
`render.py` itself only loads what they all need once: fonts
(`load_fonts()`), pictures (`load_pictures()`), and a few see-through layers.

- `camera_to_surface()` turns an OpenCV frame into a pygame image (resize,
  mirror, BGR→RGB).
- `load_classroom()` loads a classroom picture once, scales it to the window's
  width and cuts off the top (`CLASSROOM_TOP`) and bottom so it fits.
- Every screen is in the same neon 80s style (like the game Hotline Miami),
  all from code, no picture files. Things that move use `self.t`, the
  seconds since the program started, which `main.py` sets every frame;
  `beat()` turns it into a "thump" that is 1 on every `BEAT_TIME` and falls
  to 0. Boxes are always `panel()` (dark purple, pink edge), like the strips
  in the game, so all the screens look like one game.

**`draw_game.py`:** `draw_game` draws the teacher's picture (fading in by
`view`), or while you look away the picture for that direction
(`LOOK_AWAY_IMAGES`: your paper, or the left/right neighbour's paper, never
the teacher), then see-through strips: answers (`answer_boxes()`, `-` for a
blank), warnings and the clock at the top, the suspicion bar at the bottom.
- On your paper it writes `game.paper.written` on the answer lines
  (`OWN_ANSWER_Y`). For a neighbour, `neighbour_picture()` picks the picture
  with the letter circled on their paper (`left_B`, `right_unknown` for
  "?"), blurred by `neighbours.clarity()` (`blurred()` shrinks it and
  stretches it back). If that picture is missing, `neighbour_note()` draws
  the letter in a white note instead. `look_away_texts()` picks the hint
  ("Answer 2: guess with A-D, or S = blank").
- `hud_strip()` draws the see-through purple strips with a pink edge,
  `bar()` draws slanted bars (parallelograms), `shout()` draws big wobbling
  neon text (the popup, "FACE NOT FOUND"). The labels in the top strip are
  measured (`label.right`) so the boxes after them never overlap, whatever
  font the computer has.

**`draw_scenes.py`:** `draw_scene()` draws whichever scene is playing:
- `draw_warning_scene`: zooms into the teacher's picture, as if he walks up
  to you, then cuts to `classroom_warning.jpeg` under a white flash, shakes
  the screen and pulses red.
- `draw_caught_scene`: the teacher frozen with the red "!" (`make_exclaim()`
  draws it once: a black "!" moved in every direction for the outline, the
  red one on top), then a white flash and `classroom_caught.jpeg`.
  `scene_texts()` (shared with the warning scene) draws the red light, the
  two strips of text and the flash.
- `draw_game_over`: black, "GAME OVER", then the two logos chat
  (`GAME_OVER_CHAT`, one conversation per way of failing). The logos are
  drawn in code, once, as pictures: Claude's burst is thick lines with
  round tips in warm colours (`make_claude_logo()`), Gemini's star is a
  "superellipse" shape whose colours go round its middle
  (`make_gemini_logo()`: each pixel's angle picks the colour). Both have a
  dark cartoon outline and a pulsing glow behind (`make_glow()`).
  `logo_face()` puts a face on them: eyes with a shine, rosy cheeks, and a
  mouth that talks (opens and closes), laughs (^ ^ eyes, tongue) or
  smiles, with a blink now and then.

**`draw_results.py`:**
- `draw_end` after an exam. Handed in (or collected): `draw_tally()` over
  the frozen game: the question cards pop in one by one in their colour
  (`RESULT_COLOURS`: green right, red wrong, grey blank) with their points
  over them, then the grade, then the bonuses, while the big score counts
  up (`tally.running_score()`) and thumps (`thumped()`) each time a part
  arrives. Failed: the game over chat (`chat_screen()`, finished, both
  logos laughing) with the menu under it, so the screen does not change
  when the chat ends.
- `draw_run_end` after the run: each exam in a `panel()` (its grade or how
  it was failed, its score), the total counted up, and `top_scores()` with
  the new entry lit up (a pulsing pink bar). A new top score also gets
  "NEW HIGH SCORE! #2" and `confetti()`: 60 small rectangles, each with its
  own place, speed and swing from a fixed random seed, falling and
  tumbling with time.

**`draw_menus.py`:**
- (`draw_briefing.py`) `draw_briefing` is the **hallway gossip** screen
  before each exam: first the slot machine, the "MOOD-O-MATIC"
  (`slot_cabinet()`: a gold frame with bulbs placed by `bulb_spots()`;
  `slot_reel()`: the moods on a drum, smaller away from the middle, blurred
  when fast, shaded by `drum_shade()`; `slot_lever()`: pulled down by the
  head's select bar, springing back when the spin starts) with "SPIN", then the mood's `"story"` lines and its
  `"good"` (+, green) and `"bad"` (−, red) lines (`mood_story()`), and
  "I'M READY" as a menu item.
- `draw_loading` is the "chapter" screen after it: "Chapter 1/3", the
  exam's title, the date, and a bar with a percentage. The bar fills unevenly, like a real one:
  `menu.loading_steps()` makes a random plan of jumps when the loading
  starts, and `menu.loading_progress()` turns the time into how full the
  bar is.
- `draw_menu` draws the menus (the main menu also shows `top_scores()`):
  - `menu_background()`: a three-colour gradient (one line per pixel row)
    whose colours slide between `MENU_PALETTES`; light rays turning with
    time, drawn at half size, faded outwards (`ray_fade`) and smoothly
    stretched so their edges are soft; light film grain (hides colour
    steps), faint "scanlines" like an old TV, and darker corners
    (`vignette`). The layers that never change are made once in
    `make_menu_layers()` with NumPy, which works on all pixels at once.
  - `neon_text()` (in `style.py`): the text drawn four times: a soft
    shadow, a half see-through cyan and pink copy moved a few pixels, and
    the real colour on top; titles also get a blurred pink glow behind
    (`pygame.transform.gaussian_blur`), and so does the selected item
    (`item_glow()`).
  - `menu_title()` rocks the title (`math.sin(t)`) and makes it thump bigger
    on every `BEAT_TIME`. `menu_items()` draws the selected item bigger and
    rocking, with the select bar under it, and saves where each item is in
    `menu_rects` (for mouse clicks).
  - `pygame.transform.rotozoom` turns and scales a picture; that is all the
    "animation" is.
- The draw functions only **read** the game, the run and the teacher; they
  never change them.

### `main.py` — the loop
Everything is inside one class, `App`, so the methods can share the game,
the run, the screen name and the settings (`self.…`) without passing them
around: `go_to()`, `start_run()` (a new `Run`), `start_exam()` (shows the
hallway gossip), `start_loading()` (after "I'm ready"), `begin_playing()` (a fresh `Game` from the run and today's
mood for the teacher), `record_run()` (the top scores),
`calibrate_then(next_screen)`; `menu_action()` and `choose(item)` for the
menus; `handle_key()` and `handle_click()` for input; `count_score()` for
the ticks of the score count; `start_screen()`, `loading_screen()`,
`menu_screen()` and `game_screen()` draw one screen each; `run()` is the
loop.

Setup (`App.__init__`): open the window, sounds, camera, tracker,
calibration, game and the menus, and load the top scores. Then each frame:

(The window: `open_window()` always gives a 960×600 surface to draw on. The
`pygame.SCALED` flag stretches it to the real window size with black bars and
maps mouse clicks back, so no drawing code needs to know the screen size.
Normally it is a resizable window with a title bar, maximized at the start.
`pygame.FULLSCREEN` with `SCALED` is a borderless window the size of the
desktop, not a real video-mode change. F11 just calls `open_window()` again.)

1. **Input**: keys and mouse (`pygame.event.get()`); quit, calibrate, restart, F11 fullscreen,
   A-D (`LETTER_KEYS`) → `game.write(letter, direction)`, S (`BLANK_KEY`) →
   `game.leave_blank(direction)`.
2. **Camera**: `camera.read()`, then `tracker.read(frame, now)`.
3. **Per screen**:
   - DISCLAIMER: the notice, shown once when the game opens.
   - START / CALIBRATING: big preview, feed `calibration.add()`; when done,
     go to `after_calibration` (the main menu, the game, or settings).
   - BRIEFING: a menu screen with one item: "SPIN" starts the slot machine
     (`spin_time`; `turn_reel()` moves it on and ticks; no menu while it
     turns), then "I'M READY"; `draw_briefing`.
   - LOADING: count `loading_time` up to `LOADING_TIME`, then
     `begin_playing()`. Nothing in the game moves yet.
   - MENU / HELP / SETTINGS: `head_input.update(yaw, pitch, dt, ...)` may
     give an action → `menu_action()`; then `draw_menu`.
   - GAME: `direction = tracker.current_direction(...)`. If not `None`:
     `teacher.update(dt)`, filtered by `teacher.sounds()` (silence while
     looking down), and `game.update(direction, dt, teacher)`; play a sound
     per event. `classroom_view()` says how visible the classroom is (0 =
     black, 1 = shown, fading in over `FADE_TIME`). Draw; on top, a scene,
     the pause layer or the popup. Paused = nothing is updated, so the
     teacher and the clock freeze too. After failing, the scenes run even
     if the face is lost (nothing to pause), and Space skips them. When the
     exam is over → END (`go_to(END)` gives the result to `run.finish_quiz()`).
   - END: a menu screen too: `count_score()` moves the count on (`end_time`)
     and plays a tick per new part; `game_screen(..., over=True)` draws the
     frozen game with the classroom always shown, and `draw_end` the count
     and the menu on top.
   - RUN_END: the same count, over the run's exams, and `draw_run_end`.
     Space skips a count.
4. `crossfade(dt)`: for SCREEN_FADE_TIME after `go_to()` the old screen's
   last picture (copied in `go_to()`) is laid over the new one, more and
   more see-through, so screens blend into each other instead of jumping.
   `pygame.display.flip()` shows the frame; `clock.tick(FPS)` waits so we don't
   run faster than 30 fps.

### `tests/`
One test file per file in `logic/` (and for the head tracker and the
camera). They check the rules, the paper, the run, the teacher, the score
count, the top scores, the direction logic and the menus **without a
camera**, by calling the functions with made-up angles and times.
`test_game.py` uses a `FakeTeacher` whose watching/facing the test sets by
hand. Run them:

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
5. `game.update(LEFT, 0.033, teacher)` → the teacher is not watching, so
   `game.suspicion.update()` drains the bar a little; you were already
   looking left, so `game.neighbours.update()` grows `focus_time[LEFT]` from
   1.20 to 1.233 s. Returns `[]`.
6. Nothing to play.
7. `classroom_view(LEFT, ...)` is 0, so `renderer.draw_game()` draws the
   left neighbour's picture blurred by `neighbours.clarity(LEFT)` = 1.233 / 2.5 ≈
   0.49 (still too blurry to read) with "Reading answer 1 from the left"
   (there is no bar for it: the blur shows how far you are).
8. `pygame.display.flip()`: you see it.
9. Keep looking: at 2.5 s, `"read"` and the picture is sharp: her paper
   shows, say, "C" circled. You look down and press C: `game.write("C",
   DOWN)` writes it on your paper. (Had you looked away at 2 s, it would
   have started blurry again. You could also have pressed a letter without
   reading anything: a guess, −0.5 if wrong.)

Had the teacher been `WATCHING`, step 5 would instead raise the suspicion bar
by 0.033 / 0.9, not sharpen the paper, and return `["spotted"]` on the first
such frame: the alarm.

---

## 5. Try it yourself

Small changes to learn by doing. Run `./run.sh` (Windows: `run.bat`) after each one.

1. **Easy:** in `settings.py`, set `PAPER_FOCUS_TIME = 1.0`. Copying is now much faster.
2. **Easy:** in `QUIZZES`, give the Quiz 5 questions instead of 3. Check that
   the answer boxes on screen update by themselves (look at how
   `draw_game.py` uses `game.paper.size()`).
3. **Easy:** set `POINTS_WRONG = -1.0`. Guessing is now a bad idea. Run the
   tests: which ones notice, and which don't (they read the number from
   `settings.py`)?
4. **Medium:** add a seventh mood to `MOODS` and put it in one exam's pool.
   No other file needs to change.
5. **Medium:** in `ui/sounds.py`, change the `"read"` sound to two notes, like
   `"won"` is built.
6. **Harder:** in `logic/suspicion.py`, make looking DOWN drain the
   suspicion bar twice as fast as other directions. Then add a test for it
   in `tests/test_game.py`.
7. **Harder:** print the yaw and pitch to the terminal in `main.py` every
   frame, then look left, right and down and watch the numbers change.
