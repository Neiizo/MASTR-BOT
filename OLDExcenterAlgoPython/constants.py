# Description: Constants for the Excenter Algorithm
###-------- Drop Status --------###
FREE = 0
ASSIGNED = 1
SKIPPED = 2
GONE = 3

###-------- Rail Status --------###
CAN_PICK = 10
PICKING = 11
CAN_PLACE = 12
PLACING = 13
DONE_PLACING = 14
WAIT_CONVEYOR = 15


###------- Slider Status -------###
# Should we add a security, and make different states from the rail to avoid mixups?
IDLE = 20
TRAVELING = 21
SKIPPED = SKIPPED
SKIP_N_WAIT = 22
PICKING = PICKING
PLACING = PLACING
DROPPED = 23
WAITING = 24
