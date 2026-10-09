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
| 1 | Look at the exam paper | **Down** | Safe, and the only place to write an answer (keys A-D, S = blank), but you see and hear nothing. |
| 2 | Look at the teacher | **Straight at the monitor** | The only way to *see* what the teacher is doing, but staring while they look at the class is suspicious. |
| 3 | Copy from a neighbour | **Left or right** | The only way to read answers, but if the teacher sees it, you get caught. |

**Goal:** a run is three exams (the Quiz, the Midterm, the Final; section
11). In each, answer every question without getting caught and without
collecting 3 warnings. Each answer is A, B, C or D, and only one neighbour
knows it; the other one's paper shows "?". You may also guess, or leave a
question blank. Each question is worth one point: right +1, wrong −0.5,
blank 0. When the clock runs out the paper is collected as it is.

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
- **Calibration** at the start (section 12.1): the player shows four poses
  (screen, left, right, down), pressing Space for each. The screen pose
  becomes their *neutral*; all angles are measured from it, so it works
  wherever the webcam sits. The other three set this player's own
  thresholds (60 % of the way to each pose).
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
- **Writing:** press A, B, C or D to write the current answer, or S to leave
  it blank. It only works while looking down. Any letter is accepted, read
  or not: an unread letter is a guess (right +1, wrong −0.5, blank 0), so
  copying is the safe way to points and guessing a gamble. Then the next
  question starts.
- No sound from the teacher at all.

### 3.2 Looking at the screen (teacher)

- The classroom fades in from black over `FADE_TIME` (0.15 s).
- While the teacher looks at the class, the **suspicion bar** fills: full
  after 3 s (`STARE_GRACE_TIME` 2 s shown yellow, then `STARE_FILL_TIME` 1 s
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
  knows it; never the same letter twice in a row or more than twice per
  exam, never the same neighbour three times in a row (NOTES #43).
- **Gradual focus** (Emre's idea): the neighbour's paper (the picture with
  the letter circled, or "?") is blurry and gets sharper the longer you keep
  looking; after `PAPER_FOCUS_TIME` (2.5 s) without looking away you have
  **read** it (ding). Every look starts blurry again, so reading means
  holding a risky look; the blur itself shows how far (no bar). This replaced the old
  copy bar (5 s, kept between looks), where copying was just waiting.
- **Seen copying** (the teacher is watching): an alarm plays, the suspicion
  bar fills fast (full in `CAUGHT_TIME`, 0.7 s), and copying does not move
  forward. Look away before it is full and you escape; full = **caught**.

### 3.4 The suspicion bar

One bar for both staring and being seen copying, so staring after being seen
carries on from there. It never jumps back to empty, because that would tell
the player when the teacher looked away: it drains slowly
(`SUSPICION_DRAIN_TIME`, 8 s for a full bar) while nothing suspicious happens.

### 3.5 Winning and losing

| Outcome | Condition | Sound |
|---|---|---|
| **Handed in** (graded) | every question answered or left blank | rising notes |
| **Collected** (graded) | the exam's time runs out: the rest count as blank | falling notes |
| **Failed: caught** (0 points) | suspicion bar full while seen copying | MGS alert |
| **Failed: warnings** (0 points) | 3 warnings | MGS alert |

A graded exam's score is counted up part by part on the end screen, like
in Balatro: each question (+1000 / −500 / 0), the early hand-in bonus (up to
+1000, the share of the time left), close calls (100–500, more the fuller
the suspicion bar was when you got away, +300 above 80 %) and −300 per
warning. A failed exam goes to the game over chat and scores 0.

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
  clock and the two bars. The webcam picture is only on the start
  screen (calibration), not in the menus or the game (NOTES #47).
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
  sheet has the letter (or "?") circled on it. Shown from the start of a
  look, but blurred until the focus is full, so it cannot be read early.
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
- **Mugshot** (`MUGSHOT_SCENE_TIME`, 5.5 s, Space skips, NOTES #61): after
  every loss, before game over. Black and silent; the exam paper (torn in
  half, taped back together) fades in with the webcam photo taken the
  moment you lost, cropped to your face, clipped on it; after
  `MUGSHOT_WRITE_DELAY` the teacher writes "GOT CAUGHT!" over it in red
  marker (a marker sound made in code, or `marker.mp3`). Pictures `torn`
  and `got_caught` (IMAGE_PROMPTS.md); the photo goes where the picture is
  pure green. The photo is only kept in memory.
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
| `read` (ding), `write` (pencil scratch), `warning`, `spotted`, `won`, `time_up`, `tally0`… (the score count, a semitone higher each), `tally_done`, `new_top` (fanfare) | generated beeps |

`Erasing Chalk On Chalkboard Sound Effect.mp3` is in the folder but not used
yet (see section 8).

---

## 6. Code structure

```
main.py              Main loop and screens (notice, start, calibrating, menus, game, results)
settings.py          Every tuning number, also the exams (QUIZZES) and the moods (MOODS)
logic/               The rules, no drawing, no camera, all tested
  game.py            One exam: clock, warnings, caught, scenes, score
  exam_paper.py      Answer key, what you wrote, the grade (+1 / -0.5 / 0)
  neighbours.py      Reading a neighbour's paper (gradual focus)
  suspicion.py       The suspicion bar and close calls
  run.py             Three exams in a row, their moods, the total
  teacher.py         Teacher state machine and mood; which sounds the player hears
  tally.py           The score count, one part at a time
  highscore.py       The top scores file
  menu.py            Menus: selected item; head tilt/turn -> up/down/select/back; loading bar
  disclaimer.py      The opening notice: typed, signed, stamped
  guide.py           How to play: Gemini and Claude's lines, the tasks to try
  verdict.py         The grade roast after the final (lines per letter, the AA/BA/BB show)
  character.py       The characters' rules (from CHARACTERS), glasses' blur, the energy drink
tracking/
  camera.py          Reads the webcam in a background thread
  head_tracker.py    Webcam frame -> yaw/pitch -> DOWN / SCREEN / LEFT / RIGHT / None
ui/
  render.py          The Renderer: fonts and pictures; drawing in the files below
  style.py           Colours, fonts, the neon helpers
  draw_game.py, draw_scenes.py, draw_results.py, draw_menus.py, draw_notice.py, draw_guide.py,
  draw_characters.py
  sounds.py          Generated beeps + sound files, played by name
  glitch_intro.py    Our team's intro (self-contained, for every project)
tests/               unittest tests for logic/ and the tracker logic
old/tracker.py       Old body tracker, kept for reference
```

Each frame: read the webcam → head direction → `teacher.update(dt)` and
`game.update(direction, dt, teacher)` return **events** (`"read"`,
`"spotted"`, `"state:TURNING"`, …) → play a sound for each → draw. `dt` (time
since the last frame) keeps the speed the same at any frame rate.

---

## 7. Open questions

- **Q1 — How is an answer filled?** ✅ decided: look sideways to read the
  letter (or "?"), then look down and press A-D to write it. Guessing
  without reading is allowed too; S leaves it blank (right +1, wrong −0.5,
  blank 0).
- **Q2 — Interrupted copying:** ✅ decided: progress is **kept**.
- **Q3 — Number of warnings:** 3 (could be 2).
- **Q4 — Exam time:** ✅ fixed per exam of the run (150 / 130 / 120 s); when
  it runs out the paper is collected and graded.
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
Please intro; the official notice; gradual focus instead of the copy bar;
score, close calls and a best score; camera reconnecting; guessing and
leaving blank (+1 / −0.5 / 0), time up collects the paper; the score counted
up like Balatro; the code split into `logic/`, `tracking/`, `ui/`; the
three-exam run with moods as numbers and the gossip line (11.8 phase A);
early bonus and close calls growing with the suspicion; top 5 scores on the
main menu and the results; tests (152).

**Next, roughly in order:**

00. **Update 2** (section 12) ✅ built (NOTES #40–#45): calibration with
    four poses, the score table, a practice exam, answers without streaks,
    the slot-machine score, characters. Next: play it with the webcam and
    tune `CALIBRATION_SHARE` and `CHARACTERS` (section 12.4).

0. **The next big update: three quizzes and the teacher's moods.** Phase A
   is done; next is phase B, the real moods (section 11.8). It changes
   items 1, 2 and 5 below.

1. **Playtest and tune** the numbers in `settings.py` with the whole team
   (teacher durations, `PAPER_FOCUS_TIME`, `EXAM_TIME`, `CAUGHT_TIME`). Test with
   other webcams, lighting, glasses.
2. **More sounds:** the chalk sound as a loop while the teacher erases the
   board (needs `loop()`/`stop()` in `sounds.py`), quiet classroom background,
   real tick/ding files. The game must keep working without them.
3. **More art:** a turning picture; a walking teacher so moving between board
   and desk is not a jump.
4. **Menus and polish:** ✅ main menu, how-to-play screen, settings, end
   menu, all head-controlled (commit #15). ✅ How to play is a hands-on
   guide where Gemini and Claude teach the game (NOTES #34), followed by a
  2-question practice exam (NOTES #42). Still: end screen with
   time/warnings, readable webcam errors, menu music.
5. **Difficulty and score:** ✅ score, top scores, levels (Quiz → Midterm →
   Final) with moods. Still: the teacher checks more often as the exam goes
   on (phase B); Easy/Normal/Hard; letter grades (11.6.5).
5b. **Showing how it works:** ✅ the debug panel (F3, NOTES #62): the
   tracking pipeline step by step, for the presentation.
6. **Final testing and README:** fresh `git clone` on another computer,
   screenshot, credits and licences for art and sounds. Try `run.bat` on a
   real Windows computer (written on Linux, not yet run on Windows).

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
  has sound on/off, fullscreen and recalibrate).
- **Background music:** ✅ `theme.mp3` (made by the team with Suno) loops:
  normal in the menus (NOTES #28). ✅ A tenser track for the exam,
  `thrilling.mp3`, quieter than the theme (NOTES #33). All three tracks are
  Suno-made from samples; README "Music" lists them (NOTES #64).

---

## 10. Libraries

| Library | Use |
|---|---|
| `opencv-contrib-python` | Webcam |
| `mediapipe` | Face Landmarker (head angles) |
| `pygame-ce` | Window, drawing, pictures, sound, keyboard |
| `numpy` | Comes with MediaPipe; used to generate beeps |

---

## 11. The next update: three quizzes and the teacher's moods (draft)

Being written together by the team. **Decided** = agreed; **proposed** = a
suggestion waiting for a yes; the last part collects the team's new ideas.

### 11.1 Why

After playing, the team found two basic problems:

- **The teacher is not random enough.** Always busy → "hmm" → watching →
  busy, with durations in narrow, even ranges (busy 3.5–6.5 s, watching
  4–7 s) and the same 0.2 s warning every time. After a few turns the
  player feels the rhythm ("5 s passed, he turns now"). No surprises, no
  bluffs, one way of behaving for the whole game.
- **Nothing to come back for.** One short exam, always the same.

Not the fix: a fully random teacher. Three surprise looks in a row and the
player is caught without a chance, which is unfair, not fun. The aim is
**controlled randomness**: the player cannot predict the teacher, but an
attentive player can always notice a sign.

### 11.2 One run = three quizzes (decided)

- A run is **three quizzes in a row**; the score of the run is the **total**
  of the three, and the best score is the best run.
- A run takes **about 10 minutes at most**; a good run 4–6 minutes.

| | Max time |
|---|---|
| Quiz 1 (easy mood) | 150 s |
| Quiz 2 (medium mood) | 130 s |
| Quiz 3 (hard mood) | 120 s |
| 3 × loading screen with the mood gossip | 3 × ~5 s |
| Scenes and the result between quizzes | ~1 min |
| **Total** | **~8.5 min at worst** |

- Flow: menu → Quiz 1 (loading screen shows the day's gossip) → short
  result ("Quiz 1: 3200 points") → Quiz 2 → result → Quiz 3 → final screen
  (the three scores, the total, the best score).

**Built** (phase A, NOTES #26):

- Failing an exam (caught, 3 warnings) scores **0 for that exam**, and the
  run **goes on to the next one**, so a run is always three exams. Time up
  is not a failure: the paper is collected and graded.
- The game over chat comes right after a failed exam; a graded one gets
  the Balatro-style score count.
- Each exam starts with **0 warnings**.
- The **exam time setting is gone** (the times are fixed per exam, so top
  scores are fair).
- The questions: **3 / 4 / 5**.

### 11.3 The same teacher, a different mood every day (decided)

The teacher stays the same man (same pictures), but each quiz he is in a
different **mood**. The loading screen tells it as hallway gossip, e.g.
**"HALLWAY GOSSIP: Someone scratched his motorcycle."** That is a joke and
a hint at once: the player knows what kind of day it is. Each mood has its
own behaviour and its own **sign** to learn.

Before each exam a **hallway gossip** screen (built, NOTES #27, #30): a
slot machine spins over the exam's moods and stops on today's, then a short
story and what it means, as + and − lines. The Quiz has only good (or
plain) moods, the Midterm moods with good and bad sides, the Final only bad
ones; each exam picks from 4–5 (`QUIZZES`, `MOODS`). The six moods in the
table below were the first draft.

**He keeps an eye on you** (built, NOTES #30): above a hidden point on the
suspicion bar (60 % / 45 % / 30 % for the three exams) the teacher's watching
does not end until the bar drains back under it.

Each quiz has a **pool of two moods** (decided); a run picks one of the two
at random, so the difficulty grows quiz by quiz but no two runs are the
same. The six moods below are **proposed** (which ones stay is still open):

| Quiz | Mood (the gossip) | Behaviour | The sign |
|---|---|---|---|
| 1 | "His team won last night" | Happy, watching highlights on the phone: long busy times, always warns before turning. | He whistles; **the whistling stops** = he is about to turn. |
| 1 | "He graded papers all night" | Yawns at the desk, sometimes **dozes off** (very long safe moments), but now and then jerks awake. | Yawning = safe; **the snoring stops** = danger. |
| 2 | "He is on his third coffee" | Jittery: short busy times, many bluff "hmm"s, keeps moving between board and desk. Bonus: once he **goes to the toilet**, the room is empty for a few seconds: free copying. | Putting the cup down. |
| 2 | "He is fighting with someone on the phone" | Long phone calls at the desk; now and then yells "WHAT?!" at the phone (a bluff that scares you). | Before a real look he says **"I'll call you back"**. |
| 3 | "Someone scratched his motorcycle" | Angry and suspicious: short busy times, sneaky glances, long stares, staring gets a warning faster. A car alarm makes him look out of the window: a short chance for you. | He keeps grumbling; **silence** = he is coming. |
| 3 | "He caught someone last week" | Paranoid: walks between the rows, sneaky glances, bluffs. | **Footsteps** coming closer or going away. |

### 11.4 How the teacher picks what to do (proposed)

Instead of the fixed cycle, after each busy time the teacher **draws his
next move**, with weights set by the mood:

- **Normal turn:** "hmm", then watching (today's behaviour).
- **Bluff:** "hmm", but he does not turn; he goes on working. Turning your
  head away in panic costs time.
- **Sneaky glance:** no "hmm", a very short look (0.5–1 s). Never without
  its sign (e.g. the chalk sound stops a moment before), so it stays fair.
- **Long stare:** sometimes much longer than usual: a patience test.
- **Moving:** board ↔ desk, more or less often depending on the mood.

**Durations:** mostly normal, but now and then very short or very long,
instead of even ranges; this breaks the rhythm.

**Fairness rules:** never two sneaky glances in a row; always a few safe
seconds after a look; moves are drawn from a "bag" (like the Tetris piece
bag) so the same move does not come by chance again and again, but the
order cannot be predicted.

**Getting harder within a quiz:** the more answers you have written, the
shorter his busy times; the last question is always the tensest.

**In code:** every mood is only data in `settings.py` (move weights,
duration ranges, sign sound, fairness rules); `Teacher(mood)` follows it.
A new mood = new settings, not new code. Tests run every mood for ten
minutes and check that bluffs happen, sneaky glances never come twice in a
row and the safe time after a look is kept.

### 11.5 What it needs

- **Sounds** (the team picks them from a sound library): whistling,
  snoring, yawning, grumbling, footsteps, a cup, a car alarm, "I'll call you
  back", "WHAT?!". Sounds made in code stand in until the files exist.
- **Pictures** (optional, Gemini): the teacher asleep at the desk, the
  empty classroom (toilet break), the teacher looking out of the window.
  Without them the moment can be told with text and sound.
- **Mood pictures** (Gemini; the code is ready, NOTES #38; the prompts,
  ready to paste, are in `IMAGE_PROMPTS.md`): the same
  pictures with the mood's look, named `<picture>_<mood>.jpeg`, same
  camera angle and size as the originals (the zoom on his face and the
  paper spots must still match). Wanted: `birthday` (party hat, balloons,
  a banner; the four classroom pictures, the three look-away pictures,
  `classroom_warning`, `classroom_caught`), `dean_visit` (a suit and tie;
  the four classroom pictures, `classroom_warning`, `classroom_caught`),
  `new_phone` (`classroom_desk_busy`: head down in the new phone;
  `classroom_desk_watching`: looking up, phone still in his hand).
- **Sound files** that replace the ones made in code: `footsteps.mp3`,
  `paper-rip.mp3` (see `SOUND_FILES` in `ui/sounds.py`).

### 11.6 The team's new ideas, and what we think of them

The team brought five ideas. Not all of them will be built. Verdicts so far
(the order of work is in 11.7; the team chose to start with the three-quiz
run):

**1. Looking UP: "pretending to think" — maybe, last, as an experiment.**
A fourth head direction (pitch above a threshold). While the teacher
watches, staring at the ceiling looks innocent ("hmm, how did this go?"):
the suspicion bar drains fast. Cost: you see neither the teacher nor the
paper, the exam clock runs faster, and staring up too long gets suspicious.
(Other ideas for UP: spying on the teacher in a reflection of the ceiling
lamp; checking the wall clock.)
- Good: fits the theme; a "panic button" when the bar is high, with a price.
- Risk: the teacher is at the **top** of the screen, so a player looking at
  him lifts the head a little; that may be read as UP. Only testing with a
  real webcam can show whether a threshold works. A wrong UP here is
  especially annoying (the clock speeds up when you only wanted to look).
- So: after everything else, as a separate experiment.

**2. A run between quizzes, with a canteen break (Balatro / Vampire
Survivors style) — yes.** "Saving the semester": **Small Quiz → canteen →
Midterm → canteen → Final**. It matches the three-quiz run (11.2) and the
moods getting harder. A canteen choice takes 10–15 s, which fits the
10-minute budget. The biggest gain for playing again.

**3. Trade-off cards (picked in the canteen) — yes, 3–4 of the 5, some
changed.** Every card is an advantage with a price. Most of them only change
numbers that already exist (focus time, suspicion speed, escape time), so
they are cheap to build and test. (The team's notes said "5 s copying"; that
was the old copy bar — reading now takes `PAPER_FOCUS_TIME`, 2.5 s.)

| Card | Plus | Minus | Verdict |
|---|---|---|---|
| **Front row** (the teacher's blind spot) | Staring fills the suspicion bar much slower. | Being seen: half the time to escape (≈0.4 s instead of `CAUGHT_TIME`). | ✅ As it is: a real dilemma. |
| **Back row** (safe zone) | Turning the head is much harder to notice. | The paper is far: reading takes longer (2.5 s → ~4 s). | ✅ As it is. |
| **Glasses** (binocular view) | Reading is very fast (~1.2 s). | Tunnel vision: the edges of the classroom are blurred, so the teacher is hard to see (worst when he is at the desk, near the edge). | ✅ As it is. |
| **Energy drink** | Reading and writing twice as fast, extra exam time. | Proposed by the team: the head tracking "jitters" (more sensitive). | ⚠️ Keep the plus, **change the minus**: making the (already shaky) tracking worse on purpose feels like the game is broken, not like a price. Instead e.g. a heartbeat sound covers the teacher's sound cues, or suspicion fills faster. |
| **Radio earpiece** (spy) | Answers whispered into your ear: no need to look sideways. | You cannot hear the teacher's cues ("hmm", chalk...). | ❌ As it is it removes the core of the game (no reason to look sideways). ✅ **Toned down**: it only whispers **which neighbour knows** the answer (no searching for the "?" side), and you still have to read it; the price stays (no teacher sounds). |

Proposed rules: the canteen offers **2 random cards, you take 1**; cards
last until the end of the run, so at most 2 per run.

**4. Score and adrenaline — ✅ done (NOTES #26).**
- *Early hand-in bonus* (points per second left): already there (the time
  bonus, as a share of the exam time).
- *Close call*: already there, but every escape gives the same +150.
  **Better (the team's version):** the bonus grows with how full the
  suspicion bar was when you got away; escaping above 80 % gives a lot.
  That rewards exactly the risk. → do it.
- *"Copy in one breath"* (5 s without lifting the head): with the gradual
  focus every read already needs one unbroken look, so this adds nothing.
  If a "greed" reward is wanted: **finish a read after hearing the "hmm"**
  (keep looking although the teacher is about to turn).

**5. A letter grade at the end (AA–FF) — ✅ done (NOTES #37)**, as the team
asked: like a real teacher, only a semester grade, on a curve over all the
earlier runs (a fixed table for the first 5); a class average after each
exam. The first draft below was: Cheapest and
funniest. ME461 is a METU course, and the AA–FF grades are exactly what the
players know. Instead of a screen full of numbers, one huge neon grade badge:
"EXAM HANDED IN!" with [ AA ] under it; "CAUGHT CHEATING!" with [ FF ].

| Grade | Meaning | Colour | When |
|---|---|---|---|
| AA | Perfect | neon green / gold | 5/5 right, high score, close calls |
| BA / BB | Good | neon blue / cyan | 4–5 right, clean |
| CC | Pass | neon yellow | borderline (3 right) |
| DC | Conditional pass | neon orange | 1–2 right, or many warnings |
| FF | Fail | neon red | caught, time up, or 0 right |

Each quiz gets a grade; the run ends with a **semester grade** (from the
three). Score and best score stay, smaller, under the grade. (The exact
thresholds are still open; with 3/4/5 questions per quiz they must use the
share of right answers, not "5/5".)

### 11.7 Order of work

1. **Core:** the three-quiz run with the moods and the controlled-random
   teacher (11.2–11.4) — in two phases, see 11.8. ✅ Phase A done; phase B next.
2. **Cheap and strong:** letter grades; ✅ close-call bonus growing with the
   suspicion.
3. **Playing again:** the canteen and 3–4 cards.
4. **Experiment:** looking UP.

### 11.8 Plan for the three-quiz run (phase A built in NOTES #26)

**What changes in the code.** Today one "game" is one exam: `Game` holds the
rules of one quiz, and when it ends the end menu comes. A layer goes on top:

- A new **`Run`** class (`run.py`): which quiz you are at, each quiz's
  result (score, how it ended, later its grade), the mood picked for each
  quiz, the total. The rules stay in `Game`; `Run` only puts the quizzes in
  order. No pygame, so it is tested like `Game`.
- The **quizzes are data** in `settings.py`, e.g.

  ```
  QUIZZES = [
      {"title": "THE QUIZ",    "time": 150, "moods": ("team_won", "all_nighter")},
      {"title": "THE MIDTERM", "time": 130, "moods": ("coffee", "phone_fight")},
      {"title": "THE FINAL",   "time": 120, "moods": ("motorcycle", "paranoid")},
  ]
  ```

  (plus the number of questions per quiz, see the decisions below).
- At the start of each quiz `Game` is reset with that quiz's time (and
  question count), and `Teacher` with the mood picked from its pool.

**Screens:**

```
MENU → LOADING (Quiz 1 + gossip) → GAME → [scenes] → QUIZ RESULT
     → LOADING (Quiz 2) → GAME → … → QUIZ RESULT
     → LOADING (Quiz 3) → GAME → … → RUN END (3 results + total + best) → end menu
```

- **Loading screen:** "ME461 - CHAPTER 1/2/3", "THE QUIZ / THE MIDTERM /
  THE FINAL", the date, and the **gossip line** of the mood, which replaces
  today's random funny loading line.
- **QUIZ RESULT (new):** a short screen between quizzes ("QUIZ 1: 3200
  POINTS", or its grade). It goes on by itself, or at once with Space.
- **RUN END (new):** the three quiz results one under the other, the total,
  "NEW BEST!", then today's end menu (play again / main menu / quit).
- `R` restarts the whole run; `M` leaves the run for the main menu.
- Score: each quiz scores itself; the run's score is the sum; the best
  score is the best run.
- Later the canteen comes in between: … QUIZ RESULT → CANTEEN → LOADING …

**Two phases:**

- **Phase A — the skeleton of the run:** `Run`, three quizzes, the result
  and run-end screens, total score, best score. The moods are only
  **different numbers** in this phase (the teacher's busy/watching times
  and move chance per quiz) plus the gossip line on the loading screen. A
  playable run the team can test right away.
- **Phase B — real moods:** bluffs, sneaky glances, sign sounds, fairness
  rules, getting harder within a quiz (11.4). That reworks `teacher.py`, so
  it is a step of its own.

**Tests:** quizzes come in order; a lost quiz scores 0 and the run goes on;
the total and the best score are right; each quiz gets its own time,
question count and mood.

**Time check:** with 3/4/5 questions a good run takes about 4 minutes; the
longest one (150 + 130 + 120 s, plus loading, scenes and results) stays
under 8.5 minutes.

### 11.9 Decisions (taken when phase A was built)

| # | Question | Decided |
|---|---|---|
| 1 | An exam is failed: then what? | **0 points for that exam, go on to the next.** Time up is not a failure: the paper is collected and graded. |
| 2 | How many questions per exam? | **3 / 4 / 5.** |
| 3 | When does the game over chat come? | **Right after a failed exam.** (The proposal was "at the end of every run"; the team chose: score count when the exam is not failed, chat when it is.) |
| 4 | Letter grades (AA–FF) in phase A? | **Not yet.** The grade is shown as points ("2.5 / 3"); letter grades are the next cheap step (11.6.5). |
| 5 | The "exam time" option in Settings | **Removed.** |
| 6 | Warnings | **Start from 0 in every exam.** |
| 7 | The result screen between exams | **The score count, then a menu:** "Next exam" / "Main menu" (not a timer). |
| 8 | Which moods stay (11.3)? | All six, as numbers for now; each exam has a pool of two. |
| 9 | Canteen and cards (11.6) | Still to build; rules as proposed. |
| 10 | Best score | **Top 5 runs** on the main menu and the results, the new one lit up with "NEW HIGH SCORE!". |

### 11.10 Where things stand (for whoever picks this up)

- **Branch:** `main`. `dont-get-caught` (the game), `windows` and
  `windows-support` were merged into it (NOTES #32). NOTES #25–#31 are in one
  commit (after `9c91a49`, NOTES #24): guessing and blanks, the code in folders, the
  Balatro-style count, the three-exam run with moods, top scores, the
  gossip slot machine, music, crossfades, the hidden suspicion point, the
  ninja and sharp-eye bonuses. All 179 tests pass.
- **Emre's branch** `me461-python-visual-tracking-app2-gp` (commit
  `2ddf878`) was not merged; its README and parts of its `render.py` are
  in Turkish.
- **Sounds:** the team picks the sound files from a library themselves;
  until then sounds made in code stand in (`ui/sounds.py`, `SOUND_FILES`).
  The music is `assets/sounds/theme.mp3` (menus, Suno) and `thrilling.mp3` (exam).
- **Next step:** play a whole run with the webcam and tune `QUIZZES` and
  `MOODS`; then phase B (11.4): bluffs, sneaky glances, sign sounds.

---

## 12. Update 2: calibration, the score table, a practice exam, characters

Asked for by the team after playing (8 Oct 2026). Built in this order, one
NOTES entry each. All the numbers stay in `settings.py` (it already holds
every tuning number, so nothing had to be moved); the characters are a
`CHARACTERS` table there, so tuning one is changing a number, not code.

| # | What | Why |
|---|---|---|
| 1 ✅ #40 | **Four-pose calibration** | Every player turns their head differently. The player shows the game each pose (screen, left, right, down) and presses Space; the thresholds come from their own poses. |
| 2 ✅ #41 | **The score count as a table** | The cards and the bonus rows were hard to read; a table (what you wrote, the right answer, the points) reads at a glance. |
| 3 ✅ #42 | **A practice exam after How to play** | 2 questions, a sleepy teacher, short: try it all for real once before the run. Not counted in the scores. |
| 4 ✅ #43 | **Answers without streaks** | "A A A B" happened often. No letter twice in a row, at most twice per exam; the knowing neighbour is never the same side three times in a row. |
| 5 ✅ #44 | **Slot-machine score** | The score rolls like the reels of a slot machine while it counts; the bigger the score, the more it shakes, sparkles and flashes (Balatro). |
| 6 ✅ #45 | **Characters** | Pick who you are before a run; each one bends one rule with an advantage and a price. |

### 12.1 Calibration (item 1)

The start screen (and Settings → Recalibrate, and K in the game) goes
through four poses, each with its own instruction:

1. **SCREEN** — sit normally and look at the screen.
2. **LEFT** — turn left as far as you would to copy, *but keep the screen
   in sight* (in the game you must still see it).
3. **RIGHT** — the same to the right.
4. **DOWN** — look down at your desk, still seeing the screen.

Each pose: hold it, press Space (or click), and it is measured for
`CALIBRATION_SAMPLE_TIME`. The threshold of a direction is
`CALIBRATION_SHARE` (60 %) of the way to the pose, kept between
`CALIBRATION_MIN_ANGLE` and `CALIBRATION_MAX_ANGLE`. A pose that went the
wrong way or hardly moved keeps the old fixed threshold. The menus use the
same left/right turn.

### 12.2 Characters (item 6)

Picked on a new screen after PLAY, kept for the next run. Each changes
only numbers the game already has (focus time, the suspicion bar's
speeds, the teacher's times) plus one new rule.

| Character | Plus | Minus |
|---|---|---|
| **NPC with a Monster bag** (a Monster gaming laptop, at a paper exam) | Nothing special: the plain game. | Nothing. |
| **The New Era guy** (flat-brim cap) | The brim hides your eyes: staring and being seen copying fill the bar slower. | Whenever you are not looking at your paper the bar creeps up slowly, even when the teacher is busy. |
| **Glasses** | Reading a neighbour's paper is a bit quicker. | Looking at the teacher, the classroom is blurry first and has to come into focus. |
| **The nerd** | Starts every exam with one joker (J while looking down: writes the right answer). | Must hand the exam in early (a share of the time left), or loses points; his early bonus counts only from that line. |
| **Energy drink addict** | A coin toss each exam: **sugar rush** — the world runs a bit slower for you. | **Crash** — now and then you get sleepy: reading gets slower, your eyelids close. |
| **The front-row student** (was the teacher's buddy, NOTES #58) | He checks on you less often (longer busy times). | When he does look, he looks longer. |
| **The 7th-year legend** (NOTES #58) | Has seen it all: the teacher's looks are shorter. | The teacher has seen him too: the bar fills faster when he is seen copying. |
| **Not a ME student** (NOTES #58) | The teacher thinks he's just lost: staring at the teacher barely fills the bar. | It's all Greek to him: the neighbours' answers show up as α β γ δ (pictures `left_greek_*` / `right_greek_*`, prompts in IMAGE_PROMPTS.md; a note if one is missing). |
| **The "quick question" guy** (NOTES #58) | Keeps the teacher explaining: longer busy times. | The teacher keeps an eye on him: the bar creeps up while he is not looking at his paper. |
| **Lazy but funny** | Both neighbours like you: both show the right answer. | The teacher gets alarmed faster: the bar fills faster when he sees you. No sharp-eye bonus (nothing to find). |

The character is on the loading screen ("PLAYING AS") and on a badge in
the game. The top scores do not change. The practice exam is always
played as the NPC.

### 12.3 The briefing and the sliding character screen (NOTES #48)

PLAY starts the character music and a sarcastic briefing timed to it (a
line per bar: "3 EXAMS." ... "(A LOT OF PRESSURE.)", "DON'T GET CAUGHT.",
soft to hard, the title staying 8 beats, NOTES #60); then the
characters slide in as a Hotline Miami-like row, the chosen one big in the
middle and thumping to the beat. Timing numbers measured from the file:
147 BPM, first hit 0.81 s, drop 11.84 s (`settings.py`).

### 12.4 To tune after playing (all in `settings.py`)

- Calibration: `CALIBRATION_SHARE` (0.6). Too jumpy → higher; too hard to
  reach → lower.
- Each character's numbers in `CHARACTERS`. Signs that one is too strong:
  everyone picks it; too weak: nobody does. The nerd's 30 % and the cap's
  `creep_time` (30 s) are the guesses most likely to need changing.
- The game is still hard (the team's feeling): the first numbers to try
  are `PAPER_FOCUS_TIME` (2.5 s), `CAUGHT_TIME` (0.7 s) and the moods'
  `"watching"` times.
