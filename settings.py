"""
All the numbers that tune the game, in one place.

Change a value here, save, and run the game again. No other file needs to
change. Each value says its unit (seconds, degrees, pixels).
"""

# --- Version ---
GAME_VERSION = "0.1 beta"   # shown in the window title and on the main menu

# --- Webcam ---
CAMERA_INDEX = 0            # 0 = first webcam; try 1 if the wrong one opens
CAMERA_FALLBACK_INDICES = (1,)  # tried only before the first working camera is found; () disables fallback
CAMERA_WARMUP_TIME = 3.0     # seconds to wait for a newly opened camera's first picture
CAMERA_STALE_TIME = 0.5      # seconds; older pictures pause the game instead of pretending to be live
CAMERA_RECONNECT_TIME = 1.0  # seconds without a good picture before reopening the same camera
CAMERA_RETRY_INTERVAL = 0.5  # seconds between open/reconnect attempts
CAMERA_READ_RETRY = 0.05     # seconds between failed frame reads (avoid a busy loop)
CAMERA_STOP_TIMEOUT = 1.0    # seconds to wait for the reader on exit; some drivers block in read()
WINDOWS_DIRECTSHOW = True   # Windows only: False = use Windows' default camera system instead
FACE_MODEL_FILE = "face_landmarker.task"

# --- Face finding ---
MIN_FACE_CONFIDENCE = 0.4   # 0..1; lower keeps the face longer while turning, but may see faces that aren't there
FACE_LOST_GRACE = 0.6       # seconds the face may vanish before the game pauses (it often vanishes mid-turn)
LOST_DOWN_PITCH = 8         # degrees; face vanished while tilted at least this far down → counts as DOWN

# --- Head direction (degrees, measured from the calibrated "screen" angle) ---
# These two are used until calibration has measured the player's own poses
# (and for a pose that went the wrong way).
YAW_THRESHOLD = 18          # turn this far left/right → LEFT/RIGHT
PITCH_DOWN_THRESHOLD = 23   # tilt this far down → DOWN
YAW_SIGN = 1                # set to -1 if LEFT and RIGHT come out swapped
PITCH_SIGN = 1              # set to -1 if looking UP is detected as DOWN
SMOOTHING = 0.8             # 0..1, lower = steadier but slower
HOLD_TIME = 0.1             # seconds a new direction must last before it counts

# --- Calibration: the player shows four poses (screen, left, right, down) ---
CALIBRATION_SAMPLE_TIME = 1.0  # seconds each pose is measured after Space
CALIBRATION_SHARE = 0.6     # 0..1; a direction counts once the head is this part of the way to its pose
CALIBRATION_MIN_ANGLE = 8   # degrees; a threshold is never smaller (or the tracker's shaking would count)
CALIBRATION_MAX_ANGLE = 35  # degrees; ... nor bigger (the face is lost if you turn much further)

# --- Menus (head control; degrees are measured from the calibrated screen angle) ---
MENU_PITCH_THRESHOLD = 12   # degrees; tilt up/down this far → move the selection up/down
MENU_YAW_THRESHOLD = 18     # degrees; turn right → select, turn left → back
MENU_MOVE_HOLD = 0.15       # seconds a tilt must last before the selection moves
MENU_REPEAT_TIME = 0.6      # seconds between moves while the tilt is held
MENU_SELECT_TIME = 0.8      # seconds a turn must be held to select / go back
HEAD_PAUSE_AFTER_KEYS = 1.0 # seconds head control is off in the menus after a key press or click
LOADING_TIME = 3.0          # seconds the "get ready" screen is shown before each game (above 0)
EXAM_TITLE_TIME = 1.8       # seconds of the quick title card after it ("THE FINAL - God, please help me.")
EXAM_TAGLINE_DELAY = 0.45   # seconds into the title card before its sarcastic line slams in
LOADING_JUMPS = 5           # how many times the loading bar jumps forward (it is stuck in between)
LOADING_STALL = 0.6         # 0..1; part of the time between two jumps the bar is stuck

# --- The slot machine on the gossip screen (which mood the teacher is in) ---
SLOT_SPIN_TIME = 2.5        # seconds the reel spins before it stops on today's mood
SLOT_TURNS = 3              # how many times the reel goes all the way round (more = faster spin)
SLOT_BOUNCE = 0.35          # moods; at the end the reel goes this much too far and settles back, like a real one
SLOT_LEVER_TIME = 0.4       # seconds the lever takes to spring back up after the pull

# --- Music (assets/sounds/theme.mp3 in the menus, thrilling.mp3 in the exam; the game runs without them) ---
MUSIC_VOLUME = 0.6          # 0..1, the music's volume in the menus
EXAM_MUSIC_VOLUME = 0.35    # 0..1, the exam music's volume (quieter: the teacher's sounds must be heard)
CHALK_VOLUME = 0.5          # 0..1, the chalk sound while the teacher erases the board (it loops)
LOOP_FADE_TIME = 0.15       # seconds a looping sound (the chalk) takes to fade in or out
MUSIC_FADE_TIME = 1.5       # seconds to fade the music from silent to full volume, or back
SCREEN_FADE_TIME = 0.4      # seconds the old screen takes to fade out when the screen changes

# --- The run intro and the character screen, timed to their music ---
# (assets/sounds/character_[cut_180sec].mp3; measured from the file: 147
# beats per minute, a strong hit at the start of every bar of 4 beats from
# 0.81 s, and the "drop", where it gets twice as loud, at 11.84 s.) A
# different song needs these three numbers measured again.
CHARACTER_MUSIC_BPM = 147   # beats per minute of the character music
INTRO_FIRST_HIT = 0.81      # seconds into the music of the first strong hit (a new line slams in on each bar)
INTRO_DROP = 11.84          # seconds into the music of the drop: the intro ends, the characters slide in
CAROUSEL_SPEED = 12.0       # how fast the character carousel slides to the chosen one (higher = snappier)

# --- The guide ("How to play": Gemini and Claude teach the game, see logic/guide.py) ---
GUIDE_TYPE_SPEED = 40       # letters per second the lines are typed
GUIDE_LINE_PAUSE = 1.6      # seconds a typed line stays before the next one starts
GUIDE_STEP_PAUSE = 1.0      # seconds after a task is done before the next step
GUIDE_HOLD_TIME = 0.8       # seconds the player must hold a direction for a "look" task
GUIDE_BLIP_LETTERS = 2      # letters per talking blip while a line is typed

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
ANSWERS_NEEDED = 5          # questions on one exam when no quiz says otherwise; also the most (the paper has 5 lines)
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
EXAM_TIME = 200             # seconds of one exam when no quiz says otherwise; at 0 the paper is collected

# --- Grading the exam paper (exam points per question; any letter can be written, even unread) ---
POINTS_CORRECT = 1.0        # exam points for a right answer
POINTS_WRONG = -0.5         # exam points for a wrong answer (a wild guess costs you)
POINTS_BLANK = 0.0          # exam points for a question left blank
# The answer key is random, but without streaks ("A A A B" felt broken):
MAX_SAME_LETTER = 2         # a letter is the right answer at most this many times in one exam
MAX_SIDE_STREAK = 2         # the same neighbour knows at most this many answers in a row

# --- Score (only for a handed-in exam; losing scores 0) ---
SCORE_PER_POINT = 1000      # score for each exam point (a wrong answer takes off half of this)
SCORE_TIME_BONUS = 1000     # early hand-in bonus: points if no time was used at all; less the more time used (share of the exam time)
# A close call: the teacher saw you copying and you looked away in time. The
# fuller the suspicion bar was at that moment, the more it is worth.
CLOSE_CALL_MIN = 100        # points for getting away with an almost empty bar
CLOSE_CALL_PER_BAR = 400    # extra points for a full bar (half full = half of it)
CLOSE_CALL_EDGE = 0.8       # 0..1; getting away above this much of the bar is a "razor close" call ...
CLOSE_CALL_EDGE_BONUS = 300 # ... worth this many extra points
SCORE_PER_WARNING = 300     # points taken off for each warning
# Bonuses of a graded exam.
SCORE_NINJA = 1500          # every answer right and no warning: a perfect, silent ninja
SCORE_ALMOST_NINJA = 500    # every answer right with exactly one warning
SCORE_SHARP_EYE = 100       # each time the first paper you read for a question is the one that knows it
HIGH_SCORE_FILE = "highscore.json"  # where the top scores are kept (next to main.py)
TOP_SCORES_KEPT = 5         # how many of the best runs are kept and shown on the main menu
NAME_LETTERS = 3            # letters in a top score's name, like an arcade machine ("EFE")

# --- The semester's letter grade (METU style, on a curve; see logic/grade.py) ---
# Like a real teacher: no letters for single exams (you see your score and
# the class average), one letter at the end of the semester. The run's total
# is graded against ALL the earlier runs on this computer (the "class"):
# its "z" is how many standard deviations it is above their average (0 =
# average, +1 = clearly better). Until there are GRADE_CURVE_MIN earlier
# runs there is no class yet, and a fixed table is used: the share of all
# the exam points you got (points / questions; right +1, wrong -0.5, a
# failed exam 0).
# (letter, the least z on the curve, the least share without a curve). Best first.
GRADES = [
    ("AA",  1.3, 0.90),
    ("BA",  0.9, 0.80),
    ("BB",  0.5, 0.70),
    ("CB",  0.1, 0.60),
    ("CC", -0.3, 0.50),   # about the class average: a pass
    ("DC", -0.7, 0.40),
    ("DD", -1.1, 0.30),
    ("FD", -1.5, 0.15),
    ("FF", float("-inf"), float("-inf")),   # everything else, and a total of 0
]
GRADE_CURVE_MIN = 5          # earlier runs needed before grading on the curve
GRADE_HISTORY_KEPT = 200     # how many past runs (and past scores of each exam) are kept, the newest
GRADE_STAMP_DELAY = 0.5      # seconds after the score count ends before the grade is stamped on
TALLY_START = 0.8           # seconds after the end screen opens before the score tally starts
TALLY_STEP_TIME = 0.45      # seconds between two parts of the tally (each question, then the bonuses)
TALLY_COUNT_TIME = 0.3      # seconds the score takes to count up after a part appears
# The score rolls like the reels of a slot machine while it counts. The
# bigger the score, the wilder: it shakes more, more sparks fly, and from
# TALLY_JACKPOT_SHARE up it ends with "JACKPOT!".
TALLY_FX_FULL_SCORE = 6000  # an exam score this big gets the strongest effects (a run: this x its exams)
TALLY_JACKPOT_SHARE = 0.7   # 0..1 of TALLY_FX_FULL_SCORE; from here the count ends with a jackpot
TALLY_SHAKE = 7             # pixels the score's reels shake at most while counting
TALLY_SPARKS = 36           # sparks that fly out of the score at most when a part arrives

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

# --- The run: three exams in a row (PLAN.md section 11) ---
# Each exam: its title (loading screen) and its "tagline" (the sarcastic
# line on the title card after loading), its time in seconds, how many
# questions (at most ANSWERS_NEEDED), the teacher moods it picks one of at
# random (the slot machine on the gossip screen), so no two runs are the
# same, and "suspicious": a hidden 0..1 point on the suspicion bar. Above it,
# the teacher keeps watching you until the bar drains back under it: you
# have to look at your paper. Lower = he gets suspicious sooner. The run's
# score is the total.
QUIZZES = [
    {"title": "THE QUIZ",    "tagline": "This gotta be easy... right?",
     "time": 150, "questions": 3, "suspicious": 0.60,
     "moods": ("team_won", "all_nighter", "birthday", "new_phone", "normal_day")},
    {"title": "THE MIDTERM", "tagline": "I can handle this. Probably. Maybe not.",
     "time": 130, "questions": 4, "suspicious": 0.45,
     "moods": ("coffee", "phone_fight", "diet", "traffic")},
    {"title": "THE FINAL",   "tagline": "God, please help me.",
     "time": 120, "questions": 5, "suspicious": 0.30,
     "moods": ("motorcycle", "paranoid", "dean_visit", "lost_bet")},
]
SUSPICIOUS_AT = 0.6         # 0..1, the hidden point when no exam says otherwise (see "suspicious" above)
# The practice exam after "How to play": the same kind of entry as above,
# short and easy, with a sleepy teacher. It is not counted anywhere (no top
# score, no class average, no grade).
# "ease": every danger at this part of its strength (0.75 = 75 %): the
# suspicion bar fills slower, the teacher's looks are shorter, and you read
# faster (PAPER_FOCUS_TIME x 0.75). 1.0 (or no "ease") for the real exams.
PRACTICE_QUIZ = {"title": "PRACTICE EXAM", "tagline": "It doesn't even count. Relax.", "time": 60, "questions": 2, "suspicious": 0.8,
                 "moods": ("practice",), "ease": 0.75}
# The teacher's moods. Before each exam the gossip screen spins a slot
# machine over the exam's moods, stops on today's, and tells the gossip, a
# short story of what happened ("story": one string per line, at most about
# 70 letters) and what it means: "good" lines (+, green) and "bad" lines
# (-, red). The Quiz's moods are only good (or plain), the Midterm's have
# both, the Final's are only bad. For now a mood is only numbers (bluffs and
# sneaky glances come in phase B): "busy" and "watching" are (min, max)
# seconds of those states, "move" the 0..1 chance to change place
# (board/desk) after watching, and "place" (optional) where he starts
# ("BOARD" if not given). A mood can also have its own pictures, e.g.
# assets/images/classroom_board_busy_birthday.jpeg (see ui/render.py).
# The good/bad lines must match the numbers (tests/test_moods.py checks
# them against "normal_day": e.g. "Long busy times" needs longer busy times).
MOODS = {
    # --- The practice exam (PRACTICE_QUIZ) ---
    "practice": {
        "gossip": "It is only a practice exam.",
        "story": ["Nothing counts today, and he knows it.",
                  "He brought a newspaper and a big cup of tea,",
                  "and he is in no hurry to look up."],
        "good": ["Very long busy times", "Short, sleepy looks", "He never leaves the board"],
        "bad": [],
        "busy": (6.0, 9.0), "watching": (2.5, 3.5), "move": 0.0},
    # --- The Quiz: good days ---
    "team_won": {
        "gossip": "His team won last night.",
        "story": ["His team won the derby in the very last minute.",
                  "He has been humming the club song all morning,",
                  "and he keeps watching the goal on his phone."],
        "good": ["Long busy times: he is watching the goal again", "Only quick looks at the class"],
        "bad": [],
        "busy": (5.0, 8.0), "watching": (3.0, 4.5), "move": 0.3},
    "all_nighter": {
        "gossip": "He graded papers all night.",
        "story": ["He marked two hundred midterms until four in the morning.",
                  "His eyes keep closing over the papers on his desk,",
                  "and he hardly has the energy to walk around."],
        "good": ["Long quiet moments while he dozes", "He stays where he is"],
        "bad": [],
        "busy": (5.0, 9.0), "watching": (3.0, 5.0), "move": 0.1},
    "birthday": {
        "gossip": "It is his birthday today.",
        "story": ["There was cake in the teachers' room this morning.",
                  "He is smiling at his phone, reading the messages,",
                  "one happy birthday after another."],
        "good": ["Very long busy times", "Short, happy looks"],
        "bad": [],
        "busy": (6.0, 9.5), "watching": (3.0, 4.5), "move": 0.2},
    "new_phone": {
        "gossip": "He got a new phone.",
        "story": ["The newest model, still with the plastic on it.",
                  "He is moving his photos over, one by one,",
                  "and looks up only while something is loading."],
        "good": ["Long busy times at the desk", "Quick looks", "He never leaves the desk"],
        "bad": [],
        "busy": (5.0, 8.5), "watching": (2.5, 4.5), "move": 0.0, "place": "DESK"},
    "normal_day": {
        "gossip": "Nothing special happened today.",
        "story": ["No news, no gossip, no drama.",
                  "Just a teacher, a quiz,",
                  "and a class full of students."],
        "good": [],
        "bad": [],
        "busy": (3.5, 6.5), "watching": (4.0, 7.0), "move": 0.4},
    # --- The Midterm: good and bad ---
    "coffee": {
        "gossip": "He is on his third coffee.",
        "story": ["Three espressos before nine o'clock.",
                  "He cannot sit still for a second:",
                  "board, desk, board, desk..."],
        "good": ["His looks are quick and nervous"],
        "bad": ["Short busy times", "He keeps moving between board and desk"],
        "busy": (2.5, 5.0), "watching": (2.5, 4.0), "move": 0.6},
    "phone_fight": {
        "gossip": "He is fighting with someone on the phone.",
        "story": ["The insurance company called about his car.",
                  "He is arguing at his desk, louder and louder.",
                  "But when he hangs up, he is in a terrible mood."],
        "good": ["Long calls, and he stays at his desk"],
        "bad": ["When he looks, he looks for a while"],
        "busy": (4.5, 7.5), "watching": (5.0, 7.5), "move": 0.05, "place": "DESK"},
    "diet": {
        "gossip": "He started a diet this morning.",
        "story": ["No breakfast, no sugar, no bread.",
                  "He is hungry, grumpy and very, very bored,",
                  "so he looks up all the time, but sees nothing."],
        "good": ["Short, absent-minded looks", "Too hungry to walk around"],
        "bad": ["Short busy times"],
        "busy": (2.5, 5.0), "watching": (2.5, 4.0), "move": 0.15},
    "traffic": {
        "gossip": "He was stuck in traffic for two hours.",
        "story": ["Two hours on the highway, to come and watch you.",
                  "He is tired and angry at the whole world.",
                  "Someone in this room is going to pay for it."],
        "good": ["Too tired to walk around"],
        "bad": ["Long, angry looks"],
        "busy": (3.5, 6.5), "watching": (5.0, 8.0), "move": 0.1},
    # --- The Final: bad days ---
    "motorcycle": {
        "gossip": "Someone scratched his motorcycle.",
        "story": ["His beloved motorcycle got a long scratch in the parking lot.",
                  "He thinks a student did it.",
                  "Maybe someone in this very room."],
        "good": [],
        "bad": ["Short busy times", "Long, angry stares"],
        "busy": (2.5, 4.5), "watching": (5.0, 8.0), "move": 0.4},
    "paranoid": {
        "gossip": "He caught someone last week.",
        "story": ["Last week he found notes in a student's sleeve.",
                  "Since then he trusts nobody,",
                  "and he walks around the room all the time."],
        "good": [],
        "bad": ["He barely works", "He keeps moving"],
        "busy": (2.0, 4.5), "watching": (4.5, 7.0), "move": 0.6},
    "dean_visit": {
        "gossip": "The dean is visiting today.",
        "story": ["The dean might walk in at any moment.",
                  "He wants to look like the strictest teacher alive,",
                  "so he watches the class like a hawk."],
        "good": [],
        "bad": ["Very long stares", "Short busy times"],
        "busy": (2.5, 5.0), "watching": (5.5, 8.5), "move": 0.25},
    "lost_bet": {
        "gossip": "He lost a bet to another professor.",
        "story": ["He bet he would catch three cheaters this week.",
                  "It is Friday, and he has caught none.",
                  "You would be number one."],
        "good": [],
        "bad": ["Short busy times", "He moves a lot"],
        "busy": (2.0, 4.5), "watching": (4.5, 7.5), "move": 0.55},
}

# --- Characters (picked before a run; PLAN.md 12.2, logic/character.py) ---
# Each character changes a few numbers of the rules. Anything a character
# does not list stays as it is (see DEFAULTS in logic/character.py):
#   focus_speed      x how fast a neighbour's paper gets sharp (1 = normal)
#   seen_speed       x how fast the suspicion bar fills while he sees you copying
#   stare_speed      x how fast it fills while you stare at him
#   creep_time       seconds for the bar to fill while you look anywhere but your paper,
#                    even when nothing suspicious happens (None = it drains as usual)
#   screen_focus_time  seconds the classroom takes to get sharp after you look at it (0 = at once)
#   screen_blur_start  0..1, how sharp the classroom is at the start of that (0 = very blurry)
#   jokers           jokers per exam (J while looking down: writes the right answer)
#   hand_in_share    0..1 of the exam time that must be left when you hand in ...
#   late_penalty     ... or this many points are taken off; the early bonus also
#                    counts from that line (0 there, full with all the time left)
#   busy_times, watching_times   x how long the teacher is busy / watches
#   both_know        True = both neighbours know every answer (and no sharp-eye bonus)
#   energy           True = a coin toss every exam: a sugar rush or a crash:
#   rush_chance      0..1, the chance of a sugar rush in the first exam ...
#   rush_chance_drop ... and how much lower it is for each rush already had in this run
#   rush_speed       x the speed of the world (the teacher, the clock, the bar) in a rush
#   crash_every      (min, max) seconds between two sleepy spells in a crash ...
#   crash_time       ... how long a spell lasts (seconds) ...
#   crash_focus      ... and x how fast you read during it
# "name", "tagline", "plus" and "minus" are what the character screen says
# (one sentence per + / - line; long ones are wrapped).
CHARACTERS = {
    "npc": {
        "name": "NPC WITH A MONSTER BAG",
        "tagline": "Brought his 4 kg Monster gaming laptop to a pen-and-paper exam. RGB on.",
        "plus": ["Absolutely nothing happens. The game exactly as the devs intended"],
        "minus": ["The laptop can't help. It's an exam. He knows. He brought it anyway"]},
    "cap": {
        "name": "THE NEW ERA GUY",
        "tagline": "Flat brim, gold sticker still on. Hasn't seen his own eyebrows since 2019.",
        "plus": ["The brim hides his eyes: staring and copying fill the bar slower"],
        "minus": ["Hat indoors?! The teacher is offended: the bar creeps up whenever "
                  "you're not looking at your paper"],
        "seen_speed": 0.65, "stare_speed": 0.6, "creep_time": 30.0},
    "glasses": {
        "name": "GLASSES",
        "tagline": "-6 diopters. Reads a neighbour's paper from orbit. Can't find the board.",
        "plus": ["Eagle eyes: reads a neighbour's paper faster"],
        "minus": ["Looks up and sees a blurry, teacher-shaped blob for a moment"],
        "focus_speed": 1.25, "screen_focus_time": 0.9, "screen_blur_start": 0.25},
    "nerd": {
        "name": "THE NERD",
        "tagline": "Studied for three weeks. Cheats anyway, \"just to double-check\".",
        "plus": ["One joker per exam: J writes the one answer he actually knows"],
        "minus": ["His early bonus only starts at 30% of the time left",
                  "Later than that? His ego costs 1000 points"],
        "jokers": 1, "hand_in_share": 0.3, "late_penalty": 1000},
    "energy": {
        "name": "ENERGY DRINK ADDICT",
        "tagline": "Four cans before nine. Heart rate: yes.",
        "plus": ["Sugar rush (50%): time slows down, like in the movies"],
        "minus": ["Crash (50%): naps at random moments and reads like a sloth"],
        "energy": True, "rush_chance": 0.5, "rush_chance_drop": 0.15, "rush_speed": 0.85, "crash_every": (8.0, 14.0), "crash_time": 3.5,
        "crash_focus": 0.4},
    "buddy": {
        "name": "THE TEACHER'S BUDDY",
        "tagline": "They go fishing on Sundays. Calls him \"hocam\" with a wink.",
        "plus": ["Why check on your fishing buddy? He looks up less often"],
        "minus": ["But when he does, it's a long, disappointed dad stare"],
        "busy_times": 1.35, "watching_times": 1.35},
    "lazy": {
        "name": "LAZY BUT FUNNY",
        "tagline": "Never opened the book. Has a joke for every question instead.",
        "plus": ["Charisma 100: both neighbours show him the answer"],
        "minus": ["The teacher knows that laugh: the bar fills faster when he's seen",
                  "No sharp-eye bonus: there's nothing to find"],
        "both_know": True, "seen_speed": 1.4, "stare_speed": 1.3},
}
DEFAULT_CHARACTER = "npc"   # the first choice, and the one in the practice exam
