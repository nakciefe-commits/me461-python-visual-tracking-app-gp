# Visual Tracking Game — Exam Paper Edition

A webcam game controlled by the player's body, written only in Python and its
libraries. ME461 group project by **Glitch Please**.

## Status

**Playable.** This folder is a complete copy of `me461-python-visual-tracking-app-gp`
with a new exam paper mechanic. Look left or right to see a neighbour's marked
paper. Only the current question is visible and it slowly clears from blur;
look down to see your own paper and press A, B, C, D or E to write an
answer. Each paper has numbered questions with placeholder lines and five
options. The existing teacher, classroom assets, sounds and head tracking are
included. Complete all five answers correctly before the 90-second timer ends.

## Yeni dinamik ve kontroller

- **Öne bak:** öğretmeni ve sınıfı gör; kendi sınav kâğıdın gizlidir.
- **Sağa / sola bak:** önce yalnızca `1. soru` görünür. Komşunun kâğıdı bulanık
  başlar; aynı tarafa bakarken 2,5 saniyede netleşir. Başka yöne bakınca,
  taraf değiştirince veya kamera takibi durunca yeniden bulanık başlar.
- **Başını aşağı eğ:** kendi sınav kâğıdını net gör; `a b c d e` ile seçili
  soruyu cevapla. Komşuda artık sıradaki seçili soru görünür (2. soru, 3. soru…).
- Cevaptan sonra sıradaki boş soru seçilir. `↑ / ↓` ile önceki soruları seçip
  cevaplarını değiştirebilirsin. İşaretler kendi kâğıdında kalır.
- İki komşu aynı sınavın doğru cevaplarını gösterir. Cevaplar oyun boyunca
  sabittir; yeni oyunda yeniden üretilir. Yanlış cevapları düzelterek kazanabilirsin.
- `F2`: yeniden kalibre et. `F3`: öğretmenin durumunu göster (test).
  `C` ve `D` artık cevap şıklarıdır.
- `R`: yeniden başlat. `Q / Esc`: çık. `F11`: tam ekran.

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

For this updated copy, open a terminal in `me461-python-visual-tracking-app2-gp`:

```
./run.sh
```

The game opens with a (satirical) warning screen; press Space or click to go
on. Sit at the desk with the webcam on top of the monitor. The start screen shows
the webcam with the tracking drawn on your face. Sit normally, look at the
screen, and click **Calibrate** (or press Space): for 2 seconds the game learns
your "looking at the screen" position. Then:

| Head | Option | What happens |
|---|---|---|
| Down | 1 - paper | Safe. Your own full paper is visible; A..E marks the selected question. You cannot see or hear the teacher. |
| At the screen | 2 - teacher | The classroom is visible; your own paper is hidden. Existing A..E input still works, but look down to inspect the marks. While the teacher faces the class, suspicion fills: yellow for 2 s, then red for 1 s; full gives a warning. 3 warnings = game over. |
| Left / right | 3 - neighbour | Only the selected question is shown, initially Q1. The paper starts blurred and becomes sharp after 2.5 seconds of continuous looking at the same neighbour. Looking away, switching sides or tracking pauses reset focus. While the teacher watches, an **alarm** plays and suspicion fills in 0.7 s. |

The teacher erases the board or plays on the phone (safe), then looks at the
class for a few seconds (danger). **Luigi's "hmm"** means the teacher is
about to look up: stop copying. There is no sound when they are busy again:
look at the screen to find out. While you look down at the paper you hear
**nothing** from the teacher: look up to find out what they are doing.
You have 90 seconds. Merely looking sideways never fills your own answers.
The selected row is highlighted. A..E automatically advances to the next
blank question; Up / Down lets you revise any question. If a full paper has
wrong answers, a message asks you to check them. All five correct marks win;
the end screen shows the final score.

Losing by being caught or by 3 warnings plays the Metal Gear alert; running
out of time plays falling notes.

Keys: Space calibrate, A..E answer, Up / Down select question, `q`/Esc quit,
`r` restart, F2 recalibrate, F11 fullscreen on/off, F3 show the teacher's
state (for testing; the papers remain visible). The game opens as a maximized window (title bar and taskbar stay
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

`PAPER_FOCUS_TIME` changes how long a neighbour paper takes to become sharp.
`PAPER_BLUR_SIGMA` controls the initial blur strength.

## Kamera bağlantısı

Tek bir kare okunamazsa oyun kapanmaz. Kamera arka planda yeniden denenir;
0,5 saniyeden eski görüntü varsa oyun, sınav süresi ve cevap girişi duraklar.
Görüntü geri gelince devam eder. Başlangıçta `CAMERA_INDEX = 1` görüntü vermezse
`0` denenir; çalışan cihaz bulunduktan sonra yeniden bağlantı aynı cihazda kalır.
Denemeleri terminalde görebilirsin. Kamerayı kullanan diğer uygulamaları kapat;
gerekirse `CAMERA_INDEX` değerini kendi kamerana göre değiştir.
`CAMERA_FALLBACK_INDICES = ()` otomatik alternatif kamera denemesini kapatır.

The old body tracker still runs with `.venv/bin/python tracker.py`.

## How it works

Each webcam frame: grab it with OpenCV, find the face with MediaPipe and work
out the head direction (`head_tracker.py`), move the teacher (`teacher.py`)
and the game rules (`game.py`) forward, play sounds for what happened
(`sounds.py`), and draw the screen with pygame (`render.py`). `main.py` runs
the loop. Answer keys are queued until the current frame's head direction is
known, and ignored while paused, sideways, calibrating or after game over.
`LEARN.md` explains every file.

## Tests

```
.venv/bin/python -m unittest discover -s tests -v
```

## Files

| File | Purpose |
|---|---|
| `main.py` | The game: main loop and screens. |
| `head_tracker.py` | Webcam frame → head direction (DOWN / SCREEN / LEFT / RIGHT). |
| `camera.py` | Reads/retries/reconnects the webcam in the background; rejects stale images. |
| `game.py` | Exam marks, question selection, suspicion, score and game rules. No drawing. |
| `teacher.py` | The teacher: busy, turning, watching; at the board or the desk. |
| `render.py` | Classroom, desk, own paper and marked neighbour papers, drawn with pygame. |
| `sounds.py` | Sound effects: beeps made in code, some replaced by files. |
| `settings.py` | Every tuning number in one place. |
| `tests/` | 104 tests for camera recovery, rules, paper focus/rendering, keyboard/main loop, teacher and tracker. |
| `run.sh` | Launcher. |
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
