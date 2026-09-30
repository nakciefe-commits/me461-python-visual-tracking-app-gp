# Visual Tracking Game

A webcam game controlled by the player's body, written only in Python and its
libraries. ME461 group project by **Glitch Please**.

## Status

The body tracker is working: the program opens the webcam, finds 33 body joints
and draws them as a live skeleton, at about 25 frames per second. The game
built on top of it is still to come.

## Requirements

- Linux with Python 3 (developed on Ubuntu 26.04, Python 3.14)
- A webcam

## Setup

```
git clone https://github.com/nakciefe-commits/me461-python-visual-tracking-app-gp.git
cd me461-python-visual-tracking-app-gp
sudo apt install -y python3-venv
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Run

```
./run.sh
```

Stand far enough back for the camera to see your whole body. Quit with `q`,
Esc, or the window's X button.

## How it works

Each webcam frame goes through four steps: grab the frame, find the joints with
MediaPipe, draw the skeleton with OpenCV, show the mirrored result. The code is
in `tracker.py`, with a comment on every step.

## Files

| File | Purpose |
|---|---|
| `tracker.py` | The program. |
| `run.sh` | Launcher. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model. |
| `requirements.txt` | Libraries to install. |
| `NOTES.md` | Update log: what changed in each commit and why. |

## Libraries

- [OpenCV](https://opencv.org/) for the webcam, drawing and the window
- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) for finding the body joints
