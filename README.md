# Visual Tracking Game

A webcam game controlled by the player's body, written only in Python and its
libraries. ME461 group project by **Glitch Please**.

## Status

**Playable.** The game reads which way your head is pointing (down at the
paper, at the screen, or to the side). A run is three exams (the Quiz, the
Midterm, the Final): copy answers from your neighbours while the teacher is
busy, or guess, without getting caught or staring too long. The teacher is
in a different mood each exam. The classroom pictures are in; the teacher's
turning sound and the game-over sound are real files, the other sounds are
still beeps made in code. Next: the teacher's real moods (bluffs, sneaky
glances), see `PLAN.md` section 11.

## Requirements

- **Linux** (developed on Ubuntu 26.04, Python 3.14) or **Windows 10/11**
  with **64-bit** Python 3 (3.12 is the safest choice on Windows, see below)
- A webcam

## Setup and run

The start script creates the `.venv` environment and installs the libraries
from `requirements.txt` the first time it runs, and again whenever
`requirements.txt` changes (for example after a `git pull`). After that it
starts the game right away. The first start needs internet and takes a few
minutes.

### Linux

```
git clone https://github.com/nakciefe-commits/me461-python-visual-tracking-app-gp.git
cd me461-python-visual-tracking-app-gp
sudo apt install -y python3-venv
```

That's all: `run.sh` creates the `.venv` environment and installs the
libraries from `requirements.txt` the first time it runs, and again whenever
`requirements.txt` changes (for example after a `git pull`).

**Windows:**

1. Install **64-bit Python 3** from <https://www.python.org/downloads/>
   (3.12 is the safest). In the installer, tick **"Add python.exe to PATH"**.
2. Get the code: `git clone` as above (or GitHub → Code → Download ZIP, and
   unzip it). `python3-venv` is not needed.
3. Double-click **`run.bat`**. It does the same job as `run.sh`, and stops
   with a clear message on 32-bit Python (MediaPipe needs 64-bit). If
   installing the libraries fails because MediaPipe has no package for your
   Python version, install Python 3.12, delete the `.venv` folder and run
   `run.bat` again.

Run the game natively on Windows, not in WSL or a Linux virtual machine: the
webcam does not work there without extra setup. **Webcam not working?** See
"If the webcam doesn't work" below.

## Run

```
./run.sh
```

On Windows, double-click `run.bat` (or type `run.bat` in a terminal in the
project folder).

The game opens with our team's "Glitch Please" intro (any key skips it), then
a (satirical) official notice on a desk: it is typed out (Space shows it all
at once), press Space to sign it (the "signature" is someone trying to draw a
helicopter), an "APPROVED" stamp comes down and the
game goes on. Sit at the desk with the webcam on top of the monitor. The start screen shows
the webcam with the tracking drawn on your face. Sit normally, look at the
screen, and click **Calibrate** (or press Space): the game learns your
"looking at the screen" position. Then it asks for three more poses, one
at a time, with an arrow: **turn left**, **turn right** and **look down**,
each only as far as you would in the game *while still seeing the screen*.
Get into the pose and press Space; hold still for a second (ding). The game
sets how far you must turn from your own poses, so it fits how you sit and
move. Then the **main menu** opens (Play,
How to play, Settings, Quit). Control it with your head: **tilt up/down** to
move the selection, **turn right** and hold until the bar fills to choose,
**turn left** and hold to go back. The arrow keys, Enter, Esc and the mouse
work too; after a key press or a click the head is ignored for 1 s, so the
two do not fight (the box at the bottom right shows "KEYBOARD", then "HEAD
CONTROL" again). **Quit** and **Main menu** ask "ARE YOU SURE?" first:
turn right again (or Enter) for yes, left (or Esc) for no. In **Settings** you can turn the sound off, switch
fullscreen, or calibrate again. The main menu also shows the **top scores**
(the 5 best runs).

**How to play** is a hands-on guide: Gemini and Claude take turns talking
to you (typed out, with little talking blips) and you try each thing as
they explain it: look down at your paper and write a letter, turn right
(the neighbour shows "?"), turn left and keep looking until the paper is
sharp (B), write B, look at the screen to see the teacher. Then they
explain the "hmm", being caught, close calls, warnings, the bonuses and the
three-exam run. A banner says what to do, with a bar while you hold it.
Space hurries a line (or does the task for you), Esc goes back. When they
are done, a **practice exam** starts: two questions, 60 seconds, a sleepy
teacher with long busy times, and everything at 75 % of its danger (the
suspicion bar fills slower, his looks are shorter, you read faster). It counts for nothing (no top score, no
class average); after it, "Play for real" starts a run.

Choose **Play**: the character music starts and a short, sarcastic
**briefing** plays to it, Hotline Miami style: on every strong hit of the
music a new line slams onto the screen ("3 EXAMS." "1 SEMESTER." "0 HOURS
OF STUDYING." ... "YOUR FAMILY EXPECTS... ...THE MAXIMUM SCORE." "NO
PRESSURE." "(A LOT OF PRESSURE.)"), with a flash and a shake. Space, Enter
or turning your head right skips it. When the music drops, the characters
slide in: they stand in a row, the chosen one big in the middle, thumping
to the beat; **turn left/right** to slide the row, **look down** (hold) to
pick, look up (hold) to go back. Choose
**who you are**. Each character bends one rule, with
an advantage and a price (the numbers are in `CHARACTERS` in
`settings.py`):

| Character | + | − |
|---|---|---|
| NPC with a Monster bag (a gaming laptop he brought to a paper exam) | the plain game | — |
| The New Era guy (flat-brim cap) | staring and copying fill the suspicion bar slower | while you are not looking at your paper the bar creeps up (full in 30 s), even when the teacher is busy |
| Glasses | reads a neighbour's paper faster | the classroom is blurry for a moment each time you look at the teacher |
| The nerd | one **joker** per exam: `j` while looking at your paper writes the right answer | his early bonus only starts at 30 % of the time left (0 there, the full bonus with all the time left); later than that, −1000 points |
| Energy drink addict | a coin toss each exam (50 %, 15 % less after every rush in the run): **sugar rush**, the world (teacher, clock, bar) runs slower for you | or a **crash**: now and then you get sleepy (eyelids close) and read slowly |
| The teacher's buddy | the teacher checks less often | but when he looks, he looks longer |
| Lazy but funny | both neighbours show you the answer | the teacher is alarmed faster; no sharp-eye bonus |

A badge at the top left of the game shows your character (and the nerd's
jokers and deadline, the energy drink's day). **Play again** keeps the
character. Then the **run: three exams in a row**:

| Exam | Questions | Time |
|---|---|---|
| The Quiz | 3 | 150 s |
| The Midterm | 4 | 130 s |
| The Final | 5 | 120 s |

Before each exam the **hallway gossip** screen tells what happened to the
teacher. Turn right on **Spin**: a slot machine rolls through the exam's
moods (4–5 each) and stops on today's, e.g. "He is on his third coffee.",
then a short story and what it means: green **+** and red **−** lines
("+ His looks are quick", "− He keeps moving"). The Quiz's moods are good
days (or a plain one), the Midterm's have good and bad sides, the Final's
are bad days. A mood changes how long the teacher is busy and watching and
how often he moves. When you are ready, **turn right** (and hold) on "I'm
ready" (or press Enter); turn left goes back to the menu. A 3-second
"chapter" screen ("Chapter 1/3 - The Quiz", today's date) gives you time to
sit straight; when its bar is full, a quick title card slams in the exam's
name and what you think of it ("THE QUIZ - This gotta be easy... right?",
"THE MIDTERM - I can handle this. Probably. Maybe not.", "THE FINAL - God,
please help me."), then the exam starts. (The first exam's gossip spin
still has the character music; from the second one on, the menu theme.)

| Head | Option | What happens |
|---|---|---|
| Down | 1 - paper | Safe. You see your own paper, not the teacher, and hear nothing. Press **A, B, C or D** to write an answer, or **S** to leave the question blank. Any letter goes, read or not: guessing is allowed. |
| At the screen | 2 - teacher | The only way to see the classroom and what the teacher is doing. While the teacher looks at the class, the suspicion bar fills; after 3 s it turns red, and when it is full you get a warning: the teacher walks up to your desk and points at you angrily (the game stops for 2.5 s while this happens). 3 warnings = game over. Being seen copying fills the same bar, so staring afterwards carries on from there. The bar never jumps to empty: it drains slowly while you do nothing suspicious. |
| Left / right | 3 - copy | The neighbour's paper is blurry and gets sharper the longer you keep looking; after 2.5 s without looking away you can read it: a letter, or **?** if they don't know it (then the other neighbour does). Every look starts blurry again. Remember it, look down and write it. Answer every question to hand in the exam. You see the neighbour's paper, not the teacher. If the teacher is looking at the class, an **alarm** plays and the suspicion bar fills in 0.9 s: look away before it is full, or you are **caught**. Copying does not move forward while the teacher sees you. |

The teacher erases the board or plays on the phone (safe), then looks at the
class for a few seconds (danger). **Luigi's "hmm"** means the teacher is
about to look up: stop copying. There is no sound when they are busy again:
look at the screen to find out. While you look down at the paper you hear
**nothing** from the teacher: look up to find out what they are doing.
While he erases the board you hear the **chalk**; it stops the moment he
starts to turn. You hear his **footsteps** when he walks between the board
and the desk, and when he comes to your desk after a warning. When you are
caught, he tears your exam in two (rrrip... rrrrip!).

Some moods change more than the numbers: with a **new phone** he never
leaves his desk. A mood can also have its own pictures (his birthday: a
party hat and balloons; the dean's visit: a suit): a file like
`assets/images/classroom_board_busy_birthday.jpeg` is shown instead of
`classroom_board_busy.jpeg` on that day. Without them, the normal pictures.

**When the clock runs out**, the teacher collects your paper as it is (the
unanswered questions count as blank) and it is graded: falling notes play.
**Failing** an exam means being caught or getting 3 warnings (the Metal Gear
alert plays). When you are caught, a red Metal Gear "!" pops up over the
teacher, then he tears up your exam. After failing comes a GAME OVER screen
where the Gemini and Claude logos make fun of you, with a different joke
each time, typed out with little talking blips (Space skips it). A failed
exam scores 0, and the run goes on with the next exam.

**Music:** an 80s Miami theme (`assets/sounds/theme.mp3`) loops in the
menus from the start screen on (not during the intro and the notice). It
fades out while an exam loads; during the exam a tense track
(`assets/sounds/thrilling.mp3`) plays, quieter so you still hear the
teacher, and stops when you fail. The theme fades back in afterwards, from
its beginning. The briefing and the character screen have their own
track (`assets/sounds/character_[cut_180sec].mp3`), which starts at once
(the briefing is timed to it). Sound OFF in the settings turns them all off. Every screen
change is a short crossfade.

**Grading:** every question is worth one point: right **+1**, wrong
**−0.5**, blank **0**. So a blind guess is a gamble (right only one time in
four).

**He keeps an eye on you:** each exam has a hidden point on the suspicion
bar (lower each exam). Above it, the teacher does not look away: he keeps
watching you until the bar drains back under it, so you have to look at
your paper.

**Score:** after a handed-in exam the score is counted up part by part, like
in Balatro, in two tables. On the left one row per question lights up in
turn: what you wrote, the answer key, right / wrong / blank and the points
(+1000 right, −500 wrong, 0 blank), then the grade. On the right the
bonuses come one row each: the **early bonus** (up to +1000, the share of the exam time you did
not use), the **close calls** (the teacher saw you copying and you looked
away in time: 100 to 500 points, the fuller the suspicion bar was the more;
above 80 % it is a "razor close" call, +300 more), **sharp eyes** (+100
each time the first paper you read for a question is the one that knows),
**NINJA!** (+1500: every answer right, no warning; **almost ninja** +500
with one warning) and −300 per warning.
The score itself rolls up like a **slot machine**, one spinning reel per
digit in a gold frame with bulbs: the bigger it gets, the more it shakes,
sparkles and flashes, and a huge score ends with **JACKPOT!** and a
fanfare. The run's total is counted the same way.
Space skips the count. The exam's score is never below 0.

After each exam you also see the **class average**: the average score of
that exam over everyone who played it on this computer before.

After the last exam, the **results** show each exam's score and the run's
total, counted up, next to the top scores. Then the **semester grade** is
stamped on, METU style (AA, BA, BB, CB, CC, DC, DD, FD, FF), like a real
teacher grades: **on a curve**. Your total is compared with all the earlier
runs on this computer (their average and standard deviation): about the
class average is a CC, far above it an AA. For the first 5 runs there is no
class yet, so the grade comes from the share of right answers instead (90 %
= AA, 50 % = CC). A total of 0 is always FF. A total good enough for the top 5
lights up in the list with "NEW HIGH SCORE!", confetti and a fanfare, and
you type a **three-letter name** for it, like on an arcade machine: tilt
up/down to change the letter, turn right for the next one, turn left to go
back (or just type the letters and press Enter). The top scores
("1. EFE 12808 7 OCT") are kept in `highscore.json` (each computer has its own).

Keys: Space calibrate (once per pose), `a`/`b`/`c`/`d` write an answer, `s` leave it blank,
`j` the nerd's joker (all while looking at your paper), Esc quits in the game, asks
"Are you sure?" on the main menu (and goes back in the other menus; the window's X button and
`q` do nothing, Ctrl+C in the terminal still stops it), `r` restart the run, `m`
main menu, `k` recalibrate, F11
fullscreen on/off, `t` always show the classroom and the teacher's state (for testing). The game opens as a maximized window (title bar and taskbar stay
visible); F11 makes it borderless fullscreen. In `settings.py`, set
`FULLSCREEN = True` to start fullscreen or `MAXIMIZED = False` to start as a
small 960×600 window. If no face
is seen for more than 0.6 s the game pauses, unless your head was going down:
then you are looking at the paper (the camera can't see your face then), and
the game carries on. You don't need to turn your head
far: 18° counts as looking to the side, and a face turned too far away is hard
to track.

To tune the head tracking, watch the yaw/pitch numbers at the top right of
the game and change the numbers in `settings.py`. Your own face (the
webcam picture) is only shown on the start screen, while calibrating; the
menus and the game do not show it.

The old body tracker still runs with `.venv/bin/python old/tracker.py`
(Windows: `.venv\Scripts\python old\tracker.py`).

## How it works

Each webcam frame: grab it with OpenCV (`tracking/camera.py`), find the face
with MediaPipe and work out the head direction (`tracking/head_tracker.py`),
move the teacher (`logic/teacher.py`) and the game rules (`logic/game.py`)
forward, play sounds for what happened (`ui/sounds.py`), and draw the screen
with pygame (`ui/render.py`). `main.py` runs the loop. `LEARN.md` explains
every file.

## If the webcam doesn't work

Go through these in order. After each change, start the game again.

1. **Another program is using the webcam.** Only one program can use it at a
   time. Close Zoom, Teams, Discord, OBS, the Camera app, and browser tabs with
   video calls. (The game waits on "WAITING FOR CAMERA" and reconnects by
   itself once the camera is free.)
2. **Windows blocks camera access.** Settings → Privacy & security → Camera:
   turn on **Camera access** and **Let desktop apps access your camera**.
3. **The camera is switched off or covered.** Many laptops have a sliding
   cover, a privacy switch, or a camera key (often one of F1–F12 with a
   camera icon).
4. **The wrong camera opens** (e.g. a laptop's infrared camera, a virtual
   camera from OBS, or a phone used as a webcam). In `settings.py` change
   `CAMERA_INDEX = 0` to `1`, then `2`. To see which numbers work, run this in
   the project folder; it prints `True` for each camera that opens:
   - Windows: `.venv\Scripts\python -c "import cv2; [print(i, cv2.VideoCapture(i, cv2.CAP_DSHOW).isOpened()) for i in range(4)]"`
   - Linux: `.venv/bin/python -c "import cv2; [print(i, cv2.VideoCapture(i).isOpened()) for i in range(4)]"`
5. **Windows only: the picture is black or frozen, or the game keeps waiting
   for the camera.** In `settings.py` set `WINDOWS_DIRECTSHOW = False`. The
   game then uses Windows' default camera system (Media Foundation). It can
   take 10+ seconds to open, so wait a bit.
6. **The picture works but the face is not found, or the game is slow.**
   Turn on a light in front of you. A dark room makes webcams send fewer
   frames per second and hides the face. Avoid a bright window behind you.
7. **Linux only: no camera found.** Run `ls /dev/video*`. If nothing is
   listed, the system doesn't see the webcam (check the cable / USB port). If
   it is listed but won't open, add yourself to the `video` group:
   `sudo usermod -aG video $USER`, then log out and in.

If none of this helps, write down the exact error text from the terminal (on
Windows the `run.bat` window stays open after a crash) and the steps you tried.

## Tests

```
.venv/bin/python -m unittest discover -s tests -v
```

On Windows: `.venv\Scripts\python -m unittest discover -s tests -v`

## Files

The code is in three folders: **`logic/`** the rules (no drawing, no camera,
all tested), **`tracking/`** the webcam and the head, **`ui/`** everything
you see and hear. `main.py` and `settings.py` stay at the top.

| File | Purpose |
|---|---|
| `main.py` | The game: main loop and screens. |
| `settings.py` | Every tuning number in one place, also the three exams and the teacher's moods. |
| **`logic/`** | |
| `logic/game.py` | The rules of one exam: clock, warnings, caught, scenes, score. Uses the three files below. |
| `logic/exam_paper.py` | Your paper: the answer key, what you wrote, the grade (+1 / −0.5 / 0). |
| `logic/neighbours.py` | Reading a neighbour's paper (it gets sharper as you keep looking). |
| `logic/suspicion.py` | The suspicion bar and close calls. |
| `logic/run.py` | A run: three exams in a row, their moods, the total. |
| `logic/teacher.py` | The teacher: busy, turning, watching; at the board or the desk; today's mood. |
| `logic/tally.py` | The score count after an exam (one part at a time). |
| `logic/highscore.py` | Loads and saves the top scores (`highscore.json`, not in git). |
| `logic/bag.py` | Random order without repeats (like the Tetris piece bag), for the game over jokes. |
| `logic/menu.py` | Menus: the selected item, and head tilts/turns → up/down/select/back; the loading bar's uneven fill. |
| `logic/disclaimer.py` | The opening notice: typing, signing, the stamp (no drawing). |
| `logic/guide.py` | The "How to play" guide: Gemini and Claude's lines and the tasks to try (no drawing). |
| `logic/character.py` | The characters: their rules (from `CHARACTERS` in `settings.py`), the blur of glasses, the energy drink's rush or crash. |
| **`tracking/`** | |
| `tracking/camera.py` | Reads the webcam in the background. |
| `tracking/head_tracker.py` | Webcam frame → head direction (DOWN / SCREEN / LEFT / RIGHT). |
| **`ui/`** | |
| `ui/render.py` | The `Renderer`: loads fonts and pictures; its drawing is in the files below. |
| `ui/style.py` | The neon look: colours, fonts, text, bars, boxes. |
| `ui/draw_game.py` | The game screen: the classroom, your paper, the neighbours, the strips. |
| `ui/draw_scenes.py` | Warning, caught and game over scenes. |
| `ui/draw_results.py` | The score count after an exam, the run's results, the top scores. |
| `ui/draw_menus.py` | Start, loading, camera wait and the menus. |
| `ui/draw_notice.py` | The opening notice on the desk. |
| `ui/draw_guide.py` | The "How to play" guide: what you look at, the task banner, the chat. |
| `ui/draw_characters.py` | The character screen, with portraits drawn in code. |
| `ui/sounds.py` | Sound effects: beeps made in code, some replaced by files. |
| `ui/glitch_intro.py` | Our team's "Glitch Please" intro. One file, only needs pygame: copy it into any project. |
| `tests/` | Unit tests for the rules, the tracker and the menus. |
| `old/tracker.py` | The first body tracker, kept for reference. |
| `run.sh` | Launcher (Linux). |
| `run.bat` | Launcher (Windows). |
| `.gitattributes` | Keeps Windows line endings in `run.bat`. |
| `face_landmarker.task` | Pre-trained MediaPipe face model. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model, used by `old/tracker.py`. |
| `assets/images/` | The four classroom pictures, plus the three look-away pictures (`classroom_desk_looking_down/left/right`) and each neighbour's paper with a letter (`left_A` … `left_D`, `left_unknown` = "?", same for `right_`), the teacher pointing at you after a warning (`classroom_warning`) (`original/`: as made by Gemini, before sharpening). |
| `assets/sounds/` | Sound files (Luigi "hmm", MGS alert, chalk erasing for later), `theme.mp3` (menu music), `thrilling.mp3` (exam music) and `character_[cut_180sec].mp3` (the briefing and the character screen). |
| `LEARN.md` | **Start here to learn the code:** how it works, file by file. |
| `PLAN.md` | Game design, open questions, what is done and what is next. |
| `IMAGE_PROMPTS.md` | Ready-to-paste Gemini prompts for the teacher's mood pictures (which image to upload, what to save it as). |
| `NOTES.md` | Update log: what changed in each commit and why. |
| `CLAUDE.md` | Rules for changing the code (read automatically by Claude Code). |
| `requirements.txt` | Libraries to install. |

## Libraries

- [OpenCV](https://opencv.org/) for the webcam
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) for finding the face and body
- [pygame-ce](https://pyga.me/) for the game window, drawing and sound
- [NumPy](https://numpy.org/) for generating the sounds
