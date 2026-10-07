# Visual Tracking Game

A webcam game controlled by the player's body, written only in Python and its
libraries. ME461 group project by **Glitch Please**.

## Status

**Playable.** The game reads which way your head is pointing (down at the
paper, at the screen, or to the side). Copy answers from your neighbour while
the teacher is busy, without getting caught, staring too long, or running
out of time. The classroom pictures are in; the teacher's turning sound and
the game-over sound are real files, the other sounds are still beeps made in
code. Next: playtesting, more sounds and art (see `PLAN.md` section 8).

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
CONTROL" again). In **Settings** you can change the exam time (60 / 90 / 120 /
200 s), turn the sound off, switch fullscreen, or calibrate again. Choose
**Play**: a 3-second "chapter" screen ("The Quiz", today's date, a funny
loading line) gives you time to sit straight, then the exam starts:

| Head | Option | What happens |
|---|---|---|
| Down | 1 - paper | Safe. You see your own paper, not the teacher, and hear nothing. Press **A, B, C or D** to write the answer you read. |
| At the screen | 2 - teacher | The only way to see the classroom and what the teacher is doing. While the teacher looks at the class, the suspicion bar fills; after 3 s it turns red, and when it is full you get a warning: the teacher walks up to your desk and points at you angrily (the game stops for 2.5 s while this happens). 3 warnings = game over. Being seen copying fills the same bar, so staring afterwards carries on from there. The bar never jumps to empty: it drains slowly while you do nothing suspicious. |
| Left / right | 3 - copy | Hold 5 s to read the neighbour's answer (ticking sound): a letter, or **?** if they don't know it (then the other neighbour does). Remember it, look down and write it. Write all 5 to hand in the exam; the end screen shows how many are right. You see the neighbour's paper, not the teacher. If the teacher is looking at the class, an **alarm** plays and the suspicion bar fills in 0.9 s: look away before it is full, or you are **caught**. Copying does not move forward while the teacher sees you. |

The teacher erases the board or plays on the phone (safe), then looks at the
class for a few seconds (danger). **Luigi's "hmm"** means the teacher is
about to look up: stop copying. There is no sound when they are busy again:
look at the screen to find out. While you look down at the paper you hear
**nothing** from the teacher: look up to find out what they are doing.
You have 60 seconds.

Losing by being caught or by 3 warnings plays the Metal Gear alert; running
out of time plays falling notes. When you are caught, a red Metal Gear "!"
pops up over the teacher, then he tears up your exam. After every loss comes
a GAME OVER screen where the Gemini and Claude logos make fun of you (Space
skips it), then the end menu.

When the game is over, the end screen shows the result and a small menu
(Play again, Main menu, Quit), controlled the same way.

Keys: Space calibrate, `a`/`b`/`c`/`d` write an answer (while looking at
your paper), `q` quit (Esc quits in the game and on the main menu, and goes
back in the other menus), `r` restart, `m` main menu, `k` recalibrate, F11
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

The old body tracker still runs with `.venv/bin/python tracker.py`.

## How it works

Each webcam frame: grab it with OpenCV, find the face with MediaPipe and work
out the head direction (`head_tracker.py`), move the teacher (`teacher.py`)
and the game rules (`game.py`) forward, play sounds for what happened
(`sounds.py`), and draw the screen with pygame (`render.py`). `main.py` runs
the loop. `LEARN.md` explains every file.

## Tests

```
.venv/bin/python -m unittest discover -s tests -v
```

## Files

| File | Purpose |
|---|---|
| `main.py` | The game: main loop and screens. |
| `menu.py` | Menus: the selected item, and head tilts/turns → up/down/select/back; the loading bar's uneven fill. |
| `disclaimer.py` | The opening notice: typing, signing, the stamp (no drawing). |
| `glitch_intro.py` | Our team's "Glitch Please" intro. One file, only needs pygame: copy it into any project. |
| `head_tracker.py` | Webcam frame → head direction (DOWN / SCREEN / LEFT / RIGHT). |
| `camera.py` | Reads the webcam in the background. |
| `game.py` | Game rules. No drawing. |
| `teacher.py` | The teacher: busy, turning, watching; at the board or the desk. |
| `render.py` | All drawing. |
| `sounds.py` | Sound effects: beeps made in code, some replaced by files. |
| `settings.py` | Every tuning number in one place. |
| `tests/` | Unit tests for the rules, the tracker and the menus. |
| `run.sh` | Launcher. |
| `face_landmarker.task` | Pre-trained MediaPipe face model. |
| `tracker.py` | The first body tracker, kept for reference. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model, used by `tracker.py`. |
| `assets/images/` | The four classroom pictures, plus the three look-away pictures (`classroom_desk_looking_down/left/right`) and each neighbour's paper with a letter (`left_A` … `left_D`, `left_unknown` = "?", same for `right_`), the teacher pointing at you after a warning (`classroom_warning`) (`original/`: as made by Gemini, before sharpening). |
| `assets/sounds/` | Sound files (Luigi "hmm", MGS alert, chalk erasing for later). |
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
