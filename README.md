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

- Linux or Windows with Python 3 (developed on Ubuntu 26.04, Python 3.14;
  on Windows, Python 3.12 is the safest choice, see below)
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

**Windows:** install Python from [python.org](https://www.python.org/downloads/)
(tick "Add python.exe to PATH") and clone the repository; `python3-venv` is
not needed. `run.bat` does the same job as `run.sh`. If installing the
libraries fails because MediaPipe has no package for your Python version,
install Python 3.12, delete the `.venv` folder and run `run.bat` again.

## Run

```
./run.sh
```

On Windows, double-click `run.bat` (or type `run.bat` in a terminal in the
project folder).

Sit at the desk with the webcam on top of the monitor. The start screen shows
the webcam with the tracking drawn on your face. Sit normally, look at the
screen, and click **Calibrate** (or press Space): for 2 seconds the game learns
your "looking at the screen" position. Then:

| Head | Option | What happens |
|---|---|---|
| Down | 1 - paper | Safe. The screen is black. |
| At the screen | 2 - teacher | The only way to see the classroom and what the teacher is doing. While the teacher looks at the class, the suspicion bar fills; after 3 s it turns red, and when it is full you get a warning. 3 warnings = game over. Being seen copying fills the same bar, so staring afterwards carries on from there. The bar never jumps to empty: it drains slowly while you do nothing suspicious. |
| Left / right | 3 - copy | Hold 3 s to fill one answer (ticking sound). Fill 5 to win. The screen is black. If the teacher is looking at the class, an **alarm** plays and the suspicion bar fills in 0.9 s: look away before it is full, or you are **caught**. Copying does not move forward while the teacher sees you. |

The teacher erases the board or plays on the phone (safe), then looks at the
class for a few seconds (danger). **Luigi's "hmm"** means the teacher is
about to look up: stop copying. There is no sound when they are busy again:
look at the screen to find out. While you look down at the paper you hear
**nothing** from the teacher: look up to find out what they are doing.
You have 60 seconds.

Losing by being caught or by 3 warnings plays the Metal Gear alert; running
out of time plays falling notes.

Keys: Space calibrate, `q`/Esc quit, `r` restart, `c` recalibrate, `d`
always show the classroom and the teacher's state (for testing). If no face
is seen for more than 0.6 s the game pauses, unless your head was going down:
then you are looking at the paper (the camera can't see your face then), and
the game carries on. You don't need to turn your head
far: 18° counts as looking to the side, and a face turned too far away is hard
to track.

To tune the head tracking, watch the yaw/pitch numbers under the webcam
preview and change the numbers in `settings.py`.

The old body tracker still runs with `.venv/bin/python tracker.py`
(Windows: `.venv\Scripts\python tracker.py`).

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

On Windows: `.venv\Scripts\python -m unittest discover -s tests -v`

## Files

| File | Purpose |
|---|---|
| `main.py` | The game: main loop and screens. |
| `head_tracker.py` | Webcam frame → head direction (DOWN / SCREEN / LEFT / RIGHT). |
| `camera.py` | Reads the webcam in the background. |
| `game.py` | Game rules. No drawing. |
| `teacher.py` | The teacher: busy, turning, watching; at the board or the desk. |
| `render.py` | All drawing. |
| `sounds.py` | Sound effects: beeps made in code, some replaced by files. |
| `settings.py` | Every tuning number in one place. |
| `tests/` | Unit tests for the rules and the tracker. |
| `run.sh` | Launcher (Linux). |
| `run.bat` | Launcher (Windows). |
| `.gitattributes` | Keeps Windows line endings in `run.bat`. |
| `face_landmarker.task` | Pre-trained MediaPipe face model. |
| `tracker.py` | The first body tracker, kept for reference. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model, used by `tracker.py`. |
| `assets/images/` | The four classroom pictures (`original/`: as made by Gemini, before sharpening). |
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
