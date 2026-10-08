"""
Packs the game into one program that runs without Python: a .exe on
Windows (a plain program on Linux). Uses PyInstaller, a build tool (not a
game library): install it only to build, with
    pip install pyinstaller
then run, from the project folder:
    python packaging/build_exe.py
The result is in dist/, e.g. dist/DontGetCaught-0.1-beta.exe. It holds
Python, the libraries (OpenCV, MediaPipe, pygame), the pictures, the sounds
and the face model, so the player only needs a webcam: double-click it.

Windows .exe files must be built on Windows: the GitHub workflow
.github/workflows/build-windows.yml does it on GitHub's Windows computers.
"""

import os
import sys

import PyInstaller.__main__

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # the project folder
sys.path.insert(0, ROOT)
from settings import GAME_VERSION   # noqa: E402  (needs ROOT on the path first)

NAME = "DontGetCaught-" + GAME_VERSION.replace(" ", "-")   # e.g. DontGetCaught-0.1-beta


def data(source, target):
    """'Put this file or folder there inside the program' (PyInstaller's --add-data)."""
    return ["--add-data", f"{os.path.join(ROOT, source)}{os.pathsep}{target}"]


PyInstaller.__main__.run([
    os.path.join(ROOT, "main.py"),
    "--name", NAME,
    "--onefile",        # one single file to hand out
    "--windowed",       # no black console window behind the game
    "--noconfirm",
    *data("assets", "assets"),
    *data("face_landmarker.task", "."),
    "--collect-all", "mediapipe",   # MediaPipe loads parts of itself at run time; take all of it
    "--distpath", os.path.join(ROOT, "dist"),
    "--workpath", os.path.join(ROOT, "packaging", "work"),
    "--specpath", os.path.join(ROOT, "packaging", "work"),
])
