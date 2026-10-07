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
| 1 | Look at the exam paper | **Down** | Safe; see your paper and write A..E. The teacher is hidden and silent. |
| 2 | Look at the teacher | **Straight at the monitor** | See the classroom; your paper is hidden. Staring at a watching teacher is suspicious. |
| 3 | Read a neighbour's paper | **Left or right** | See only the current question, gradually clearing from blur. Being seen is dangerous; keys cannot write here. |

**Goal:** answer all 5 questions correctly in 90 seconds without getting
caught and without collecting 3 warnings.

### Why it is fun: the information problem

The player can only see the classroom while looking at the monitor. While
reading a neighbour's paper they cannot see the teacher, and while looking
down at their own paper they cannot see **or hear** the teacher. That creates the core loop:

1. Glance at the monitor to check the teacher.
2. When the teacher is busy, look sideways, let the current question become
   sharp, and remember its marked A..E option.
3. Listen while copying: Luigi's "hmm" means the teacher is about to look up.
4. Look away from the neighbour before the teacher sees you.
5. Return to your own paper (DOWN or SCREEN), answer with A..E, and use
   Up / Down to revisit a question. Do not stare at a watching teacher.

The exam clock forces the player to take risks: without it, the safe play
would be to look at the paper forever.

---

## 2. Controls: head tracking (`head_tracker.py`)

Each webcam frame becomes one of:

| Result | Meaning |
|---|---|
| `DOWN` | Head tilted down more than `PITCH_DOWN_THRESHOLD` (23°) |
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

- Always safe; the suspicion bar drains. Your full exam paper is visible.
- A..E marks the selected question; Up / Down changes the selection.
- No sound from the teacher at all.

### 3.2 Looking at the screen (teacher)

- The classroom fades in over `FADE_TIME` (0.15 s). The own-paper overlay is
  hidden. Existing A..E input still works; look down to inspect your paper.
- While the teacher looks at the class, the **suspicion bar** fills: full
  after 3 s (`STARE_GRACE_TIME` 2 s shown yellow, then `STARE_FILL_TIME` 1 s
  red). Full = **warning** (popup + buzz) and the bar starts over.
- While the teacher is busy, staring is free (`STARE_ONLY_WHEN_FACING`).
- **3 warnings = game over.**

### 3.3 Looking sideways (copying)

- Show just the selected question on the left or right neighbour's paper:
  initially Q1, then the next blank question after writing. Both neighbours
  use the same answer key, generated once per exam.
- The paper starts blurred and becomes sharp over `PAPER_FOCUS_TIME` (2.5 s).
  The focus clock belongs to one continuous sideways look. Looking away,
  switching neighbours, changing questions, recalibrating or losing camera/face
  tracking resets it. Focusing never automatically writes a mark.
- Sideways looks never mark your paper. Return to DOWN or SCREEN and type the
  remembered choice; writing automatically advances to the next blank row.
- **Seen copying** (the teacher is watching): an alarm plays, the suspicion
  bar fills fast (full in `CAUGHT_TIME`, 0.7 s). Look away before it is full
  and you escape; full = **caught**.
- Up / Down can revisit answers on your own paper. A full but incorrect paper
  remains playable; a hint asks you to review it. All correct answers win.

### 3.4 The suspicion bar

One bar for both staring and being seen copying, so staring after being seen
carries on from there. It never jumps back to empty, because that would tell
the player when the teacher looked away: it drains slowly
(`SUSPICION_DRAIN_TIME`, 10 s for a full bar) while nothing suspicious happens.

### 3.5 Winning and losing

| Outcome | Condition | Sound |
|---|---|---|
| **Win** | 5 manually entered correct answers | rising notes |
| **Lose: caught** | suspicion bar full while seen copying | MGS alert |
| **Lose: warnings** | 3 warnings | MGS alert |
| **Lose: time** | `EXAM_TIME` (90 s) runs out | falling notes |

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
  clock, webcam preview, keyboard instructions and suspicion bar. Papers
  and the desk are drawn directly using pygame, without extra image files.
- **Pictures** were made with Gemini and sharpened with Real-ESRGAN (an AI
  upscaler, run once by hand, not part of the game). Originals are in
  `assets/images/original/`. A new picture must show the same classroom from
  the same angle, so that swapping pictures only changes the teacher.
- **Sounds** (`sounds.py`): most are beeps generated in code; `SOUND_FILES`
  replaces some with files from `assets/sounds/`:

| Event | Sound |
|---|---|
| `state:TURNING` | `luigi-hmm.mp3` |
| `lost_caught`, `lost_warnings` | `mgs-alert-sound.mp3` |
| `tick`, `answer`, `warning`, `spotted`, `won`, `lost_time` | generated beeps |

`Erasing Chalk On Chalkboard Sound Effect.mp3` is in the folder but not used
yet (see section 8).

---

## 6. Code structure

```
main.py            Main loop and screens (start, calibrating, game, end)
camera.py          Reads/retries/reconnects the webcam in a background thread
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

- **Q1 — How is an answer filled?** ✅ Read the marked neighbour paper, then
  return to your own paper (DOWN or SCREEN) and write with A..E.
- **Q2 — Interrupted answering:** ✅ Written marks are **kept**. Up / Down
  revisits any question. Reading a neighbour never writes automatically.
- **Q3 — Number of warnings:** 3 (could be 2).
- **Q4 — Exam time:** ✅ 90 s for now; tune by playtesting.
- **Q5 — Does staring count while the teacher is busy?** ✅ No.

---

## 8. Done and next

**Done:** head tracking with calibration; copying and staring rules; the
teacher with four pictures; exam clock; own paper visible only when looking down;
one current question on neighbour papers with gradual blur; camera recovery;
A..E input and question navigation;
correct-answer checking; real sounds for turning and game over; one suspicion
bar that drains slowly; tests (104). F2 recalibrates; F3 shows teacher state.

**Next, roughly in order:**

1. **Playtest and tune** the numbers in `settings.py` with the whole team
   (teacher durations, `EXAM_TIME`, `CAUGHT_TIME`). Test with
   other webcams, lighting, glasses.
2. **More sounds:** the chalk sound as a loop while the teacher erases the
   board (needs `loop()`/`stop()` in `sounds.py`), quiet classroom background,
   real tick/ding files. The game must keep working without them.
3. **More art:** polish the drawn desk/papers, add a turning picture and
   a walking teacher so moving between board and desk is not a jump.
4. **Menus and polish:** main menu, how-to-play screen, end screen with
   answers/time/warnings, readable webcam errors.
5. **Difficulty and score:** the teacher checks more often as the exam goes
   on; Easy/Normal/Hard; score from time left, warnings and close calls; a
   high-score file.
6. **Final testing and README:** fresh `git clone` on another computer,
   screenshot, credits and licences for art and sounds.

---

## 9. Future ideas

- **Neighbours with different answers:** left = good student, right = bad
  student; wrong answers lower the grade.
- **Neighbour covers their paper** sometimes, or notices you and raises a hand.
- **Teacher gets suspicious over time:** each warning makes them check more.
- **Levels:** different teachers (strict, sleepy, wandering) or rooms.
- **Eye tracking** (iris landmarks) instead of turning the head: harder mode.
- **Hand gestures:** raise a hand to distract the teacher once per game.
- **Two-player mode:** one cheats, the other controls the teacher.
- **Settings screen:** sensitivity, volume, difficulty.

---

## 10. Libraries

| Library | Use |
|---|---|
| `opencv-contrib-python` | Webcam |
| `mediapipe` | Face Landmarker (head angles) |
| `pygame-ce` | Window, drawing, pictures, sound, keyboard |
| `numpy` | Comes with MediaPipe; used to generate beeps |
