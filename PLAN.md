# Game Plan — "Don't Get Caught"

ME461 group project by **Glitch Please**. A webcam game written only in Python
and its libraries, controlled by where the player turns their head.

This file is the design and build plan. It covers the full game, the first
demo, and ideas for later. `NOTES.md` stays the commit-by-commit log.

---

## 1. The idea

The player is a student sitting an exam. The monitor shows the classroom from
the student's seat: the teacher, the board, the other desks. The webcam watches
the player's head. The player can do three things:

| # | Action | Head direction | Why do it |
|---|---|---|---|
| 1 | Look at the exam paper | **Down** | Safe place to be. |
| 2 | Look at the teacher | **Straight at the monitor** | The only way to *see* what the teacher is doing, but staring too long is suspicious. |
| 3 | Copy from a neighbour | **Left or right** | The only way to fill answers, but if the teacher sees it, the game is over. |

**Goal:** fill all the answers (5 by default) without getting caught and
without collecting too many warnings.

### Why it is fun: the information problem

When the player looks down or to the side, **they cannot see the monitor**.
So while copying they are blind to the teacher. That creates the core loop:

1. Glance at the monitor to check the teacher (option 2).
2. When it looks safe, look sideways and copy (option 3).
3. Listen while copying: sounds tell you if the teacher is moving.
4. Look back or down before the teacher turns around.
5. Do not stare at the teacher too long, or you get a warning.

This answers "how does the player decide when to copy": they read the
teacher's pattern from short glances and from sounds, then pick their moment.
Sound is a core mechanic, not decoration.

---

## 2. Controls: head tracking

### 2.1 What we detect

Each webcam frame becomes one of these:

| Result | Meaning |
|---|---|
| `DOWN` | Head tilted down past a threshold → option 1 |
| `SCREEN` | Head roughly straight → option 2 |
| `LEFT` / `RIGHT` | Head turned sideways past a threshold → option 3 |
| `None` | No face found → game pauses, shows **"Face not found"** |

### 2.2 How

- **Library:** MediaPipe **Face Landmarker** (model file `face_landmarker.task`,
  already downloaded). The current `tracker.py` uses the full-body Pose model,
  which needs the whole body in view and gives a poor head angle. A seated
  player only shows head and shoulders, so we switch to the face model.
- The Face Landmarker returns a **transformation matrix** for the face. From it
  we compute two angles:
  - **yaw**: turning left/right (0° = facing the camera)
  - **pitch**: nodding up/down (0° = facing the camera)
- **Calibration** at the start of every game: the player sits normally, looks
  at the screen and clicks **Calibrate** (or presses Space); for 2 seconds we
  average the angles and store them as the player's *neutral*.
  All thresholds are measured from this neutral, so it works no matter where
  the webcam sits or how tall the player is.
- **Thresholds** (starting values, to be tuned):
  - `DOWN` if pitch is more than **20°** below neutral
  - `LEFT`/`RIGHT` if yaw is more than **25°** from neutral
  - otherwise `SCREEN`
- **Smoothing:** exponential moving average of the angles, so one noisy frame
  does not jump the value.
- **Hold time (0.2 s):** a new direction must last 0.2 s before it counts.
  This stops jitter from creating fake glances, which could get the player
  caught unfairly.
- **Sign switches:** `YAW_SIGN` and `PITCH_SIGN` constants. If left/right come
  out swapped, or up is read as down, flip one to `-1`.

A first version of this is in `head_tracker.py` (written before this plan; not
tested yet with a real person).

### 2.3 Face not found

The face often vanishes for a few frames in the middle of a head turn, so gaps
shorter than **0.6 s** are ignored (the last direction is kept). After that the
game **pauses** (all timers freeze) and shows **"Face not found — game
paused"**. It resumes automatically when the face comes back.

---

## 3. Full game rules

All numbers are starting values and live as constants at the top of the code
so we can tune them by playtesting.

### 3.1 Option 1: looking down (paper)

- Always safe.
- The suspicion bar (3.2) resets / drains.
- Copy progress (3.3) resets.
- *Open question Q1:* should looking down also be where you "write" a copied
  answer? See section 9.

### 3.2 Option 2: looking at the teacher (monitor)

- The first **3 s** of looking are free (grace time).
- After that, the **suspicion bar** fills over **2 s**.
- When it is full: **warning**. A popup appears ("The teacher noticed you
  staring! Warning 1/3"), a warning sound plays, the bar resets.
- **3 warnings = game over.**
- Looking away (down or sideways) resets the stare timer.

### 3.3 Option 3: copying (left or right)

- Looking sideways fills the **copy bar**. Holding it for **2.5 s** fills one
  answer.
- While the bar fills, a **tick** sound plays repeatedly (about every 0.3 s), so
  the player knows it is working without looking at the screen. A **ding**
  plays when an answer is filled.
- After an answer is filled, the player must look away and back again to start
  the next one. This stops one long stare from filling everything.
- If the player looks away before 2.5 s, progress is **reset** (demo default;
  see Q2).
- **Caught:** if the teacher is in a watching state while the player is
  looking sideways → **game over immediately**.

### 3.4 Winning and losing

| Outcome | Condition |
|---|---|
| **Win** | All 5 answers filled. |
| **Lose — caught** | Looking sideways while the teacher is watching. |
| **Lose — warnings** | 3 warnings from staring. |
| **Lose — time** | Exam timer (for example **90 s**) runs out before all answers are filled. |

The exam timer is what forces the player to take risks. Without it, the safe
play would be to look down forever.

### 3.5 Score (optional, for a later version)

- Time left when finishing.
- Fewer warnings = bonus.
- "Close calls": copied while the teacher was turning.

---

## 4. The teacher

The teacher is a **state machine**. Each state lasts a random time in a range,
so players cannot memorise the pattern.

| State | Duration | Safe to copy? | What the player sees | What the player hears |
|---|---|---|---|---|
| `WRITING_ON_BOARD` | 4–8 s | ✅ yes | Back turned, writing | Chalk scratching |
| `TURNING` | ~1 s | ✅ yes (last chance!) | Turning around | Chalk stops |
| `WATCHING_CLASS` | 2–5 s | ❌ no | Facing the class | Silence / "Hmm." |
| `WALKING` | 3–6 s | ❌ no | Walking between desks | Footsteps |
| `DISTRACTED` (phone, reading) | 3–6 s | ✅ yes | Looking at phone | Phone buzz |

- `TURNING` is the **warning sign**: it gives a fair reaction window before
  danger. Its sound must be clear, since the player is often not looking at
  the screen.
- A small **reaction grace** (~0.3 s) after `WATCHING_CLASS` begins, before
  sideways looking counts as caught. Feels fairer and covers tracking delay.
- Difficulty can grow over the exam: shorter safe states, longer danger
  states, shorter `TURNING`.

---

## 5. Graphics, animation and sound

### 5.1 Library: pygame

We use **pygame-ce** (the community edition of pygame; used as
`import pygame`, works with Python 3.14). It gives us:

| Need | How in pygame |
|---|---|
| Game window | `pygame.display.set_mode((960, 600))` |
| Show our art | `pygame.image.load("assets/teacher.png")`, then `screen.blit(image, (x, y))` |
| Animation | Redraw the screen every frame (~30 times a second). An animation is a list of images ("frames"); every few game frames we switch to the next image. Moving = changing the `(x, y)` where we draw. |
| Sound effects | `pygame.mixer.Sound("assets/tick.wav").play()` |
| Background music | `pygame.mixer.music.load(...)`, `.play(-1)` (loops) |
| Text | `pygame.font.SysFont(None, 40).render("Warning!", True, colour)` |
| Keyboard | `pygame.event.get()` for Q/Esc/R |

OpenCV stays for the webcam; MediaPipe stays for the face. The small webcam
preview is drawn into the pygame window by converting the OpenCV frame into a
pygame image.

### 5.2 Using our own (AI-generated) art

- Put images in `assets/images/`. **PNG with transparent background** for
  characters, so they can be drawn on top of the classroom.
- **One file per animation frame**, named in order, e.g.
  `teacher_writing_0.png`, `teacher_writing_1.png`, …
  (or one "sprite sheet" image with frames side by side; we can cut it in code).
- Keep the same size and the same character position in every frame of one
  animation, otherwise the character will jump around.
- Suggested image list for the first real version:

| Image | Frames | Notes |
|---|---|---|
| `classroom_bg.png` | 1 | Whole background: board, walls, desks. 960×600. |
| `teacher_writing_*.png` | 2–4 | Back turned, arm moving. |
| `teacher_turning_*.png` | 2–3 | Half-turned. |
| `teacher_watching_*.png` | 1–2 | Facing class, maybe blinking. |
| `teacher_walking_*.png` | 4 | Walk cycle; we move it across the screen in code. |
| `teacher_phone_*.png` | 1–2 | Looking at phone. |
| `warning_popup.png` | 1 | Optional, otherwise drawn in code. |

AI art often comes out in different sizes and styles: we may need to crop,
resize and cut backgrounds out (any image editor, or GIMP / remove.bg).

### 5.3 Sound

- Put sounds in `assets/sounds/`, **`.wav` or `.ogg`** (pygame plays both).
- Free sources: freesound.org, or record our own with a phone (chalk on a
  board, footsteps, a cough).
- For the demo we can **generate** simple tones in code (tick, ding, buzz)
  with numpy, so no files are needed yet.

| Sound | When |
|---|---|
| `tick` | Repeats while the copy bar fills |
| `ding` | Answer filled |
| `buzz` | Warning |
| `chalk` (loop) | Teacher writing |
| `chalk_stop` / turn | Teacher turning, the key danger cue |
| `footsteps` (loop) | Teacher walking |
| `phone` | Teacher distracted |
| `caught` | Game over: caught |
| `bell` | Win / exam over |
| background classroom noise | Always, quiet |

---

## 6. Code structure

```
main.py            Starts everything, runs the main loop, handles screens (menu/game/end)
head_tracker.py    Webcam frame → yaw/pitch → DOWN / SCREEN / LEFT / RIGHT / None
game.py            Game rules: timers, bars, answers, warnings, win/lose. No drawing.
teacher.py         Teacher state machine: current state, timers, "is watching?"
render.py          All drawing: classroom, teacher animation, HUD, popups, webcam preview
sounds.py          Loads (or generates) sounds, plays them by name
assets/images/     Art
assets/sounds/     Sounds
tracker.py         Old body tracker, kept for reference
```

Keeping the **rules** (`game.py`) separate from the **drawing** (`render.py`)
means we can change the art without touching the rules, and test the rules
without a camera.

### 6.1 Main loop (once per frame, ~30 fps)

```
1. Handle keys / window close
2. Read webcam frame (OpenCV)
3. head_tracker → direction (or None)
4. If None:          pause, show "Face not found"
   else:             teacher.update(dt)
                     game.update(direction, teacher, dt)  → events (tick, answer, warning, caught, win…)
5. Play sounds for the events
6. render.draw(game, teacher, direction, webcam frame)
7. pygame.display.flip()
```

`dt` is the time since the last frame in seconds, so the game runs at the same
speed even if the frame rate changes.

### 6.2 Game screens (state machine)

```
MENU → CALIBRATING → PLAYING ⇄ PAUSED (face not found)
                        ↓
               WON  /  LOST (caught | warnings | time)
                        ↓
                      MENU  (R = play again, Q = quit)
```

### 6.3 Performance

- Face Landmarker + 640×480 webcam should run at 25–30 fps (body tracker
  already gets ~25).
- If the game feels laggy, move the webcam + face detection into a separate
  **thread** so drawing never waits for the camera.

---

## 7. The demo (first thing to build)

**Purpose:** prove the head tracking and the two bars work and feel right,
before any art or teacher exists.

### 7.1 What it shows

```
┌──────────────────────────────────────────────────────────────────┐
│ OPTION 3 — COPYING (LEFT)                    ┌──────────────────┐ │
│                                              │  webcam preview  │ │
│ Answers:  ■ ■ ■ □ □   3/5                    │  (mirrored)      │ │
│ Warnings: ● ○ ○       1/3                    │ yaw +31 pitch -4 │ │
│                                              └──────────────────┘ │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│ │ 1  PAPER     │  │ 2  SCREEN    │  │ 3  NEIGHBOUR │ ← highlighted│
│ └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                   │
│ Copying        [██████████░░░░░░░░░]                              │
│ Suspicion      [░░░░│░░░░░░░░░░░░░░]  (grace | fill)              │
└──────────────────────────────────────────────────────────────────┘
```

- **Big label** of the current option: 1 / 2 / 3 (and LEFT/RIGHT).
- **Three option boxes**; the active one is highlighted.
- **Copy bar** (option 3): fills over 2.5 s, **tick** sound while filling,
  **ding** when an answer is filled.
- **Suspicion bar** (option 2): after 3 s of staring it fills over 2 s; when
  full, a **warning popup** shows for 2 s with a **buzz** sound.
- **Answers** 0/5 and **warnings** 0/3 counters.
- **Webcam preview** with the yaw/pitch numbers, for tuning thresholds.
- **"Face not found — game paused"** overlay when no face is seen.
- **Calibration screen** at start: "Look at the screen" with a 2 s countdown.
- **End screens:** "All answers filled!" (win) or "Too many warnings" (lose).
- **Keys:** `Q`/`Esc` quit, `R` restart, `C` recalibrate.

### 7.2 Not in the demo

- No teacher → nobody can catch you, and no exam timer.
- No art, no real sound files (sounds generated in code).
- No neighbours.

### 7.3 Done when

- [ ] Each of the three directions is detected correctly for at least two team
      members, at the real desk/monitor setup.
- [ ] No false switches while sitting still for 30 s.
- [ ] Left and right are not swapped; down is not confused with up.
- [ ] Copy bar, tick, ding, answer count work.
- [ ] Suspicion bar, popup, buzz, warning count, game over at 3 work.
- [ ] Covering the face pauses, uncovering resumes.
- [ ] Runs at 20+ fps.

---

## 8. Build roadmap

Each step ends in something runnable, and gets a `NOTES.md` entry when
committed. **Detailed instructions for each step (for an AI agent or a person)
are in `STEPS.md`.**

| # | Step | Result |
|---|---|---|
| 1 | **Head tracker** | `head_tracker.py` + a test window printing the direction and angles. Tune thresholds. |
| 2 | **Demo** (section 7) | `main.py`, `game.py`, `render.py` (shapes + text), generated sounds. |
| 3 | **Playtest the demo** | Tune timings (copy 2.5 s? grace 3 s?). Decide Q1/Q2 below. |
| 4 | **Teacher logic** | `teacher.py` state machine, shown as text + coloured box ("WRITING — safe"). Caught rule, exam timer. Now the game is fully playable without art. |
| 5 | **Sound files** | Chalk, footsteps, turning cue, etc. Playtest: can you play by ear? |
| 6 | **Art + animation** | Classroom background, teacher animations from our images. |
| 7 | **Menus and polish** | Start menu, calibration screen, win/lose screens, restart. |
| 8 | **Difficulty + score** | Teacher gets harder over time, final score. |
| 9 | **Final testing + README** | Test on other computers/webcams, update README and NOTES. |

---

## 9. Open questions (decide after playtesting the demo)

- **Q1 — How is an answer filled?**
  - (a) *Simple:* look sideways 2.5 s → answer filled. **(demo default)**
  - (b) *Memorise then write:* look sideways to "read" an answer, then look
    down ~1.5 s to "write" it. If caught before writing, it is lost. Gives
    option 1 a real purpose.
- **Q2 — Interrupted copying:** does progress **reset** (strict; demo default)
  or **pause** (allows several short peeks)?
- **Q3 — Number of warnings:** 3 or 2 before game over?
- **Q4 — Exam time limit:** 90 s? 120 s?
- **Q5 — Does staring count while the teacher is writing (back turned)?**
  Realistically the teacher cannot see you staring then.

---

## 10. Future ideas

- **Neighbours with different answers.** Left = good student (correct
  answers), right = bad student (wrong answers). Wrong answers lower the
  final grade. The player has to figure out whom to copy.
- **Neighbour covers their paper** sometimes, so copying from that side does not
  work for a while.
- **Neighbour reacts:** looking at them too long makes them notice and raise
  their hand.
- **Multiple question types:** longer questions need more copying time.
- **Teacher gets suspicious over time:** each warning makes the teacher check
  more often.
- **Eraser / pencil sounds** when writing answers (pairs with Q1-b).
- **Levels:** different teachers (strict, sleepy, wandering) or rooms.
- **Hand gestures** (we already have the body tracker): e.g. raise hand to
  "ask a question" and distract the teacher once per game.
- **Eye tracking** (iris landmarks from the Face Landmarker) instead of whole
  head turning: harder mode, glance with the eyes only.
- **High-score table** saved to a file.
- **Two-player mode:** one player cheats, the other controls the teacher with
  the keyboard.
- **Settings screen:** sensitivity (thresholds), sound volume, difficulty.

---

## 11. Libraries

| Library | Use |
|---|---|
| `opencv-contrib-python` | Webcam |
| `mediapipe` | Face Landmarker (head angles) |
| `pygame-ce` | Window, drawing, images, animation, sound, keyboard |
| `numpy` | Comes with MediaPipe; used for generating demo sounds |

`pygame-ce` is installed in `.venv` but **not yet in `requirements.txt`**;
add it when the demo is committed.
