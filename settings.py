"""
All the numbers that tune the game, in one place.

Change a value here, save, and run the game again. No other file needs to
change. Each value says its unit (seconds, degrees, pixels).
"""

# --- Webcam ---
CAMERA_INDEX = 0            # 0 = first webcam; try 1 if the wrong one opens
FACE_MODEL_FILE = "face_landmarker.task"

# --- Face finding ---
MIN_FACE_CONFIDENCE = 0.3   # 0..1; lower keeps the face longer while turning, but may see faces that aren't there
FACE_LOST_GRACE = 0.6       # seconds the face may vanish before the game pauses (it often vanishes mid-turn)
LOST_DOWN_PITCH = 8         # degrees; face vanished while tilted at least this far down → counts as DOWN

# --- Head direction (degrees, measured from the calibrated "screen" angle) ---
YAW_THRESHOLD = 18          # turn this far left/right → LEFT/RIGHT
PITCH_DOWN_THRESHOLD = 28   # tilt this far down → DOWN
YAW_SIGN = 1                # set to -1 if LEFT and RIGHT come out swapped
PITCH_SIGN = 1              # set to -1 if looking UP is detected as DOWN
SMOOTHING = 0.8             # 0..1, lower = steadier but slower
HOLD_TIME = 0.1             # seconds a new direction must last before it counts
CALIBRATION_TIME = 2.0      # seconds the player looks at the screen at the start

# --- Window ---
WINDOW_WIDTH = 960          # pixels
WINDOW_HEIGHT = 600         # pixels
FPS = 30                    # frames per second the game tries to run at

# --- Rules ---
ANSWERS_NEEDED = 5          # answers to fill to win
COPY_TIME = 3.0             # seconds of looking sideways to fill one answer
STARE_GRACE_TIME = 3.0      # seconds you may look at the screen for free
STARE_FILL_TIME = 2.0       # seconds after the grace time until a warning
MAX_WARNINGS = 3            # this many warnings = game over
POPUP_TIME = 2.0            # seconds a popup stays on screen
TICK_INTERVAL = 0.3         # seconds between tick sounds while copying
EXAM_TIME = 60              # seconds; run out before all answers are filled = lose

# --- Teacher ---
# (min, max) seconds for each teacher state; each time a random value in between is used.
TEACHER_DURATIONS = {
    "BUSY": (3.5, 6.5),     # erasing the board or on the phone: safe to copy
    "TURNING": (0.2, 0.2),  # about to look up (warning sound): last chance to stop copying
    "WATCHING": (4.0, 7.0), # looking at the class: copying now = caught
}
MOVE_CHANCE = 0.4           # 0..1; chance the teacher goes to the other place (board/desk) after watching
CAUGHT_GRACE = 0.1          # seconds into WATCHING before looking sideways starts the suspicion bar
CAUGHT_TIME = 0.9           # seconds of being seen copying until caught; look away before it to escape
STARE_ONLY_WHEN_FACING = True  # staring only fills the suspicion bar while the teacher is watching
SUSPICION_DRAIN_TIME = 8.0  # seconds for a full suspicion bar to empty while you do nothing suspicious

# --- Classroom view ---
FADE_TIME = 0.15            # seconds for the classroom to fade in from black when you look at the screen (above 0)
CLASSROOM_TOP = 250         # pixels; how much of the (scaled) image's top is cut off to fit the window
