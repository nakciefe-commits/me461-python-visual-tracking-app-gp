# Visual Tracking Game

A webcam game controlled by the player's body, written only in Python and its
libraries. ME461 group project by **Glitch Please**.

## Status

**Demo stage.** The game reads which way your head is pointing (down at the
paper, at the screen, or to the side) and runs the copying and staring rules,
with simple shapes and generated sounds instead of art. The teacher, real art
and sounds are next. See `PLAN.md` for the design and `STEPS.md` for the build
steps.

## Requirements

- **Linux** (developed on Ubuntu 26.04, Python 3.14) or **Windows 10/11**
  (64-bit Python 3.10 or newer)
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
sudo apt install -y python3-venv     # once per computer
./run.sh
```

### Windows

1. Install **Python 3** (64-bit) from <https://www.python.org/downloads/>.
   In the installer, tick **"Add python.exe to PATH"**.
2. Get the code: `git clone` as above (or GitHub → Code → Download ZIP, and
   unzip it).
3. Double-click **`run.bat`** in the project folder.

Run the game natively on Windows, not in WSL or a Linux virtual machine:
the webcam does not work there without extra setup.

**Webcam not working?** See "If the webcam doesn't work" in `NOTES.md`.

## Playing

Sit at the desk with the webcam on top of the monitor. The start screen shows
the webcam with the tracking drawn on your face. Sit normally, look at the
screen, and click **Calibrate** (or press Space): for 2 seconds the game learns
your "looking at the screen" position. Then:

| Head | Option | What happens |
|---|---|---|
| Down | 1 - paper | Safe. |
| At the screen | 2 - teacher | The suspicion bar fills; after 3 s it turns red, and when it is full you get a warning. 3 warnings = game over. |
| Left / right | 3 - copy | Hold 2.5 s to fill one answer (ticking sound). Fill 5 to win. |

Keys: Space calibrate, `q`/Esc quit, `r` restart, `c` recalibrate. If no face
is seen for more than 0.6 s the game pauses, unless your head was going down:
then you are looking at the paper (the camera can't see your face then), and
the game carries on. You don't need to turn your head
far: 25° counts as looking to the side, and a face turned too far away is hard
to track.

To tune the head tracking, watch the yaw/pitch numbers under the webcam
preview and change the numbers in `settings.py`.

The old body tracker still runs with `.venv/bin/python tracker.py`.

## How it works

Each webcam frame: grab it with OpenCV, find the face with MediaPipe and work
out the head direction (`head_tracker.py`), move the game rules forward
(`game.py`), play sounds for what happened (`sounds.py`), and draw the screen
with pygame (`render.py`). `main.py` runs the loop.

## Tests

```
.venv/bin/python -m unittest discover -s tests -v
```

## Files

| File | Purpose |
|---|---|
| `main.py` | The game: main loop and screens. |
| `head_tracker.py` | Webcam frame → head direction (DOWN / SCREEN / LEFT / RIGHT). |
| `camera.py` | Reads the webcam in the background. |
| `game.py` | Game rules. No drawing. |
| `render.py` | All drawing. |
| `sounds.py` | Sound effects (generated in code for now). |
| `settings.py` | Every tuning number in one place. |
| `tests/` | Unit tests for the rules and the tracker. |
| `run.sh` / `run.bat` | Launcher for Linux / Windows. |
| `face_landmarker.task` | Pre-trained MediaPipe face model. |
| `tracker.py` | The first body tracker, kept for reference. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model, used by `tracker.py`. |
| `assets/` | Images and sounds (empty for now). |
| `LEARN.md` | **Start here to learn the code:** how it works, file by file. |
| `PLAN.md` | Game design, demo spec and future ideas. |
| `STEPS.md` | Step-by-step build instructions. |
| `requirements.txt` | Libraries to install. |
| `NOTES.md` | Update log: what changed in each commit and why. |

## Libraries

- [OpenCV](https://opencv.org/) for the webcam
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) for finding the face and body
- [pygame-ce](https://pyga.me/) for the game window, drawing and sound
- [NumPy](https://numpy.org/) for generating the sounds
