from scripts.trajectoryControl import (
    targetAssignment,
    bounceState,
    findPicksInRange,
    findDropsInRange,
)

from description.objects import *
from description.constants import *


def assignDrops(sliders: list[list[Slider]], conveyors: Conveyor, beams: Beam):
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
        if beams.railStatus[railID] != CAN_PLACE:
            continue
        
        listAvailableID = findDropsInRange(conveyors, beams, rail)
        if listAvailableID.size != 0:
            side = 0 if beams.workspaceSide[railID // 2] == 0 else -1
            targetAssignment(rail, conveyors, beams, side, listAvailableID, "out")
            
            if beams.bouncingInitState[railID]:
                attempPickAsignement(beams, conveyors, rail, railID)
                
        elif beams.bouncingInitState[railID]:
            bounceState(beams, rail, CAN_PICK)
            attempPickAsignement(beams, conveyors, rail, railID)


def attempPickAsignement(
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
    listAvailablePickID = findPicksInRange(conveyors, beams, rail)
    if listAvailablePickID.size != 0:
        side = 0 if beams.workspaceSide[railID // 2] == 1 else -1
        targetAssignment(rail, conveyors, beams, side, listAvailablePickID, "in")
    else:
        bounceState(beams, rail, CAN_PLACE)
