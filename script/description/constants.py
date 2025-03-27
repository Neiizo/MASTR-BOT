# Description: Constants for the Excenter Algorithm
###------- Target Status -------###
FREE = 0
ASSIGNED = 1
SKIPPED = 2
GONE = 3
BAD = 4

###------- Drop Status -------###
NORMAL = 10
FLIPPED = 11
ASSIGNED = ASSIGNED
SKIPPED = SKIPPED
DONE = 13

###-------- Rail Status --------###
CAN_PICK = 20
PICKING = 21
CAN_PLACE = 22
PLACING = 23


###------- Slider Status -------###
# Should we add a security, and make different states from the rail to avoid mixups?
IDLE = 30
TRAVELING = 31
SKIPPED = SKIPPED
SKIP_N_WAIT = 32
PICKING = PICKING
PLACING = PLACING
WAITING = 34
Z_MVMT = 35


###------- Direction Acronym -------###

ORTHOG_DIR = 0
SAME_DIR = 1


###------- Other constants -------###

MM_TO_M = 1e-3
M_TO_MM = 1e3

# BORDER_TOLERANCE = 10*MM_TO_M
N_EXTRA_DIST_BOUNCING = 3
BORDER_TOLERANCE = 10
TIMESTEP_AHEAD = 5
ROUNDING_DECIMALS = 5
ROUNDING_JSON = 2
PLOT_MARGIN = 50
NOISE = 5
TIME_Z_MOVE = 0.15


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BU = BOLD + UNDERLINE


n_character_per_line = 40

SEPARATOR = (
    bcolors.ENDC
    + bcolors.HEADER
    + bcolors.BOLD
    + "#" * n_character_per_line
    + bcolors.ENDC
)
SEPARATOR2 = (
    bcolors.ENDC
    + bcolors.HEADER
    + bcolors.BOLD
    + "#"
    + "-" * (n_character_per_line - 2)
    + "#"
    + bcolors.ENDC
)
LINE_START = bcolors.ENDC + bcolors.HEADER + bcolors.BOLD + "# " + bcolors.ENDC
LINE_END = bcolors.ENDC + bcolors.HEADER + bcolors.BOLD + " #" + bcolors.ENDC
