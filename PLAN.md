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
- **Gradual focus** (Emre's idea): the neighbour's paper (the picture with
  the letter circled, or "?") is blurry and gets sharper the longer you keep
  looking; after `PAPER_FOCUS_TIME` (2.5 s) without looking away you have
  **read** it (ding). Every look starts blurry again, so reading means
  holding a risky look; the blur itself shows how far (no bar). This replaced the old
  copy bar (5 s, kept between looks), where copying was just waiting.
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
Please intro; the official notice; gradual focus instead of the copy bar;
score, close calls and a best score; camera reconnecting; tests (121).

**Next, roughly in order:**

0. **The next big update: three quizzes and the teacher's moods.** Being
   planned in section 11; it changes items 1, 2 and 5 below.

1. **Playtest and tune** the numbers in `settings.py` with the whole team
   (teacher durations, `PAPER_FOCUS_TIME`, `EXAM_TIME`, `CAUGHT_TIME`). Test with
   other webcams, lighting, glasses.
2. **More sounds:** the chalk sound as a loop while the teacher erases the
   board (needs `loop()`/`stop()` in `sounds.py`), quiet classroom background,
   real tick/ding files. The game must keep working without them.
3. **More art:** a turning picture; a walking teacher so moving between board
   and desk is not a jump.
4. **Menus and polish:** ✅ main menu, how-to-play screen, settings, end
   menu, all head-controlled (commit #15). Still: end screen with
   time/warnings, readable webcam errors, menu music.
5. **Difficulty and score:** ✅ score (right answers, time left, close
   calls, warnings) and a best-score file. Still: the teacher checks more
   often as the exam goes on; Easy/Normal/Hard; levels (Quiz → Midterm →
   Final) with different teachers.
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

**Proposed** (waiting for a yes):

- Losing a quiz (caught, 3 warnings, time up) scores **0 for that quiz**,
  and the run **goes on to the next quiz**, so a run is always three quizzes
  and its length stays predictable. The game over chat of the two logos
  comes at the end of the run (e.g. when no quiz was passed).
- Each quiz starts with **0 warnings**.
- The **exam time setting goes away** (the times are fixed per quiz, so
  best scores are fair); maybe a "difficulty" setting instead.

### 11.3 The same teacher, a different mood every day (decided)

The teacher stays the same man (same pictures), but each quiz he is in a
different **mood**. The loading screen tells it as hallway gossip, e.g.
**"HALLWAY GOSSIP: Someone scratched his motorcycle."** That is a joke and
a hint at once: the player knows what kind of day it is. Each mood has its
own behaviour and its own **sign** to learn.

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

**4. Score and adrenaline — mostly there already, one change.**
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

**5. A letter grade at the end (AA–FF) — yes, definitely.** Cheapest and
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
   teacher (11.2–11.4) — in two phases, see 11.8.
2. **Cheap and strong:** letter grades; close-call bonus growing with the
   suspicion.
3. **Playing again:** the canteen and 3–4 cards.
4. **Experiment:** looking UP.

### 11.8 Plan for the three-quiz run (talked through, not built yet)

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

### 11.9 Decisions still open (with our proposals)

| # | Question | Proposal |
|---|---|---|
| 1 | A quiz is lost (caught, 3 warnings, time up): then what? | **0 points for that quiz, go on to the next.** The run is always 3 quizzes. The caught scene plays; the game over chat does not (see 3). |
| 2 | How many questions per quiz? | **3 / 4 / 5**: harder each time, and the run stays short. (5/5/5 also works, but the run gets longer.) |
| 3 | When does the game over chat (Gemini and Claude logos) come? | **At the end of every run**, with lines depending on the result: they mock a bad run, they are jealous of a good one. |
| 4 | Letter grades (AA–FF) already in phase A? | **Yes**: the result screens are new anyway, so a big grade instead of a number costs almost nothing. Thresholds to decide (share of right answers, warnings, close calls). |
| 5 | The "exam time" option in Settings | **Remove it**: times are fixed per quiz, so best scores are fair. Maybe a "difficulty" option later. |
| 6 | Warnings | **Start from 0 in every quiz.** |
| 7 | How long is the result screen between quizzes? | **4 s, or Space.** |
| 8 | Which moods stay (11.3)? | All six as proposed until the team says otherwise; each quiz has a pool of two (decided). |
| 9 | Canteen and cards (11.6) | Rules proposed: 2 random cards offered, take 1, they last the run. Energy drink and earpiece only in their changed form. |

### 11.10 Where things stand (for whoever picks this up)

- **Branch:** `dont-get-caught`. Last commit `9db2613` (NOTES #15–#23:
  menus, scenes, Glitch Please intro, official notice, softer menus).
- **Not committed yet (NOTES #24):** gradual focus instead of the copy bar,
  camera reconnecting (both taken from Emre's branch), score, close calls,
  best score (`highscore.py`), no focus bar, and this section 11. All 121
  tests pass.
- **Emre's branch** `me461-python-visual-tracking-app2-gp` (commit
  `2ddf878`) started from `681fe15` and rebuilt the papers differently. It
  was **not merged**; his gradual focus and camera code were brought over
  (NOTES #24 lists what was and was not taken). The team decided not to
  follow the rest of his plan.
- **Sounds:** the team picks the sound files from a library themselves;
  until then sounds made in code stand in (`sounds.py`, `SOUND_FILES`).
- **Next step:** answer 11.9, then build phase A of 11.8.
