"""
All the numbers that tune the game, in one place.

Change a value here, save, and run the game again. No other file needs to
change. Each value says its unit (seconds, degrees, pixels).
"""

# --- Webcam ---
CAMERA_INDEX = 0            # 0 = first webcam; try 1 if the wrong one opens
CAMERA_FALLBACK_INDICES = (1,)  # tried only before the first working camera is found; () disables fallback
CAMERA_WARMUP_TIME = 3.0     # seconds to wait for a newly opened camera's first picture
CAMERA_STALE_TIME = 0.5      # seconds; older pictures pause the game instead of pretending to be live
CAMERA_RECONNECT_TIME = 1.0  # seconds without a good picture before reopening the same camera
CAMERA_RETRY_INTERVAL = 0.5  # seconds between open/reconnect attempts
CAMERA_READ_RETRY = 0.05     # seconds between failed frame reads (avoid a busy loop)
CAMERA_STOP_TIMEOUT = 1.0    # seconds to wait for the reader on exit; some drivers block in read()
FACE_MODEL_FILE = "face_landmarker.task"

# --- Face finding ---
MIN_FACE_CONFIDENCE = 0.4   # 0..1; lower keeps the face longer while turning, but may see faces that aren't there
FACE_LOST_GRACE = 0.6       # seconds the face may vanish before the game pauses (it often vanishes mid-turn)
LOST_DOWN_PITCH = 8         # degrees; face vanished while tilted at least this far down → counts as DOWN

# --- Head direction (degrees, measured from the calibrated "screen" angle) ---
YAW_THRESHOLD = 18          # turn this far left/right → LEFT/RIGHT
PITCH_DOWN_THRESHOLD = 23   # tilt this far down → DOWN
YAW_SIGN = 1                # set to -1 if LEFT and RIGHT come out swapped
PITCH_SIGN = 1              # set to -1 if looking UP is detected as DOWN
SMOOTHING = 0.8             # 0..1, lower = steadier but slower
HOLD_TIME = 0.1             # seconds a new direction must last before it counts
CALIBRATION_TIME = 2.0      # seconds the player looks at the screen at the start

# --- Menus (head control; degrees are measured from the calibrated screen angle) ---
MENU_PITCH_THRESHOLD = 12   # degrees; tilt up/down this far → move the selection up/down
MENU_YAW_THRESHOLD = 18     # degrees; turn right → select, turn left → back
MENU_MOVE_HOLD = 0.15       # seconds a tilt must last before the selection moves
MENU_REPEAT_TIME = 0.6      # seconds between moves while the tilt is held
MENU_SELECT_TIME = 0.8      # seconds a turn must be held to select / go back
HEAD_PAUSE_AFTER_KEYS = 1.0 # seconds head control is off in the menus after a key press or click
EXAM_TIME_CHOICES = (60, 90, 120, 200)  # seconds; the exam times the settings menu cycles through
LOADING_TIME = 3.0          # seconds the "get ready" screen is shown before each game (above 0)
LOADING_JUMPS = 5           # how many times the loading bar jumps forward (it is stuck in between)
LOADING_STALL = 0.6         # 0..1; part of the time between two jumps the bar is stuck

# --- Disclaimer (the "official notice" when the game opens) ---
NOTICE_TYPE_DELAY = 0.6     # seconds before the typing starts (the paper slides in first)
NOTICE_TYPE_SPEED = 45      # letters per second the notice is typed
NOTICE_SIGN_TIME = 0.7      # seconds the signature takes to write; then the stamp comes down
NOTICE_STAMP_HOLD = 1.3     # seconds the stamped paper stays before the game goes on

# --- Window ---
WINDOW_WIDTH = 960          # pixels
WINDOW_HEIGHT = 600         # pixels
FULLSCREEN = False          # True = start as a borderless window covering the screen (F11 toggles)
MAXIMIZED = True            # True = the normal window starts maximized (title bar and taskbar stay visible)
SMOOTH_SCALING = True       # True = stretch the 960x600 picture to the window smoothly (less blocky on big screens)
FPS = 30                    # frames per second the game tries to run at

# --- Rules ---
ANSWERS_NEEDED = 5          # questions on the exam; write all of them to hand it in
PAPER_FOCUS_TIME = 2.5      # seconds of looking at a neighbour, without looking away, until their paper is sharp (read)
STARE_GRACE_TIME = 2.0      # seconds you may look at the screen for free
STARE_FILL_TIME = 1.0       # seconds after the grace time until a warning
MAX_WARNINGS = 3            # this many warnings = game over
POPUP_TIME = 2.0            # seconds a popup stays on screen
WARNING_SCENE_TIME = 2.5    # seconds the teacher comes over and points at you after a warning; the game is frozen
TEACHER_APPROACH_TIME = 0.8 # seconds of that scene the teacher takes to walk up to your desk
CAUGHT_SCENE_TIME = 4.0     # seconds of the "caught" scene: the "!", then the teacher tears up your exam
CAUGHT_EXCLAIM_TIME = 1.2   # seconds of that scene the "!" is shown before he tears the paper
GAME_OVER_TIME = 8.0        # seconds of the game over screen (the two logos talking); Space skips it
EXAM_TIME = 200              # seconds; run out before all answers are filled = lose

# --- Score (only for a handed-in exam; losing scores 0) ---
SCORE_PER_CORRECT = 1000    # points for each right answer
SCORE_TIME_BONUS = 1000     # points if no time was used at all; less the more time used (by the share of the exam time)
SCORE_PER_CLOSE_CALL = 150  # points each time the teacher saw you copying and you looked away in time
SCORE_PER_WARNING = 300     # points taken off for each warning
HIGH_SCORE_FILE = "highscore.json"  # where the best score is kept (next to main.py)

# --- Teacher ---
# (min, max) seconds for each teacher state; each time a random value in between is used.
TEACHER_DURATIONS = {
    "BUSY": (3.5, 6.5),     # erasing the board or on the phone: safe to copy
    "TURNING": (0.2, 0.2),  # about to look up (warning sound): last chance to stop copying
    "WATCHING": (4.0, 7.0), # looking at the class: copying now = caught
}
MOVE_CHANCE = 0.4           # 0..1; chance the teacher goes to the other place (board/desk) after watching
CAUGHT_GRACE = 0.1          # seconds into WATCHING before looking sideways starts the suspicion bar
CAUGHT_TIME = 0.7           # seconds of being seen copying until caught; look away before it to escape
STARE_ONLY_WHEN_FACING = True  # staring only fills the suspicion bar while the teacher is watching
SUSPICION_DRAIN_TIME = 10.0  # seconds for a full suspicion bar to empty while you do nothing suspicious

# --- Classroom view ---
FADE_TIME = 0.15            # seconds for the classroom to fade in from black when you look at the screen (above 0)
CLASSROOM_TOP = 250         # pixels; how much of the (scaled) image's top is cut off to fit the window
