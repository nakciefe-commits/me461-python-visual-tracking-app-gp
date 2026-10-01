# Update notes

ME461 group project by Glitch Please: a visual tracking game written only in
Python and its libraries.

This file is the project's update log. Every commit gets one entry, numbered in
order, newest at the bottom. Read it top to bottom to learn what exists and why.

**Adding an entry:** copy the headings of the last entry, use the next commit
number and today's date, and describe what changed, not how you felt about it.

## Setup and run

```
sudo apt install -y python3-venv            # once per computer, Ubuntu
python3 -m venv .venv                       # create the project's own Python environment
.venv/bin/pip install -r requirements.txt   # install the libraries into it
./run.sh                                    # start the program
```

Quit with `q`, Esc, or the window's X button. The video window must be selected
for the keys to work.

---

## Commit #1 — Added simple body tracker

- **Date:** 30 Sep 2026
- **Hash:** `e99a82a`

### Summary

A program that opens the webcam, finds 33 body joints and draws them as a
skeleton on the live video. Measured at about 25 frames per second on a 640x480
webcam. The game itself is not designed yet; this is the tracking base it will
be built on.

### Added

| File | Purpose |
|---|---|
| `tracker.py` | The program. |
| `run.sh` | Launcher: runs `tracker.py` with the Python in `.venv`. |
| `pose_landmarker.task` | Pre-trained MediaPipe pose model (the "full" variant), downloaded from Google. |
| `requirements.txt` | Libraries to install: `opencv-python`, `mediapipe`. |
| `.gitignore` | Keeps `.venv/` and `__pycache__/` out of the repository. |

### How it works

`main()` in `tracker.py` runs one loop, once per webcam frame:

1. `camera.read()` grabs a frame.
2. `find_joints()` passes the frame to MediaPipe and returns 33 joints, or
   `None` if no person is seen. Each joint has `x` and `y` (0.0 to 1.0 across
   the frame, `y = 0` at the top) and `visibility` (0.0 to 1.0).
3. `draw_skeleton()` converts the positions to pixels and draws the bones
   listed in `BONES` as lines and the joints as dots. Joints with visibility
   below `MIN_VISIBILITY` (0.5) are skipped.
4. The frame is mirrored, the FPS counter is drawn, and the frame is shown.

### Details worth knowing

- Joints are addressed by name through `J`, for example `joints[J.LEFT_WRIST]`.
- MediaPipe 1.0 has only the `mediapipe.tasks` API; the older
  `mediapipe.solutions` API used in most online tutorials does not exist in it.
- The detector runs in `VIDEO` mode and needs a timestamp in milliseconds that
  increases with every frame.
- OpenCV frames are BGR and MediaPipe expects RGB, so `find_joints()` converts.
- The frame is mirrored after detection. Mirroring before would swap the left
  and right joint labels.
- Text is drawn after mirroring, otherwise it would be mirrored too.
- The loop checks whether the window is still visible, because OpenCV reopens
  a closed window on the next `imshow` call.
- Set `CAMERA_INDEX` to 1 if the wrong camera opens.

---

## Commit #2 — Added update notes and README

- **Date:** 30 Sep 2026
- **Hash:** `604ed6f`

### Summary

Added the project's documentation. No code changed.

### Added

| File | Purpose |
|---|---|
| `NOTES.md` | Update log with one entry per commit, plus setup and run instructions. |
| `README.md` | The repository's front page: what the project is, who made it, how to set it up and run it. |

---

## Commit #3 — Fixed OpenCV package conflict

- **Date:** 1 Oct 2026

### Summary

The project installed two OpenCV packages that overwrite each other. It now
installs only one. No code changed.

### Changed

| File | Change |
|---|---|
| `requirements.txt` | `opencv-python` replaced with `opencv-contrib-python`. |

### The problem

`requirements.txt` asked for `opencv-python`, but `mediapipe` needs
`opencv-contrib-python`, so pip installed both. The two are the same OpenCV
library: `opencv-contrib-python` is the main package plus extra modules. Both
install into the same `cv2/` folder and share 41 files there, so whichever was
installed last overwrote the other's files. Pip does not warn about this
because the packages have different names.

It worked only because both were the same version. It breaks when:

- one of them is upgraded and the other is not, leaving a `cv2/` folder with
  files from two versions;
- one of them is uninstalled, which deletes the shared files and breaks `cv2`
  for the other one too.

### Details worth knowing

- `opencv-contrib-python` includes everything in `opencv-python`, so the code
  did not need to change.
- Do not add `opencv-python` (or any other OpenCV package) to
  `requirements.txt` again.
- **If you set up `.venv` before this commit**, uninstall both packages, then
  reinstall. Uninstalling only one breaks the other:

  ```
  .venv/bin/pip uninstall -y opencv-python opencv-contrib-python
  .venv/bin/pip install -r requirements.txt
  .venv/bin/python -c "import cv2; print(cv2.__version__)"   # should print a version
  ```
