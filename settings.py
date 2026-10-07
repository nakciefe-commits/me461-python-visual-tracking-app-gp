"""
All the numbers that tune the game, in one place.

Change a value here, save, and run the game again. No other file needs to
change. Each value says its unit (seconds, degrees, pixels).
"""

# --- Webcam ---
CAMERA_INDEX = 1            # 0 = first webcam; try 1 if the wrong one opens
CAMERA_FALLBACK_INDICES = (0,)  # tried only before the first working camera is found; () disables fallback
CAMERA_WARMUP_TIME = 3.0     # seconds to wait for a newly opened camera's first picture
CAMERA_STALE_TIME = 0.5      # seconds; older pictures pause the game instead of pretending to be live
CAMERA_RECONNECT_TIME = 1.0  # seconds without a good picture before reopening the same camera
CAMERA_RETRY_INTERVAL = 0.5  # seconds between open/reconnect attempts
CAMERA_READ_RETRY = 0.05     # seconds between failed frame reads (avoid a busy loop)
CAMERA_STOP_TIMEOUT = 1.0   # seconds to wait for the reader on exit; some drivers block in read()
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

# --- Window ---
WINDOW_WIDTH = 960          # pixels
WINDOW_HEIGHT = 600         # pixels
FULLSCREEN = False          # True = start as a borderless window covering the screen (F11 toggles)
MAXIMIZED = True            # True = the normal window starts maximized (title bar and taskbar stay visible)
FPS = 30                    # frames per second the game tries to run at

# --- Rules ---
ANSWERS_NEEDED = 5          # questions to answer correctly to win
ANSWER_CHOICES = ("a", "b", "c", "d", "e")  # keyboard keys and paper options
STARE_GRACE_TIME = 2.0      # seconds you may look at the screen for free
STARE_FILL_TIME = 1.0       # seconds after the grace time until a warning
MAX_WARNINGS = 3            # this many warnings = game over
POPUP_TIME = 2.0            # seconds a popup stays on screen
EXAM_TIME = 90              # seconds; run out before all answers are correct = lose

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

# --- Exam paper (all sizes in pixels) ---
PAPER_RECT = (24, 76, 660, 432)  # full own paper when looking down
NEIGHBOUR_PAPER_RECT = (24, 128, 660, 332)  # one question when looking sideways
NEIGHBOUR_QUESTION_HEIGHT = 124  # pixels; height of the single question row
PAPER_FOCUS_TIME = 2.5       # seconds looking continuously at one neighbour until the paper is sharp
PAPER_BLUR_SIGMA = 20.0     # pixels; maximum Gaussian blur at the start of a sideways look
PAPER_BLUR_WORK_SIGMA = 3.0 # pixels; downsample large blurs to keep drawing fast
PAPER_QUESTIONS_PER_PAGE = 5  # rows; arrow keys also change pages for longer exams
PAPER_PADDING = 18
PAPER_HEADER_HEIGHT = 62
PAPER_FOOTER_HEIGHT = 32
PAPER_FONT_SIZE = 20
PAPER_SMALL_FONT_SIZE = 16
PAPER_OPTION_RADIUS = 9
PAPER_SHADOW_OFFSET = 6
PAPER_BORDER_WIDTH = 2
PAPER_CORNER_RADIUS = 8
PAPER_COLOUR = (249, 246, 232)       # RGB
PAPER_INK = (42, 53, 66)            # RGB
PAPER_LINE = (189, 183, 164)        # RGB
PAPER_ACTIVE_COLOUR = (226, 236, 247)  # RGB; selected question background
PAPER_MARK_COLOUR = (35, 91, 153)    # RGB; pen marks
DESK_COLOUR = (96, 66, 43)          # RGB
DESK_LINE_COLOUR = (111, 77, 49)    # RGB
DESK_LINE_SPACING = 48              # pixels between wooden desk lines
