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

- Linux with Python 3 (developed on Ubuntu 26.04, Python 3.14)
- A webcam

## Setup

```
git clone https://github.com/nakciefe-commits/me461-python-visual-tracking-app-gp.git
cd me461-python-visual-tracking-app-gp
sudo apt install -y python3-venv
```

That's all: `run.sh` creates the `.venv` environment and installs the
libraries from `requirements.txt` the first time it runs, and again whenever
`requirements.txt` changes (for example after a `git pull`).

## Run

```
./run.sh
```

The game opens with our team's "Glitch Please" intro (any key skips it), then
a (satirical) official notice on a desk: it is typed out (Space shows it all
at once), press Space to sign it, an "APPROVED" stamp comes down and the
game goes on. Sit at the desk with the webcam on top of the monitor. The start screen shows
the webcam with the tracking drawn on your face. Sit normally, look at the
screen, and click **Calibrate** (or press Space): for 2 seconds the game learns
your "looking at the screen" position. Then the **main menu** opens (Play,
How to play, Settings, Quit). Control it with your head: **tilt up/down** to
move the selection, **turn right** and hold until the bar fills to choose,
**turn left** and hold to go back. The arrow keys, Enter, Esc and the mouse
work too; after a key press or a click the head is ignored for 1 s, so the
two do not fight (the box above the webcam shows "KEYBOARD", then "HEAD
CONTROL" again). In **Settings** you can turn the sound off, switch
fullscreen, or calibrate again. The main menu also shows the **top scores**
(the 5 best runs).

Choose **Play** to start a **run: three exams in a row**:

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
sit straight, then the exam starts:

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

**When the clock runs out**, the teacher collects your paper as it is (the
unanswered questions count as blank) and it is graded: falling notes play.
**Failing** an exam means being caught or getting 3 warnings (the Metal Gear
alert plays). When you are caught, a red Metal Gear "!" pops up over the
teacher, then he tears up your exam. After failing comes a GAME OVER screen
where the Gemini and Claude logos make fun of you, with a different joke
each time (Space skips it). A failed
exam scores 0, and the run goes on with the next exam.

**Music:** an 80s Miami theme (`assets/sounds/theme.mp3`) loops in the
menus from the start screen on (not during the intro and the notice). It
fades out while an exam loads, the exam itself is silent (you need to hear
the teacher), and it fades back in afterwards. Sound OFF in the settings
turns it off too. Every screen change is a short crossfade.

**Grading:** every question is worth one point: right **+1**, wrong
**−0.5**, blank **0**. So a blind guess is a gamble (right only one time in
four).

**He keeps an eye on you:** each exam has a hidden point on the suspicion
bar (lower each exam). Above it, the teacher does not look away: he keeps
watching you until the bar drains back under it, so you have to look at
your paper.

**Score:** after a handed-in exam the score is counted up part by part, like
in Balatro: each question's card pops in (+1000 right, −500 wrong, 0 blank),
then the **early bonus** (up to +1000, the share of the exam time you did
not use), the **close calls** (the teacher saw you copying and you looked
away in time: 100 to 500 points, the fuller the suspicion bar was the more;
above 80 % it is a "razor close" call, +300 more), **sharp eyes** (+100
each time the first paper you read for a question is the one that knows),
**NINJA!** (+1500: every answer right, no warning; **almost ninja** +500
with one warning) and −300 per warning.
Space skips the count. The exam's score is never below 0.

After the last exam, the **results** show each exam's score and the run's
total, counted up, next to the top scores. A total good enough for the top 5
lights up in the list with "NEW HIGH SCORE!", confetti and a fanfare. The
top scores are kept in `highscore.json` (each computer has its own).

Keys: Space calibrate, `a`/`b`/`c`/`d` write an answer, `s` leave it blank
(both while looking at your paper), `q` quit (Esc quits in the game and on
the main menu, and goes back in the other menus), `r` restart the run, `m`
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

To tune the head tracking, watch the yaw/pitch numbers under the webcam
preview and change the numbers in `settings.py`.

The old body tracker still runs with `.venv/bin/python old/tracker.py`.

## How it works

Each webcam frame: grab it with OpenCV (`tracking/camera.py`), find the face
with MediaPipe and work out the head direction (`tracking/head_tracker.py`),
move the teacher (`logic/teacher.py`) and the game rules (`logic/game.py`)
forward, play sounds for what happened (`ui/sounds.py`), and draw the screen
with pygame (`ui/render.py`). `main.py` runs the loop. `LEARN.md` explains
every file.

## Tests

```
.venv/bin/python -m unittest discover -s tests -v
```

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
| `ui/sounds.py` | Sound effects: beeps made in code, some replaced by files. |
| `ui/glitch_intro.py` | Our team's "Glitch Please" intro. One file, only needs pygame: copy it into any project. |
| `tests/` | Unit tests for the rules, the tracker and the menus. |
| `old/tracker.py` | The first body tracker, kept for reference. |
| `run.sh` | Launcher. |
| `face_landmarker.task` | Pre-trained MediaPipe face model. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model, used by `old/tracker.py`. |
| `assets/images/` | The four classroom pictures, plus the three look-away pictures (`classroom_desk_looking_down/left/right`) and each neighbour's paper with a letter (`left_A` … `left_D`, `left_unknown` = "?", same for `right_`), the teacher pointing at you after a warning (`classroom_warning`) (`original/`: as made by Gemini, before sharpening). |
| `assets/sounds/` | Sound files (Luigi "hmm", MGS alert, chalk erasing for later) and `theme.mp3`, the background music. |
| `LEARN.md` | **Start here to learn the code:** how it works, file by file. |
| `PLAN.md` | Game design, open questions, what is done and what is next. |
| `NOTES.md` | Update log: what changed in each commit and why. |
| `CLAUDE.md` | Rules for changing the code (read automatically by Claude Code). |
| `requirements.txt` | Libraries to install. |

## Libraries

- [OpenCV](https://opencv.org/) for the webcam
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) for finding the face and body
- [pygame-ce](https://pyga.me/) for the game window, drawing and sound
- [NumPy](https://numpy.org/) for generating the sounds
