"""
All the numbers that tune the game, in one place.

Change a value here, save, and run the game again. No other file needs to
change. Each value says its unit (seconds, degrees, pixels).
"""

# --- Webcam ---
CAMERA_INDEX = 0            # 0 = first webcam; try 1 if the wrong one opens
WINDOWS_DIRECTSHOW = True   # Windows only: False = use Windows' default camera system instead
FACE_MODEL_FILE = "face_landmarker.task"

# --- Face finding ---
MIN_FACE_CONFIDENCE = 0.3   # 0..1; lower keeps the face longer while turning, but may see faces that aren't there
FACE_LOST_GRACE = 0.6       # seconds the face may vanish before the game pauses (it often vanishes mid-turn)
LOST_DOWN_PITCH = 8         # degrees; face vanished while tilted at least this far down → counts as DOWN

# --- Head direction (degrees, measured from the calibrated "screen" angle) ---
YAW_THRESHOLD = 25          # turn this far left/right → LEFT/RIGHT
PITCH_DOWN_THRESHOLD = 20   # tilt this far down → DOWN
YAW_SIGN = 1                # set to -1 if LEFT and RIGHT come out swapped
PITCH_SIGN = 1              # set to -1 if looking UP is detected as DOWN
SMOOTHING = 0.4             # 0..1, lower = steadier but slower
HOLD_TIME = 0.2             # seconds a new direction must last before it counts
CALIBRATION_TIME = 2.0      # seconds the player looks at the screen at the start

# --- Window ---
WINDOW_WIDTH = 960          # pixels
WINDOW_HEIGHT = 600         # pixels
FPS = 30                    # frames per second the game tries to run at

# --- Rules ---
ANSWERS_NEEDED = 5          # answers to fill to win
COPY_TIME = 2.5             # seconds of looking sideways to fill one answer
STARE_GRACE_TIME = 3.0      # seconds you may look at the screen for free
STARE_FILL_TIME = 2.0       # seconds after the grace time until a warning
MAX_WARNINGS = 3            # this many warnings = game over
POPUP_TIME = 2.0            # seconds a popup stays on screen
TICK_INTERVAL = 0.3         # seconds between tick sounds while copying
