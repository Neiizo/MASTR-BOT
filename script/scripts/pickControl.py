from scripts.trajectoryControl import (
    targetAssignment,
    bounceState,
    findPicksInRange,
    findDropsInRange,
)

from description.objects import *
from description.constants import *


def assignPicks(sliders: list[list[Slider]], conveyors: Conveyor, beams: Beam):
    """Itterates through all of the beams, check their state, and if possible, continues 
    forward with the target assignment.

    Args:
        sliders (list[list[Slider]]): List of rails, which are list of sliders objects
        conveyors (Conveyor): object of the class Conveyor, containing all of the informations
                              regarding conveyors        
        beams (Beam): object of the class Beam, containing all of the informations
                              regarding beams
    """
    for railID, rail in enumerate(sliders):
        if beams.railStatus[railID] != CAN_PICK:
            continue
        
        listAvailableID = findPicksInRange(conveyors, beams, rail)
        if listAvailableID.size != 0:
            side = 0 if beams.workspaceSide[railID // 2] == 1 else -1
            targetAssignment(rail, conveyors, beams, side, listAvailableID, "in")
            
            if beams.bouncingInitState[railID]:
                attemptDropAssignement(beams, conveyors, rail, railID)
                
        elif beams.bouncingInitState[railID]:
            bounceState(beams, rail, CAN_PLACE)
            attemptDropAssignement(beams, conveyors, rail, railID)


def attemptDropAssignement(
    beams: Beam,
    conveyors: Conveyor,
    rail: list[Slider],
    railID: int,
):
    """For the state bouncing, tries to do the opposite action.

    Args:
        rail ([list[Slider]): List of slider objects along a given rail
        conveyors (Conveyor): object of the class Conveyor, containing all of the informations
                              regarding conveyors        
        beams (Beam): object of the class Beam, containing all of the informations
                              regarding beams
        railID (int): ID of the rail
    """
    listAvailableDropID = findDropsInRange(conveyors, beams, rail)
    if listAvailableDropID.size != 0:
        side = 0 if beams.workspaceSide[railID // 2] == 0 else -1
        targetAssignment(rail, conveyors, beams, side, listAvailableDropID, "out")
    else:
        bounceState(beams, rail, CAN_PICK)
