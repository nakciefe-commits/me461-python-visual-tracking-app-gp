# Game Plan — "Don't Get Caught"

ME461 group project by **Glitch Please**. A webcam game written only in Python
and its libraries, controlled by where the player turns their head.

This file is the **design** (how the game works and why) and the **to-do
list** (section 8). What changed in each commit, and why, is in `NOTES.md`.
All numbers below are the current values in `settings.py`; change them there.

---

## 1. The idea

The player is a student sitting an exam. The monitor shows the classroom from
the student's seat: the teacher, the board, the other desks. The webcam watches
the player's head. The player can do three things:

| # | Action | Head direction | Why do it |
|---|---|---|---|
| 1 | Look at the exam paper | **Down** | Safe, and the only place to write an answer (keys A-D), but you see and hear nothing. |
| 2 | Look at the teacher | **Straight at the monitor** | The only way to *see* what the teacher is doing, but staring while they look at the class is suspicious. |
| 3 | Copy from a neighbour | **Left or right** | The only way to read answers, but if the teacher sees it, you get caught. |

**Goal:** write all 5 answers before the exam time runs out, without getting
caught and without collecting 3 warnings. Each answer is A, B, C or D, and
only one neighbour knows it; the other one's paper shows "?". At the end the
exam is graded (e.g. 4/5 correct).

### Why it is fun: the information problem

The player can only see the classroom while looking at the monitor. While
copying they are blind to the teacher, and while looking at the paper they are
blind **and deaf**. That creates the core loop:

1. Glance at the monitor to check the teacher.
2. When the teacher is busy, look sideways and copy. If the paper shows "?",
   the answer is on the other side.
3. Listen while copying: Luigi's "hmm" means the teacher is about to look up.
4. Look away from the neighbour before the teacher sees you.
5. Look down at your paper and write the letter you remember (A-D).
6. Do not stare at the teacher while they look at the class, or you get a
   warning.

The exam clock forces the player to take risks: without it, the safe play
would be to look at the paper forever.

---

## 2. Controls: head tracking (`head_tracker.py`)

Each webcam frame becomes one of:

| Result | Meaning |
|---|---|
| `DOWN` | Head tilted down more than `PITCH_DOWN_THRESHOLD` (28°) |
| `LEFT` / `RIGHT` | Head turned more than `YAW_THRESHOLD` (18°) |
| `SCREEN` | Otherwise |
| `None` | No face for more than `FACE_LOST_GRACE` (0.6 s): the game pauses |

- **MediaPipe Face Landmarker** (`face_landmarker.task`) gives a rotation
  matrix for the face; from it we compute **yaw** (left/right) and **pitch**
  (up/down).
- **Calibration** at the start: the player looks at the screen for 2 s and the
  average angles become their *neutral*. All thresholds are measured from it,
  so it works wherever the webcam sits.
- **Smoothing** (`SMOOTHING` 0.8) stops one noisy frame from jumping the angle.
- **Hold time** (`HOLD_TIME` 0.1 s): a new direction must last this long, so
  jitter does not create fake glances. Lower = faster reaction, more jitter.
- **Face lost while looking down** counts as `DOWN`: the camera only sees the
  top of the head then.
- **Sign switches** `YAW_SIGN`, `PITCH_SIGN`: flip to `-1` if directions come
  out swapped.

---

## 3. Game rules (`game.py`)

### 3.1 Looking down (paper)

- Always safe. Nothing fills; the suspicion bar drains.
- The screen shows your own paper (`classroom_desk_looking_down`) with the
  letters written so far on the answer lines.
- **Writing:** press A, B, C or D to write the current answer. It only works
  while looking down, and only after the answer has been read from the
  neighbour who knows it. Any letter is accepted (you have to remember what
  you read); wrong ones only show in the grade at the end. Then the next
  question starts.
- No sound from the teacher at all.

### 3.2 Looking at the screen (teacher)

- The classroom fades in from black over `FADE_TIME` (0.15 s).
- While the teacher looks at the class, the **suspicion bar** fills: full
  after 5 s (`STARE_GRACE_TIME` 3 s shown yellow, then `STARE_FILL_TIME` 2 s
  red). Full = **warning** (buzz) and the bar starts over.
- **The warning scene** (`WARNING_SCENE_TIME`, 2.5 s): the teacher walks
  up to your desk (a zoom into their picture, `TEACHER_APPROACH_TIME`
  0.8 s) and points at you angrily (`classroom_warning.jpeg`), the screen
  shakes and flashes red, "WARNING 1/3" and "STOP STARING AT ME!". The game
  is frozen meanwhile, so you are not punished while you cannot see.
- While the teacher is busy, staring is free (`STARE_ONLY_WHEN_FACING`).
- **3 warnings = game over.**

### 3.3 Looking sideways (copying)

- The screen shows the neighbour's paper (`classroom_desk_looking_left` /
  `_right`), never the teacher.
- Each question has a random right letter (A-D) and a random neighbour who
  knows it.
- The **copy bar** fills; after `COPY_TIME` (5 s) you have **read** that
  neighbour's paper (tick sound while filling, ding when done): the picture
  changes to show the letter circled on their paper, or "?" if they don't
  know it. Each neighbour
  has their own progress, kept when looking away, so a paper can be read in
  pieces. A paper already read gives nothing more for this question.
- **Seen copying** (the teacher is watching): an alarm plays, the suspicion
  bar fills fast (full in `CAUGHT_TIME`, 0.9 s), and copying does not move
  forward. Look away before it is full and you escape; full = **caught**.

### 3.4 The suspicion bar

One bar for both staring and being seen copying, so staring after being seen
carries on from there. It never jumps back to empty, because that would tell
the player when the teacher looked away: it drains slowly
(`SUSPICION_DRAIN_TIME`, 8 s for a full bar) while nothing suspicious happens.

### 3.5 Winning and losing

| Outcome | Condition | Sound |
|---|---|---|
| **Win** (exam handed in) | 5 answers written; the end screen shows how many are right | rising notes |
| **Lose: caught** | suspicion bar full while seen copying | MGS alert |
| **Lose: warnings** | 3 warnings | MGS alert |
| **Lose: time** | `EXAM_TIME` (60 s) runs out | falling notes |

---

## 4. The teacher (`teacher.py`)

A state machine with three states at two places:

```
BUSY  ──►  TURNING  ──►  WATCHING  ──►  BUSY ...
safe       "hmm" sound   copying = caught
3.5–6.5 s  0.2 s         4–7 s
```

- **Places:** `BOARD` (erasing the board) and `DESK` (on the phone). After
  watching, the teacher moves to the other place with chance `MOVE_CHANCE`
  (40%).
- **Pictures:** place + state choose one of four classroom pictures
  (`classroom_<board|desk>_<busy|watching>.jpeg`). `TURNING` shows the busy
  picture: the warning is the sound.
- **`CAUGHT_GRACE`** (0.1 s): the first moment of `WATCHING` does not count, to
  cover the head tracker's delay.
- **Sounds the player hears:** only the turning "hmm", and only when not
  looking at the paper. Looking up while the teacher is still turning plays it
  late (once per turn). No sound when the teacher goes back to being busy:
  you have to look.
- Durations are random in a range (`TEACHER_DURATIONS`) so the pattern cannot
  be memorised.

---

## 5. Graphics and sound

- **pygame-ce** draws everything (`render.py`): the classroom picture fills
  the 960×600 window, with see-through strips for answers, warnings, the exam
  clock, the webcam preview and the two bars.
- **Pictures** were made with Gemini and sharpened with Real-ESRGAN (an AI
  upscaler, run once by hand, not part of the game). Originals are in
  `assets/images/original/`. A new picture must show the same classroom from
  the same angle, so that swapping pictures only changes the teacher.
- **Look-away pictures** (`classroom_desk_looking_down/left/right`, asked for
  by the instructor): what the player sees while looking down or sideways.
  Made by giving Gemini `original/classroom_board_busy.jpeg` and asking for
  the same style, room and students from the same seat, turned down/left/
  right. They never show the teacher, so the information problem stays. The
  important part (the neighbour's paper) must be in the middle of the
  picture, because the game cuts off the top (`CLASSROOM_TOP`).
- **Paper pictures** (`left_A` … `left_D`, `left_unknown`, same for `right_`):
  the same look-left/right picture, edited by Gemini so the neighbour's exam
  sheet has the letter (or "?") circled on it. Shown only once the copy bar
  is full; before that the plain picture, so nothing gives the answer away.
- **The whole interface is neon 80s**, like the game Hotline Miami: in the
  game, dark purple see-through strips with a pink edge, slanted bars,
  slanted bold text with shadows, a clock that thumps every second when
  time runs out, and a wobbling neon banner for warnings. Before each game a
  short "chapter" screen ("ME461 - Chapter 1: The Quiz", the date, a
  funny loading line, a bar that fills unevenly like a real one, with a
  percentage) so the game does not start all at once.
- **Opening:** the "Glitch Please" intro (`glitch_intro.py`): the team name
  glitching in with red/cyan split and jumping slices, the "GP" mark,
  "presents". Meant for all our projects, like a studio logo. Then the
  disclaimer as an official notice on a wooden desk: typed out, signed with
  Space, and stamped "APPROVED" (a different world from the neon menus, on
  purpose).
- **Menus** (`render.py`, `draw_menu`), made entirely in code: a pulsing pink/blue/orange gradient,
  turning light rays, scanlines, slanted text with pink and cyan "ghost"
  copies, a title that rocks and thumps on a beat. Head control: tilt up/down
  to move, turn right (hold) to choose, turn left (hold) to go back. This
  needs calibration first, so the main menu comes after the start screen.
- **Pointing picture** (`classroom_warning.jpeg`): the teacher
  a couple of metres in front of your desk, pointing their index finger at
  you. Made by Gemini from the two "watching" originals; the face and the
  finger must be in the middle of the picture (the game cuts off the top).
  It is cut less at the top than the others (`POINTING_TOP`). Without it,
  the warning scene only zooms in. The first try came out too
  close and with a cap instead of his bandana, so the prompt says the
  distance and the bandana explicitly. The prompt (with
  `original/classroom_board_watching.jpeg` and
  `original/classroom_desk_watching.jpeg` attached):

  > Using the two attached classroom pictures, draw the same classroom in
  > exactly the same art style, seen from the same student's seat
  > (first-person view, eye level of a seated student). The same teacher as
  > in the pictures: long grey hair, grey beard, an olive-green camouflage
  > bandana tied tightly over the top of his head (a bandana, NOT a cap or
  > hat, no brim), black T-shirt, jeans. He has walked down the aisle and stands about two metres
  > in front of my desk, facing me, visible from the head down to the
  > knees, with some classroom around him. He is angry: frowning eyebrows,
  > narrow eyes, mouth open as if scolding me. His arm is stretched out and
  > he points his index finger straight at me (at the viewer), the other
  > fingers closed in a fist. His face and his pointing hand are in the
  > middle of the picture; nothing important in the top quarter or the
  > bottom tenth. The front edge of my desk with my exam paper is at the
  > bottom. Square picture, no added text.
- **Caught scene** (`CAUGHT_SCENE_TIME`, 4 s): the teacher frozen with a
  red Metal Gear "!" over his head (with the MGS alert sound), then a white
  flash, a paper-ripping sound and `classroom_caught.jpeg`: the teacher
  tearing up your exam. "CAUGHT COPYING!" / "YOUR EXAM: 0/5 - SEE YOU NEXT
  SEMESTER". The picture is still to be made with Gemini; until then the
  scene stays on the "!". Prompt (attach the two "watching" originals and
  `classroom_warning.jpeg`):

  > Using the attached classroom pictures, draw the same classroom in
  > exactly the same art style, seen from the same student's seat
  > (first-person view, eye level of a seated student). The same teacher as
  > in the pictures: long grey hair, grey beard, an olive-green camouflage
  > bandana tied tightly over the top of his head (a bandana, NOT a cap or
  > hat, no brim), black T-shirt, jeans. He stands right in front of my
  > desk, about one and a half metres away, visible from the head down to
  > the waist. He holds my exam paper (the sheet that says "ME461
  > MECHATRONIC COMPON. AND INSTRUMENT - JAZZ QUIZ") up in front of his
  > chest with both hands and is tearing it in half down the middle, with
  > an angry but satisfied grin. Small pieces of paper fly around. The
  > other students turn around and stare, shocked; one covers their mouth,
  > one is laughing. His face and the torn paper are in the middle of the
  > picture; nothing important in the top quarter or the bottom tenth. My
  > empty desk is at the bottom. Square picture, no added text.
- **Game over screen** (`GAME_OVER_TIME`, 8 s, Space skips): after every
  loss, black with "GAME OVER"; the Gemini and Claude logos, drawn in code
  with cartoon faces, make fun of you in a two-line chat that depends on how
  you lost. The team wanted the two AIs that made the game (Gemini the
  pictures, Claude the code) to laugh at the cheater. A "nooo" sound plays
  (`noooo.mp3` if the team adds it, else a sound made in code).
- **Sounds** (`sounds.py`): most are beeps generated in code; `SOUND_FILES`
  replaces some with files from `assets/sounds/`:

| Event | Sound |
|---|---|
| `state:TURNING` | `luigi-hmm.mp3` |
| `lost_caught`, `lost_warnings` | `mgs-alert-sound.mp3` |
| `tick`, `read` (ding), `write` (pencil scratch), `warning`, `spotted`, `won`, `lost_time` | generated beeps |

`Erasing Chalk On Chalkboard Sound Effect.mp3` is in the folder but not used
yet (see section 8).

---

## 6. Code structure

```
main.py            Main loop and screens (notice, start, calibrating, menus, game, end)
menu.py            Menus: selected item; head tilt/turn → up/down/select/back; loading bar
disclaimer.py      The opening notice: typed, signed, stamped
glitch_intro.py    Our team's intro (self-contained, for every project)
camera.py          Reads the webcam in a background thread
head_tracker.py    Webcam frame → yaw/pitch → DOWN / SCREEN / LEFT / RIGHT / None
teacher.py         Teacher state machine; which sounds the player hears
game.py            Rules: bars, answers, warnings, clock, win/lose. No drawing.
render.py          All drawing
sounds.py          Generated beeps + sound files, played by name
settings.py        Every tuning number
tests/             unittest tests for the rules and the tracker logic
tracker.py         Old body tracker, kept for reference
```

Each frame: read the webcam → head direction → `teacher.update(dt)` and
`game.update(direction, dt, teacher)` return **events** (`"tick"`,
`"spotted"`, `"state:TURNING"`, …) → play a sound for each → draw. `dt` (time
since the last frame) keeps the speed the same at any frame rate.

---

## 7. Open questions

- **Q1 — How is an answer filled?** ✅ decided: look sideways to read the
  letter (or "?"), then look down and press A-D to write it. Wrong letters
  only lower the grade.
- **Q2 — Interrupted copying:** ✅ decided: progress is **kept**.
- **Q3 — Number of warnings:** 3 (could be 2).
- **Q4 — Exam time:** ✅ 60 s for now; tune by playtesting.
- **Q5 — Does staring count while the teacher is busy?** ✅ No.

---

## 8. Done and next

**Done:** head tracking with calibration; copying and staring rules; the
teacher with four pictures; exam clock; the classroom hidden while looking away;
real sounds for turning and game over; one suspicion bar that drains slowly;
pictures for looking down, left and right; A-D answers read from one
neighbour and written on your paper, graded at the end; neon main menu,
how-to-play, settings and end menus controlled by the head (the keyboard
pauses the head for 1 s); warning, caught and game over scenes; the Glitch
Please intro; the official notice; tests (100).

**Next, roughly in order:**

1. **Playtest and tune** the numbers in `settings.py` with the whole team
   (teacher durations, `COPY_TIME`, `EXAM_TIME`, `CAUGHT_TIME`). Test with
   other webcams, lighting, glasses.
2. **More sounds:** the chalk sound as a loop while the teacher erases the
   board (needs `loop()`/`stop()` in `sounds.py`), quiet classroom background,
   real tick/ding files. The game must keep working without them.
3. **More art:** a turning picture; a walking teacher so moving between board
   and desk is not a jump.
4. **Menus and polish:** ✅ main menu, how-to-play screen, settings, end
   menu, all head-controlled (commit #15). Still: end screen with
   time/warnings, readable webcam errors, menu music.
5. **Difficulty and score:** the teacher checks more often as the exam goes
   on; Easy/Normal/Hard; score from time left, warnings and close calls; a
   high-score file.
6. **Final testing and README:** fresh `git clone` on another computer,
   screenshot, credits and licences for art and sounds.

---

## 9. Future ideas

- **A funny sound for wrong answers** on the end screen (the team will add a
  sound file).
- **Pass mark:** e.g. at least 3/5 correct to count as a win.
- **Neighbour covers their paper** sometimes, or notices you and raises a hand.
- **Teacher gets suspicious over time:** each warning makes them check more.
- **Levels:** different teachers (strict, sleepy, wandering) or rooms.
- **Eye tracking** (iris landmarks) instead of turning the head: harder mode.
- **Hand gestures:** raise a hand to distract the teacher once per game.
- **Two-player mode:** one cheats, the other controls the teacher.
- **More settings:** sensitivity, volume, difficulty (the settings menu
  has exam time, sound on/off, fullscreen and recalibrate).

---

## 10. Libraries

| Library | Use |
|---|---|
| `opencv-contrib-python` | Webcam |
| `mediapipe` | Face Landmarker (head angles) |
| `pygame-ce` | Window, drawing, pictures, sound, keyboard |
| `numpy` | Comes with MediaPipe; used to generate beeps |
