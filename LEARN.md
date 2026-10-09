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
| | `verdict.py` | The grade roast after the final | nothing! |
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
DISCLAIMER ──signed + stamped──► START ──Space/click──► CALIBRATING ──4 poses──► MENU
                                                                         │
    HELP (the guide) ◄── "How to play" ── MENU ── "Settings" ──► SETTINGS ──"Recalibrate"──► CALIBRATING
                                │                                                      (back to SETTINGS)
                              "Play" ──► RUN_INTRO ──end───► CHARACTER ── pick ──► a new run
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
results" after the last exam. HELP is not a menu screen: it is the guide
(`guide_screen()`), and when the guide is finished the **practice exam**
starts (`start_practice()`): a `Run(practice=True)` of one short exam,
straight to LOADING (no gossip), then GAME and END like any exam, but not
counted anywhere; END offers "Play for real" / "Main menu", and R plays
the practice again (`restart()`).

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
- **Windows:** `open_device()` opens the webcam with DirectShow
  (`cv2.CAP_DSHOW`), which is much quicker there than Windows' default
  (Media Foundation); `WINDOWS_DIRECTSHOW = False` switches it off.

### `tracking/head_tracker.py` — where is the head pointing?
The hardest file. Three parts:

**a) `read(frame, now)`: find the face, compute angles**
1. Give the frame to MediaPipe's **Face Landmarker** (the model file
   `face_landmarker.task`, read into memory by us and handed over as bytes:
   given a file name, MediaPipe fails on Windows when the folder's path has
   letters like ç, ş or ı). It returns 478 points on the face (`landmarks`) and a
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
- `raw_direction()` compares the angles with the limits
  `down_threshold`, `left_threshold` and `right_threshold`: past them →
  `DOWN`, `LEFT`/`RIGHT`, otherwise `SCREEN`. They start as the fixed
  `PITCH_DOWN_THRESHOLD` (23°) and `YAW_THRESHOLD` (18°); calibration
  replaces them with the player's own (`set_thresholds()`).
- `update_direction(now)` adds a **hold time**: a new direction must last
  `HOLD_TIME` (0.1 s) before it's believed. While a new direction is waiting it's called the
  `candidate`.

**c) `current_direction(now, face_found)`: what if the face disappears?**
The face often vanishes from MediaPipe's view. The rules, in order:

| Situation | Result | `status` (shown at the top right of the game) |
|---|---|---|
| Face found | the tracked direction | `""` |
| Face vanished while the head was tilted down (`LOST_DOWN_PITCH`) **or moving down fast** (`LOST_DOWN_SPEED`) | `DOWN` (looking at the paper hides the face) | `"head down"` |
| Face vanished less than 0.6 s ago | the last direction (mid-turn gap) | `"face lost..."` |
| Otherwise | `None` → the game pauses | `"face not found"` |

The "moving down fast" part (`went_down()`): a quick nod often loses the
face before the head is 8° down, so the tracker also looks at which way it
was going. `remember_pitch()` keeps the raw pitch of the last
`PITCH_TREND_TIME` seconds with a face, and `pitch_speed()` is how many
degrees per second it changed from the oldest to the newest of them. If
the face vanished while that was below `-LOST_DOWN_SPEED`, it went down to
the paper.

`draw_face()` draws the face outline, eyes, lips and the nose arrow onto the
frame, so you can see what the tracker sees.

**`Calibration`** asks for four poses in turn (`CALIBRATION_POSES`:
screen, left, right, down). For each, the player presses Space
(`start()`), and the angles are collected for `CALIBRATION_SAMPLE_TIME`
(1 s) and averaged. The screen pose goes to `calibrate()` (the neutral).
After the last pose, `pose_threshold()` turns each pose into a threshold:
`CALIBRATION_SHARE` (60 %) of the way to it, between
`CALIBRATION_MIN_ANGLE` and `CALIBRATION_MAX_ANGLE`, so you only need to
turn a bit more than half as far as you showed. A pose that went the wrong
way keeps the fixed threshold. If the face is lost, that pose is measured
again, except looking down (it often hides the face: the last angles are
used). main.py also gives the left/right turns to the menus
(`HeadMenuInput.set_turns()`).

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
`MUGSHOT_SCENE`, `GAME_OVER_SCENE`) and `scene_time` how long it still lasts. While
`in_scene()` is True, `update()` only runs `update_scene()` (counting
`scene_time` down) and returns: the clock, the bar and copying stop, and
`main.py` stops the teacher too. This check comes *before* the game-over
check, so scenes still play after losing.
- `warn()` starts the warning scene.
- `lose()` starts the caught scene (if caught). After the last warning the
  warning scene is already playing.
- When the warning or caught scene ends and the game is lost,
  `update_scene()` starts the mugshot scene; when that ends, the game over
  scene; when that ends, `main.py` shows the end menu.
- The caught scene sends a `"rip"` event at the moment the paper is torn;
  the mugshot sends `"pen"` when the teacher starts writing
  (`MUGSHOT_WRITE_DELAY`); the game over scene starts with `"nooo"`.
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
The key is random but without streaks: `answer_key()` only picks from the
letters that are not the last one and have come fewer than
`MAX_SAME_LETTER` (2) times, and `knowing_sides()` switches sides after
`MAX_SIDE_STREAK` (2) of the same side in a row.

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
`Run(practice=True)` is the practice exam after the guide: one exam,
`PRACTICE_QUIZ` (2 questions, 60 s, the sleepy "practice" mood);
`chapter()` says "PRACTICE" instead of "CHAPTER 1/3" on the loading screen.

### `logic/slot.py` — the gossip slot machine
`run.py` has already picked today's mood; the slot machine only shows that
it is random. `reel_position(target, count, elapsed)` is a number: 0 =
the first mood in the middle of the window, 1 = the second, and so on
round and round. It goes `SLOT_TURNS` times round plus up to the target, in
`SLOT_SPIN_TIME`, with an ease-out (`1 - (1 - x)³`): fast at first, then
slowing to a stop. `passed()` counts the moods rolling past the middle
(main.py plays a tick for each); `mood_in_middle()` says which one is
there. `draw_briefing.py` draws the machine: a cabinet with a dome
(`cabinet_shape()`: an oval and a box drawn white on a "mask", a purple
gradient kept only inside it; `pygame.mask` gives the outline for the neon
edge), small bulbs all round that edge (`edge_bulb_spots()`: one every
`EDGE_BULB_GAP` pixels walked along the outline; every other one lit,
swapping every `EDGE_BULB_SWAP` seconds), a gold-framed reel window with a glass gleam
(`glass()`), the lever on its side, and a glowing screen under the reel
(`info_screen()`) where the story and the + / − lines light up after the
stop. The reel: the moods (wrapped to two lines, `reel_line()`) at
`(k - offset) * REEL_ROW` around the middle, clipped to the window
(`screen.set_clip()`).

### `logic/tally.py` — counting the score, like Balatro
After an exam the score is not just shown: each part (each question, then
each bonus) appears in turn, `TALLY_STEP_TIME` apart, and the score counts
up to include it over `TALLY_COUNT_TIME`. `parts_shown(parts, elapsed)`
says how many parts have appeared `elapsed` seconds after the screen
opened, `running_score()` what the score shows right now (and
`running_value()` the same with its fraction, so the slot-machine reels
can roll smoothly), `is_done()` whether it is over, `is_counting()` whether
a part is counting up right now. `strength(score, exams)` (0..1) says how
wild the slot-machine effects are, from the score and
`TALLY_FX_FULL_SCORE`; `jackpot()` is true from `TALLY_JACKPOT_SHARE` of
it. Only numbers, so it is tested; `draw_results.py` draws
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
the paper sliding in, the typed lines in a typewriter font, the
"signature" (someone trying to draw a helicopter: `helicopter_strokes()`
builds it from ovals and lines, `shaky()` makes the hand tremble, and it
is drawn stroke by stroke as `sign_progress()` grows), and the red stamp
(`make_stamp()`) slamming down.

### `logic/guide.py` — the "How to play" guide
`GUIDE_STEPS` is the script: each step is a few chat lines `(who, text)`
and maybe a `task`: `("look", DOWN)` (hold that direction for
`GUIDE_HOLD_TIME`), `("read", LEFT)` (keep looking until the paper is sharp,
`PAPER_FOCUS_TIME`, like in the game), `("write", "B")` (look down and press
B; `None` = any letter). A step can also say what the teacher is doing
(`"teacher": "watching"`) and a `"sound"` to play when it starts (the "hmm").
`Guide` works like `Disclaimer`: `update(dt, direction)` types the current
line (`letters()`), waits `GUIDE_LINE_PAUSE`, goes to the next line; on the
last line of a step with a task it waits (`waiting()`) until the task is
done, says "read" (the ding), waits `GUIDE_STEP_PAUSE` and goes on.
`press(letter, direction)` is for the write tasks, `skip()` for Space. It
returns events like `"talk:GEMINI"` every `GUIDE_BLIP_LETTERS` letters, which
`main.py` turns into a talking blip in that voice. `said` keeps every line
started, so the screen can show the last two. `draw_guide()` (in
`ui/draw_guide.py`) draws what you would see in the game where you look (the
classroom, your paper with what you wrote, a neighbour's paper blurred by
`clarity()`), the task banner and the chat: at the bottom while you look at
the screen, and only the newest line, higher up, while you look away, so
the papers are not covered.

### `logic/verdict.py` — the grade roast
`VERDICTS` gives each letter (AA … FF) a few conversations; main.py picks
one with a `Bag` per letter. `Verdict(letter, lines)` is like a small
`Guide` without tasks: `starts` says when each line begins (after the one
before is typed and `VERDICT_LINE_PAUSE`), `letters()` how much of each is
typed at `time`, `update(dt)` returns the talking blips, `skip()` types
everything, then closes, and `finished()` is true `VERDICT_HOLD` seconds
after the end. `hype` comes from `VERDICT_HYPE` (BB 1, BA 2, AA 3; others
0): the lines then start only after `reveal` seconds, the show, and
`update()` also returns the show's sounds (`HYPE_SOUNDS`) and a
`"firework"` for each of `firework_times()` during it. The drawing
(`draw_verdict()` in `ui/draw_scenes.py`) uses the same `firework_times()`,
so every bang you hear has a firework you see. main.py's
`update_verdict()` starts it `VERDICT_DELAY` after the grade stamp (and
the top score's name), once per run, unless `roast_on` is off (Settings).
The effects: the letter `slam`s from 3× its size (like a stamp), a
smoothstep `rise` takes it to the top when the chat starts, `light_rays()`
are thin triangles turning on a see-through layer, `firework_burst()` is
sparks flying out with air drag (`1 - e^(-kt)`: fast, then slower) and
gravity (`g t² / 2`), and the shake draws the finished screen again a few
random pixels off.

### `logic/character.py` — who you are
The characters are data: `CHARACTERS` in `settings.py` lists for each one
only the rules it changes (and its texts); `rules(name)` adds `DEFAULTS`
(no change) for the rest. So a new character, or tuning one, needs no new
code. `Game(character=...)` reads them:
- `focus_speed` goes to `neighbours.update(..., speed=)` (glasses read faster);
- `seen_speed`, `stare_speed` and `creep_time` go to `SuspicionBar` (the cap
  and the lazy guy; with `creep_time` the bar creeps up while you look
  anywhere but your paper, `update(..., away=True)`);
- `both_know` goes to `ExamPaper` (`says()` gives the letter on both sides);
- `greek` only changes what is drawn: `neighbour_letter()` turns B into β,
  and `draw_game` shows `left_greek_B` instead of `left_B` (or a note);
- `jokers` is `game.jokers`; `use_joker()` writes `paper.right_answer()`;
- `hand_in_share` gives `deadline()`: handing in with less time left adds a
  "NERD WAS LATE" row of `-late_penalty` to `score_parts()`;
- `busy_times` / `watching_times` stretch the teacher (`set_mood()`; the
  front-row student, the 7th-year legend, the "quick question" guy).
`screen_clarity(rules, look_time)` is how sharp the classroom is after
looking up (glasses: from `screen_blur_start` to 1 in
`screen_focus_time`). `Energy` is the energy drink addict's day: a coin
toss (`RUSH` or `CRASH`); `world_speed()` (the clock and the bar use
`dt * world_speed()`, so does the teacher in main.py) and `focus_speed()`;
`update(dt)` starts and ends the sleepy spells (events `"sleepy"`,
`"awake"`).

### `logic/run_intro.py` — the briefing, timed to the music
The character music was measured once (with numpy, from the file): 147
beats per minute (`CHARACTER_MUSIC_BPM`), a strong hit on the first beat of
every bar from `INTRO_FIRST_HIT` (0.81 s), and the drop at `INTRO_DROP`
(11.84 s), where it gets twice as loud. `BEAT` and `BAR` (4 beats) follow
from the tempo. `INTRO_LINES` are the sarcastic lines, one per bar, ending
on "DON'T GET CAUGHT.", which stays `INTRO_TITLE_BEATS` (8) instead of 4;
`INTRO_END` is when it is gone. `intensity(line)` goes from 0 (first line)
to 1 (last) and the drawing uses it to go from soft to hard. `line_time(i)`, `current_line(t)` and `since_line(t)` say which one is on
screen and since when; `is_over(t)` is true from `INTRO_END`. `since_beat(t)`
and `since_bar(t)` let the drawing thump on the beat (also on the character
screen). `draw_run_intro()` (`ui/draw_run_intro.py`) draws it: rushing
diagonal stripes, the line slamming down from 260 % with a white flash and
a shake (only the newest line is on screen). `grow()` turns `intensity()`
into how strong the shake, slam, flash, thump and stripe speed are (a
`BUILD_*` pair: soft on the first line, hard on the last); the title fills
the width and swaps red/white on every beat. A different song needs the three
numbers measured again.

The character screen (`ui/draw_characters.py`) is a sliding row
(`carousel()`): each portrait's distance from the middle `d = (i - slide)`
(the short way round) sets its x and its size; `main.py` moves `slide`
towards the chosen one a bit every frame (`CAROUSEL_SPEED`), so it glides.
The portraits are drawn on a small picture of their own
(`portrait_image()`) and scaled.

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
`TOP_SCORES_KEPT` (5) are kept. Each entry is `{"score", "date", "name"}`;
the name is `""` until it is typed, and `set_name(top, place, name)` adds it.
`save_top(path, top)` writes it (and only
prints a message if it can't). main.py keeps the file next to itself
(`HIGH_SCORE_PATH`), so it works wherever the game is started from.
`record_run()` saves a new top score at once without a name (so quitting
while typing does not lose it), then saves it again with the name.

### `logic/grade.py` — the semester grade, on a curve
Like a real teacher: no letter for one exam, one letter for the semester
(the run). `semester_grade(total, share, past_totals)`: with at least
`GRADE_CURVE_MIN` (5) earlier runs, `curve()` gives their average and
standard deviation (`statistics.mean`, `statistics.pstdev`), `z_score()`
says how many standard deviations the total is above the average, and
`letter_for_z()` looks it up in `GRADES` (settings.py). With fewer runs
there is no class yet: `letter_for_share()` uses the share of the exam
points (`Run.share()`). A total of 0 is FF. `class_average()` is shown
after each exam.

The scores of every play are kept in the same file as the top scores
(`highscore.py`: `load_history()`, `remember()`, `save_top(path, top,
history)`): `{"runs": [...], "exams": {"THE QUIZ": [...], ...}}`, the newest
`GRADE_HISTORY_KEPT` (200) of each. main.py's `record_exam()` (at END) reads
the class average of that exam *before* adding the new score, and
`record_run()` (at RUN_END) grades the run *before* adding it, so you are
never curved against yourself. `draw_run_end()` stamps the grade on
(`grade_stamp()`) `GRADE_STAMP_DELAY` after the count, with the "stamp"
sound (`self.stamped`, so skipping the count with Space still plays it).

### `logic/name_entry.py` — three letters, like an arcade machine
`NameEntry` holds `NAME_LETTERS` (3) letters and which one is chosen
(`slot`). `roll(+1 / -1)` turns the chosen letter through `ALPHABET`
(Z wraps to A), `next()` goes to the next letter (after the last one:
`done`), `back()` to the one before, `type(letter)` sets it and goes on,
`finish()` ends it. main.py feeds it the menu actions while `naming()` is
true (after the run's count, when the run got into the top scores): tilt
up/down = `roll()`, turn right = `next()`, turn left = `back()`; and keys
(`name_key()`): A-Z type, Enter/Esc finish. The letter keys are checked
before all the other keys, so R, M, T and K type instead of restarting.
Until the name is done the menu is hidden and does nothing.

### `ui/sounds.py` — beeps and sound files
A sound is a long list of numbers telling the speaker where to be, 44,100 times
a second. `tone(freq, seconds)` makes a sine wave with NumPy, which sounds like
a beep. `make_waves()` builds the beeps; their names match the events.
`SOUND_FILES` replaces some of them with files from `assets/sounds/` (the
Luigi "hmm" for `state:TURNING`, the MGS alert for losing by being caught or
by warnings). A missing file keeps the beep. If the computer has no sound
device, `Sounds` stays empty and `play()` does nothing, so the game still runs.
`muted = True` (the Sound setting) also makes `play()` do nothing.
`SOUND_VOLUMES` makes some quieter (the chalk). **Loops:** `loop(name, on)`
is called every frame; it starts the sound looping (`play(loops=-1)`) when
`on` turns true and fades it out when it turns false. main.py's
`chalk_heard()` says when: in the exam, `teacher.erasing()` (busy at the
board), not looking down, no scene, not paused. Made in code (stand-ins
for files the team may add): `footsteps()` (thuds that get louder, the
event comes from `teacher.update()` when he changes place and from
`game.warn()`), `rip()` (two tearing pulls: high-passed noise with
crackle and clicks), `chalk()`.

**Mood pictures:** `load_pictures()` (render.py) also loads
`<picture>_<mood>` for every picture and every mood in `MOODS` if the
file exists, and `picture(name)` returns today's version (main.py sets
`renderer.mood` before each exam). The drawing code always asks
`self.picture(...)`, never `self.classroom[...]`, so new mood pictures need
no code. A mood's `"place"` (settings.py) is where the teacher starts
(`Teacher.home`); with `"move": 0` he stays there.
**Music:** `theme.mp3` (menus) and `thrilling.mp3` (exam) are too long to
load like the other sounds, so they are played with `pygame.mixer.music`,
which reads the file a bit at a time while it plays ("streaming"), looping
forever. It can stream only one file, so `MUSIC_FILES` names two tracks,
`"menu"` and `"exam"`. Every frame `main.py` asks `music_track()` which one
should play (None = silence: the notice, loading, after failing an exam)
and calls `music(track, dt)`. That moves the volume a little towards the
track's volume (`MUSIC_VOLUME`, `EXAM_MUSIC_VOLUME`) or 0: a fade, not a
jump. When the track changes, the old one fades to 0 first, then
`load_track()` starts the new one from its beginning and it fades in.
The third track, `"character"`, is different: the run intro is timed to
it, so `cut_to()` starts it at once at full volume, and
`music_position()` says how far into it the player is (main.py's
`music_time()` uses its own count when there is no real sound device).
**Talking blips:** while the game over chat is typed, `typed_letters()`
(in `draw_scenes.py`) says how many letters of each line are typed. Each
frame `main.py` compares it with the frame before (`chat_blips()`) and
plays a short blip every `CHAT_BLIP_LETTERS` letters, in the speaker's
voice (`TALK_PITCHES`: Gemini higher, Claude lower, a random one of three
pitches each time).
The buttons use `synth()`: a sine plus some of its 3rd and 5th harmonics,
which sounds brighter, like an old synthesizer (`menu_move`, `menu_select`,
`menu_back`).
**The heartbeat:** a razor close call (game.py adds a `"heartbeat"` event)
plays `heartbeat()`: two thumps per beat ("lub-DUB") at `HEARTBEAT_BPM`,
each a falling low note pushed through `tanh` so it sounds hard (and the
extra overtones are heard on laptop speakers). Meanwhile the music sounds
far away: `far_music()` takes the next `HEARTBEAT_TIME` seconds of the
song (the exam track is also loaded whole, `track_samples`, only for this),
runs `far_away()` on it and plays that, while the real music drops to
`HEARTBEAT_MUSIC_DUCK` and then fades back. `far_away()` uses the FFT: in
the "frequency world" cutting the high notes is multiplying by a curve
(`muffle`), and adding an echo is multiplying by the echo's own FFT (the
echo is noise that dies away, like a big hall). The score count's ticks (`tally0`, `tally1`, …) go up a semitone each:
the frequency times `2 ** (i / 12)`, which is how musical notes work.

### `ui/` — drawing
pygame draws onto a "surface" (the window) and `pygame.display.flip()` (in
`main.py`) shows it. Everything is drawn **again from scratch every frame**;
that is how all the animation works.

**One `Renderer`, seven files.** `render.py` has the `Renderer` class, but
most of its drawing methods are in other files, one per kind of screen:

| File | Class | Draws |
|---|---|---|
| `style.py` | `NeonStyle` | helpers: `text()`, `shadow_text()`, `darken()`, `panel()`, `bar()`, `neon_text()`, `shout()`, `wrap()`, `preview()` |
| `draw_notice.py` | `NoticeDrawing` | the opening notice |
| `draw_menus.py` | `MenuDrawing` | start, loading, camera wait, the menus |
| `draw_briefing.py` | `BriefingDrawing` | the hallway gossip with the slot machine |
| `draw_game.py` | `GameDrawing` | the game screen, popup, pause |
| `draw_scenes.py` | `SceneDrawing` | warning, caught and game over scenes; the grade roast |
| `draw_mugshot.py` | `MugshotDrawing` | the mugshot after losing: your webcam photo on the taped-up exam |
| `draw_debug.py` | `DebugDrawing` | the debug panel (F3) over any screen: webcam with the face mesh, rotation matrix, yaw/pitch chart and graph, the direction decision, the exam's state |
| `draw_results.py` | `ResultsDrawing` | the score count after an exam, the run's results, the top scores |
| `draw_guide.py` | `GuideDrawing` | the "How to play" guide |
| `draw_characters.py` | `CharacterDrawing` | the character screen: the list, the card, portraits drawn in code (`portrait()` draws a head and shoulders, then `portrait_<key>()` adds the cap, the glasses, the can...) |

`class Renderer(NeonStyle, NoticeDrawing, MenuDrawing, BriefingDrawing,
GameDrawing, SceneDrawing, ResultsDrawing, GuideDrawing, CharacterDrawing)` inherits from all of them (these helper
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
- The mugshot (`draw_mugshot.py`): when `main.py` hears the `"lost"`
  event it calls `take_mugshot(frame, tracker.face_box())`. `face_box()`
  is the smallest box around the 478 face points; `crop_box()`
  (`logic/mugshot.py`, tested) turns it into the part of the picture to cut
  out: `MUGSHOT_FACE_ZOOM` times as tall as the face, the photo's shape,
  always inside the picture. The cut-out is mirrored and laid on both paper
  pictures, but only on their pure green pixels (`green_mask()`), so the
  paperclip stays on top. `draw_mugshot()` fades the plain paper in, then
  shows the written paper from left to right (only between the columns
  where the two pictures differ, `writing_columns()`): that looks like the
  writing. No pictures: the photo and red words on black.
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
  the frozen game, as two tables made with `table_frame()`:
  `question_table()` (a row per question: what you wrote, the key, the
  result, the points; each row glows in its colour, `RESULT_COLOURS`:
  green right, red wrong, grey blank, when its turn comes, `table_row()`,
  and its points pop in, `row_points()`; then the grade) and
  `bonus_table()` (a row per bonus), while the big score counts
  up as a slot machine (`slot_score()`): one reel per digit
  (`reel_cell()`: two digits on a paper drum, moved by the fraction of
  `running_value() / 10^place`, with blurred copies when fast; stopped,
  each reel clunks onto its whole digit), a gold frame with bulbs
  (`reel_frame()`), sparks when a part arrives (`sparks()`, a fixed seed per
  part so they do not flicker), a shake while counting, all stronger for a
  bigger score (`tally.strength()`), and "JACKPOT!" flashing for a huge
  one. Failed: the game over chat (`chat_screen()`, finished, both
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
   - START / CALIBRATING: big preview, Space = `calibration.start()` for
     each pose, feed `calibration.add()`; when done,
     go to `after_calibration` (the main menu, the game, or settings).
   - BRIEFING: a menu screen with one item: "SPIN" starts the slot machine
     (`spin_time`; `turn_reel()` moves it on and ticks; no menu while it
     turns), then "I'M READY"; `draw_briefing`.
   - LOADING: count `loading_time` up to `LOADING_TIME` (the bar), then
     `EXAM_TITLE_TIME` more for the title card (`draw_exam_title()`: the
     exam's `"title"` and `"tagline"` from `QUIZZES` slam in, with a thud),
     then `begin_playing()`. Nothing in the game moves yet.
   - HELP: `guide_screen()`: the head direction
     (`tracker.current_direction()`, the last one kept if the face is lost)
     goes to `guide.update()`; its events are played (`play_guide_sounds()`);
     `draw_guide`. When the guide is finished → the practice exam. Keys go to `guide_key()`.
   - RUN_INTRO: `intro_screen()`: `music_time()` → `draw_run_intro`; after
     the title (or Space / turning right) → CHARACTER.
   - "ARE YOU SURE?": choosing QUIT or MAIN MENU (or Esc on the main menu)
     sets `self.confirming` (`ask_confirm()`); while it is set every menu
     action goes to `answer_confirm()` (SELECT = yes, BACK = no) and
     `draw_confirm` is drawn over the menu. Selecting disarms the head, so
     "yes" needs a second, fresh turn to the right.
   - CHARACTER: a menu screen whose items are the keys of `CHARACTERS`;
     the head works sideways here (`head_input.horizontal`, `HORIZONTAL` in
     menu.py: turn left/right = previous/next, look down = choose, up = back);
     the row slides (`self.carousel`); choosing one sets `self.character`
     and starts the run; `draw_characters`.
   - GAME (characters): the teacher gets `dt * game.world_speed()` (the
     sugar rush), `set_mood()` gets the character's `busy_times` /
     `watching_times`, J calls `game.use_joker()`, and `screen_clarity()`
     tells `draw_game` how blurry the classroom is (glasses).
   - MENU / SETTINGS: `head_input.update(yaw, pitch, dt, ...)` may
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
     A new top score: after the count, the name boxes (`name_boxes()`)
     instead of the menu until the name is typed.
     Space skips a count.
4. `crossfade(dt)`: for SCREEN_FADE_TIME after `go_to()` the old screen's
   last picture (copied in `go_to()`) is laid over the new one, more and
   more see-through, so screens blend into each other instead of jumping.
   Then, if F3 turned it on, `draw_debug(now)` lays the debug panel over
   it: the face mesh is drawn on a *copy* of the webcam picture (the
   mugshot must get a clean one), and `renderer.draw_debug()` draws the
   rest from the tracker's numbers (`rotation`, `raw_yaw`/`raw_pitch`
   before smoothing, the thresholds, `candidate`/`candidate_since` for the
   HOLD_TIME bar). `track_ms` is how long `tracker.read()` (MediaPipe) took.
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
