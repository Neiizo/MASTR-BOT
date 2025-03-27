from description.objects import *
from description.constants import *
import traceback
import scripts.compute_trajectory as move
import description.config as cfg
import copy as copy


def findPicksInRange(
    conveyors: Conveyor,
    beams: Beam,
    rail: list[Slider],
) -> np.ndarray:
    """Check what pick location are available for the current rail.

    Args:
        conveyors (Conveyor): object of the class Conveyor, containing all of the informations
                              regarding conveyors
        beams (Beam): object of the class Beam, containing all of the informations regarding beams
        rail (list[Slider]): List of sliders that are on the same rail.
    """
    listPicksPos = np.array([pick["pos"] for pick in conveyors.listPicks.values()])
    status = np.array([pick["status"] for pick in conveyors.listPicks.values()])
    rowsID = np.array([pick["rowID"] for pick in conveyors.listPicks.values()])
    convID = np.array([pick["conveyorID"] for pick in conveyors.listPicks.values()])

    DoIBID = beams.direction[ORTHOG_DIR]
    DoIC = conveyors.inDirection
    slider = rail[0]
    railID = slider.ID // 2

    "Take only the coordinates along one axis (DoIBID : Direction of Interest of the Beam index)"
    pickPos = listPicksPos[:, DoIBID]
    extraDist = conveyors.extraLookingRange[0]
    
    if beams.bouncingInitState[railID] == CAN_PICK:
        extraDist *= N_EXTRA_DIST_BOUNCING 
        
    "Add a small distance, to take into account the slider's translation time"

    extraMinDist = -extraDist if DoIC[DoIC[SAME_DIR]] != -1 else 0
    extraMaxDist = extraDist if DoIC[DoIC[SAME_DIR]] == -1 else 0

    sliderArmMax = slider.maxPosition[DoIBID] + extraMaxDist
    sliderArmMin = slider.minPosition[DoIBID] + extraMinDist

    listTemp3 = np.intersect1d(
        np.flatnonzero(pickPos < sliderArmMax), np.flatnonzero(pickPos > sliderArmMin)
    )

    "Search for any picks that are in the same rows as the ones already found"
    inSameRow = np.flatnonzero(np.isin(rowsID, rowsID[listTemp3]))
    validID = np.flatnonzero(
        ((status == FREE) | (status == SKIPPED))
        & (convID == beams.workspaceSide[railID // 2])
    )

    listAvailableID = np.intersect1d(inSameRow, validID)

    return np.array(list(conveyors.listPicks.keys()))[listAvailableID]


def findDropsInRange(
    conveyors: Conveyor,
    beams: Beam,
    rail: list[Slider],
) -> np.ndarray:
    """Check what drop location are available for the current rail.

    Args:
        conveyors (Conveyor): object of the class Conveyor, containing all of the informations
                              regarding conveyors
        beams (Beam): object of the class Beam, containing all of the informations regarding beams
        rail (list[Slider]): List of sliders that are on the same rail.
    """
    listDropsPos = np.array([drop["pos"] for drop in conveyors.listDrops.values()])
    status = np.array([drop["status"] for drop in conveyors.listDrops.values()])

    DoIBID = beams.direction[ORTHOG_DIR]
    DoIC = conveyors.outDirection
    slider = rail[0]

    "Take only the coordinates along one axis (DoIID : Direction of Interest index)"
    dropPos = listDropsPos[:, DoIBID]

    "Add a small distance, to take into account the slider's translation time"
    extraDist = conveyors.extraLookingRange[1]
    
    if beams.bouncingInitState[slider.ID // 2] == CAN_PLACE:
        extraDist *= N_EXTRA_DIST_BOUNCING 

    extraMinDist = -extraDist if DoIC[DoIC[SAME_DIR]] != -1 else 0
    extraMaxDist = extraDist if DoIC[DoIC[SAME_DIR]] == -1 else 0

    maxPos = slider.maxPosition[DoIBID] + extraMaxDist
    minPos = slider.minPosition[DoIBID] + extraMinDist

    "We only take the drops locations for the corresponding cups (flipped or normal)"
    listTemp = np.flatnonzero(
        (dropPos < maxPos)
        & (dropPos > minPos)
        & ((status == NORMAL) | (status == SKIPPED))
    )

    "We also want to record the total amount of drops in range at time T, for some statistics"
    # if slider.ID // 4 == len(beams.listBeamPos) - 1:
    #     nDropsInRange = len(np.flatnonzero((dropPos < maxPos) & (dropPos > minPos)))
    #     cfg.listStat[-1]["dropsInRangePerT"][-1] += nDropsInRange
    return np.array(list(conveyors.listDrops.keys()))[listTemp]


def findViableTarget(
    conveyors: Conveyor,
    beams: Beam,
    slider: Slider,
    inOrOut: str,
    listAvailableID: np.ndarray,
) -> bool: 
    """Find a suitable target inside the list, that the slider will be able to reach in time.

    Args:
        conveyors (Conveyor): Conveyor object containing information about the conveyors.
        beams (Beam): Beam object containing beam information.
        slider (Slider): Slider object that will be assigned to the target.
        inOrOut (str): "in" or "out" depending on the target type.
        listAvailableID (np.ndarray): List of available pick/drop IDs.

    Returns:
        bool: If a suitable target has been found or not
    """
    "DoI: Direction of Interest. Array of 2 values. C stand for conveyor, B stands for beam"
    DoIC = np.array(getattr(conveyors, f"{inOrOut}Direction"))
    "DoI_ID : indices of the Direction of Interest. Single value used as an index"
    DoICID = DoIC[SAME_DIR]
    "Gives the sign of the direction, regardless of wether it's on x or y"
    signDoICID = DoIC[DoICID]
    DoIB = beams.direction
    sliderArmMax = slider.maxPosition[DoIB[ORTHOG_DIR]]
    sliderArmMin = slider.minPosition[DoIB[ORTHOG_DIR]]
    IdConv = 0 if inOrOut == "in" else 1

    extraDist = conveyors.extraLookingRange[IdConv]
    if beams.bouncingInitState[slider.ID // 2]:
        extraDist *= N_EXTRA_DIST_BOUNCING 

    minPos = sliderArmMin - extraDist if signDoICID == 1 else sliderArmMin
    maxPos = sliderArmMax if signDoICID == 1 else sliderArmMax + extraDist
    """Start a loop around the list of possible targets. Leaves only when something has been found
    or nothing is suitable."""
    for targetID in listAvailableID:
        targetPos = getTargetPos(inOrOut, targetID, conveyors)
        if signDoICID == 1:
            startSliderZone = max(sliderArmMin, targetPos[DoICID])
        else:
            startSliderZone = min(sliderArmMax, targetPos[DoICID])

        meetingPos = targetPos * np.abs(DoIC[::-1]) + startSliderZone * np.abs(DoIC)
        testing = True
        "Test if the target is reachable or not, considering the time of travel"
        while testing:
            travel_time = move.computeWholeTrajectory(slider, meetingPos)
            travel_time = (travel_time + cfg.dt) - travel_time % cfg.dt
            newSliderPos = [
                num * M_TO_MM for num in slider.trajectory.at_time(travel_time)[0]
            ]

            "Computes position of the target after that time"
            nextTargetPos = (
                targetPos + (conveyors.deltaMove[IdConv] * travel_time / cfg.dt) * DoIC
            )
            PosCoI = nextTargetPos[DoICID]  #  Position's Coordinate of Interest

            if minPos > PosCoI or PosCoI > maxPos:
                "The target will be out of reach. Try the next one"
                testing = False

            elif (newSliderPos[DoICID] - PosCoI) * signDoICID < -conveyors.errorMargin:
                "The slider will be behind the target. Try with a further target position"
                meetingPos = nextTargetPos

            elif (newSliderPos[DoICID] - PosCoI) * signDoICID < conveyors.errorMargin:
                "Target is close, but not past the error margin. Try with a further target position"
                meetingPos = newSliderPos[:-1] + conveyors.deltaMove[IdConv] * DoIC

            else:
                "The target is reachable"
                setSliderTarget(conveyors, slider, inOrOut, targetID, meetingPos)
                return True
    return False


def targetAssignment(
    rail: list[Slider],
    conveyors: Conveyor,
    beams: Beam,
    side: int,
    listAvailableID: np.ndarray,
    inOrOut: str,
) -> None:
    """Try to find a suitable target for the sliders. First create a list of eligible targets, then
    sort them, according to the rail's scheduling. Finally, test the targets until one is found.

    Args:
        rail (list[Slider]): list of sliders on the same rail.
        conveyors (Conveyor): Conveyor object containing information about the conveyors.
        beams (Beam): Beam object containing beam information.
        side (int): Side of the sliders, with respect to the output conveyor.
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        inOrOut (str): "in" or "out" depending on the target type.

    Raises:
        ValueError: If inOrOut is not "in" or "out".
        NotImplementedError: If the desired scheduling type is not implemented yet.
        ValueError: If the scheduling type is invalid.
    """

    if inOrOut == "in":
        tmp = "Pick"
        nextState = PICKING
        nextBouncingState = CAN_PLACE
        scheduling = rail[side].inScheduling

    elif inOrOut == "out":
        tmp = "Drop"
        nextState = PLACING
        nextBouncingState = CAN_PICK
        scheduling = rail[side].outScheduling

    else:
        raise ValueError("inOrOut must be either 'in' or 'out'")

    listTargets = getattr(conveyors, f"list{tmp}s")
    match scheduling:
        case "FIFO":
            listAvailableID = sortFIFO(listAvailableID, side, listTargets)

        case "LIFO":
            listAvailableID = sortLIFO(listAvailableID, side, listTargets)

        case "SPT":
            listAvailableID = sortSPT(beams, listAvailableID, side, listTargets)

        case "LPT":
            listAvailableID = sortLPT(beams, listAvailableID, side, listTargets)
            side = np.abs(side) - 1

        case "splitConveyor":
            raise NotImplementedError("splitConveyor not implemented yet")

        case _:
            raise ValueError("Invalid scheduling type")

    if rail[side].status not in (SKIPPED, WAITING):
        slider = rail[side]
        isFirstSlider = True

    else:
        "Check whether the remaining slider can still pick something"
        slider = rail[side + 1]
        isFirstSlider = False
    railID = rail[0].ID // 2

    hasFound = findViableTarget(conveyors, beams, slider, inOrOut, listAvailableID)

    if hasFound:
        """The target has been assigned, we remove it from the list.
        We do not want it assigned to the other slider as well"""
        condition = listAvailableID == slider.trackedTargetID
        listAvailableID = np.delete(listAvailableID, condition, axis=0)

        if beams.bouncingInitState[railID]:
            "We stop the bouncing state"
            beams.bouncingInitState[railID] = 0

        beams.railStatus[railID] = nextState

        if isFirstSlider and rail[side + 1].status not in (SKIPPED, WAITING):
            searchForSecondSlider(
                rail, conveyors, beams, side, listAvailableID, inOrOut
            )
        else:
            setRemainingPosition(rail, beams, side + 1 * isFirstSlider)

    elif beams.bouncingInitState[railID]:
        bounceState(beams, rail, nextBouncingState)

    elif not isFirstSlider and inOrOut == "in":
        "it means the other slider is in WAITING state and we just did a SKIP_N_WAIT"
        slider.status = SKIPPED
        beams.railStatus[railID] = PICKING


def searchForSecondSlider(
    rail: list[Slider],
    conveyors: Conveyor,
    beams: Beam,
    side: int,
    listAvailableID: np.ndarray,
    inOrOut: str,
) -> None:
    """Attempt to assign a target to the second slider on the rail.

    Args:
        rail (list[Slider]): list of sliders on the same rail.
        conveyors (Conveyor): Conveyor object containing information about the conveyors.
        beams (Beam): Beam object containing beam information.
        side (int): Side of the sliders, with respect to the output conveyor.
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        inOrOut (str): "in" or "out" depending on the target type.
    """
    hasFound = False
    slider = rail[side + 1]
    while not hasFound:
        hasFound = findViableTarget(conveyors, beams, slider, inOrOut, listAvailableID)
        if not hasFound:
            "There aren't any candidate left"
            setRemainingPosition(rail, beams, side + 1)
            break
        elif isColliding(rail[side], slider, conveyors, beams, inOrOut):
            "The target led to a collision. We remove it from the list of candidates"
            hasFound = False
            index = np.where(listAvailableID == slider.trackedTargetID)[0][0]
            listAvailableID = listAvailableID[index + 1 :]


def isColliding(
    slider1: Slider,
    slider2: Slider,
    conveyors: Conveyor,
    beams: Beam,
    inOrOut: str,
) -> bool:
    """Check whether the given targets will lead to a collision or not

    Args:
        slider1 (Slider): Slider object of the first slider
        slider2 (Slider): Slider object of the second slider
        conveyors (Conveyor): Conveyor object containing information about the conveyors.
        beams (Beam): Beam object containing beam information.
        inOrOut (str): "in" or "out" depending on the target type.

    Raises:
        ValueError: If inOrOut is not "in" or "out".

    Returns:
        bool: True if the targets will lead to a collision, False otherwise.
    """

    DoI = beams.direction
    sliderPos = getTargetPos(inOrOut, slider1.trackedTargetID, conveyors)
    targetID = slider2.trackedTargetID
    pickDropPos = getTargetPos(inOrOut, targetID, conveyors)
    deltaPos = (pickDropPos - sliderPos)[DoI[SAME_DIR]]
    deltaPos = deltaPos if (slider2.ID%2) == 1 else -deltaPos
    if deltaPos < slider1.width + slider1.safetyMargin:
        setTargetSkipped(inOrOut, targetID, conveyors)
        return True
    return False


def bounceState(beams: Beam, rail: list[Slider], nextBouncingState: int) -> None:
    """Bounces the state of the sliders and the beam.

    Args:
        beams (Beam): Beam object containing beam information.
        rail (list[Slider]): List of sliders on the same rail.
        nextBouncingState (int): The next bouncing state.
    """
    ##NOTE Maybe move all of these state changing function into the object itself (like slider.nextState)
    beams.railStatus[rail[0].ID // 2] = nextBouncingState
    if WAITING in (rail[0].status, rail[1].status):
        "We invert the state, otherwise the slider that has a pick will wait instead of PLACING"
        if rail[0].status == WAITING:
            rail[0].status = IDLE
            rail[1].status = WAITING
        else:
            rail[0].status = WAITING
            rail[1].status = IDLE


def sortFIFO(listAvailableID: np.ndarray, side: int, listTargets: list) -> np.ndarray:
    """Sort picks with furthest picks along the conveyor's direction first.

    Args:
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        side (int): Side of the picks, with respect to the output conveyor.
        listTargets (list): List of target positions.

    Returns:
        ndarray: List of the IDs of the picks sorted by distance, IDs for the conveyors.listPicks / listDrops.
    """
    rowIDs = np.array([listTargets[idx]["rowID"] for idx in listAvailableID])

    newlistAvailableID = np.array([])
    for i in np.unique(rowIDs):
        tempID = listAvailableID[rowIDs == i]
        tempID = tempID[::-1] if side == -1 else tempID

        newlistAvailableID = np.append(newlistAvailableID, tempID, axis=0)

    return newlistAvailableID


def sortLIFO(listAvailableID: np.ndarray, side: int, listTargets: list) -> np.ndarray:
    """Sort picks with closest picks along the conveyor's direction first.

    Args:
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        side (int): Side of the picks, with respect to the output conveyor.
        listTargets (list): List of target positions.

    Returns:
        ndarray: List of the IDs of the picks sorted by distance, IDs for the conveyors.listPicks / listDrops.
    """

    rowIDs = np.array([listTargets[idx]["rowID"] for idx in listAvailableID])

    newlistAvailableID = np.array([])
    for i in np.unique(rowIDs)[::-1]:
        tempID = listAvailableID[rowIDs == i]
        tempID = tempID[::-1] if side == -1 else tempID

        newlistAvailableID = np.append(newlistAvailableID, tempID, axis=0)

    return newlistAvailableID


def sortSPT(
    beams: Beam, listAvailableID: np.ndarray, side: int, listTargets: list
) -> np.ndarray:
    """Sorts picks with the closest picks along the beam's direction first.

    Args:
        beams (Beam): Beam object containing beam information.
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        side (int): Side of the picks, with respect to the output conveyor.
        listTargets (list): List of target positions.

    Returns:
        ndarray: List of the IDs of the picks sorted by distance, IDs for the conveyors.listPicks / listDrops.
    """

    listPicksPos = np.array([listTargets[idx]["pos"] for idx in listAvailableID])
    DoI = beams.direction
    
    # listAvailableID = listAvailableID[np.argsort(listPicksPos[:, DoI[SAME_DIR]])]
    listAvailableID = listAvailableID[
        np.argsort(
            listPicksPos[:, DoI[SAME_DIR]],
            axis=DoI[ORTHOG_DIR],
        )
    ]
    listAvailableID = listAvailableID[::-1] if side == -1 else listAvailableID

    return listAvailableID


def sortLPT(
    beams: Beam, listAvailableID: np.ndarray, side: int, listTargets: list
) -> np.ndarray:
    """Sorts picks with the farthest picks along the beam's direction first.

    Args:
        beams (Beam): Beam object containing beam information.
        listAvailableID (np.ndarray): List of available pick/drop IDs.
        side (int): Side of the picks, with respect to the output conveyor.
        listTargets (list): List of target positions.

    Returns:
        ndarray: List of the IDs of the picks sorted by distance, IDs for the conveyors.listPicks / listDrops.
    """
    listPicksPos = np.array([listTargets[idx]["pos"] for idx in listAvailableID])
    DoI = beams.direction
    listAvailableID = listAvailableID[
        np.argsort(
            listPicksPos[:, DoI[SAME_DIR]],
            axis=DoI[ORTHOG_DIR],
        )
    ]
    listAvailableID = listAvailableID[::-1] if side == 0 else listAvailableID

    return listAvailableID


def sortSplitConveyor():
    """The idea is to split the conveyor in two, as we always have 2 sliders. This means they
    never overlap each other and it should avoid useless waiting time from SKIP_N_WAIT sliders.
    This should also help balance the workload.
    """
    pass


def setExtraLookingRange(slider: Slider, conveyors: Conveyor) -> None:
    """Computes the average time of travel between one conveyor to the other. This time is then used
    to compute the travel distance from the conveyor in the meantime. This distance is used to look
    for possible targets in advance.

    Args:
        slider (Slider): The slider object for which the extra looking range is being set.
        conveyors (Conveyor): The conveyor object containing information about the conveyors.
    """
    targetOtherConveyor = np.add(
        slider.targetPosition[:2],
        conveyors.deltaConveyorPos * np.array(slider.direction),
    )
    t_travel = move.computeWholeTrajectory(slider, targetOtherConveyor)
    conveyors.extraLookingRange = np.array(conveyors.deltaMove) * t_travel / cfg.dt


def getTargetPos(inOrOut: str, targetID: int, conveyors: Conveyor) -> np.ndarray:
    """Returns the position of the given target.

    Args:
        inOrOut (str): "in" or "out" depending on the target type.
        targetID (int): The ID of the target.
        conveyors (Conveyor): The conveyor object containing the target information.

    Raises:
        ValueError: If inOrOut is not "in" or "out".

    Returns:
        np.ndarray: The position of the target.
    """
    if inOrOut == "in":
        return conveyors.listPicks[targetID]["pos"]

    elif inOrOut == "out":
        return conveyors.listDrops[targetID]["pos"]

    else:
        traceback.print_stack()
        raise ValueError("inOrOut must be either 'in' or 'out'")


def setTargetSkipped(inOrOut: str, targetID: int, conveyors: Conveyor) -> None:
    """Sets the target as skipped.

    Args:
        inOrOut (str): "in" or "out" depending on the target type.
        targetID (int): The ID of the target.
        conveyors (Conveyor): The conveyor object containing the target information.

    Raises:
        ValueError: If inOrOut is not "in" or "out".
    """
    if inOrOut == "in":
        conveyors.listPicks[targetID]["status"] = SKIPPED

    elif inOrOut == "out":
        conveyors.listDrops[targetID]["status"] = SKIPPED

    else:
        traceback.print_stack()
        raise ValueError("inOrOut must be either 'in' or 'out'")


def setSliderTarget(
    conveyors: Conveyor,
    slider: Slider,
    inOrOut: str,
    targetID: int,
    meetingPos: np.ndarray,
) -> None:
    """Sets the slider's target position to the given target (projected on its axis), changes the
    slider's status and the target's status.

    Args:
        inOrOut (str): "in" or "out" depending on the target type.
        targetID (int): The ID of the target.
        conveyors (Conveyor): The conveyor object containing the target information.
        slider (Slider): The slider object that will be assigned to the target.
    """
    DoIID = np.abs(np.array(getattr(conveyors, f"{inOrOut}Direction"))[SAME_DIR])

    sliderArmMax = slider.maxPosition[DoIID]
    sliderArmMin = slider.minPosition[DoIID]
    slider.targetPosition = meetingPos
    slider.targetPosition[DoIID] = np.clip(
        slider.targetPosition[DoIID], sliderArmMin, sliderArmMax
    )
    slider.trackedTargetID = targetID
    if inOrOut == "in":
        conveyors.listPicks[targetID]["status"] = ASSIGNED
        slider.status = PICKING

    else:
        conveyors.listDrops[targetID]["status"] = ASSIGNED
        slider.status = PLACING


def setRemainingPosition(rail: list[Slider], beams: Beam, side: int) -> None:
    """Set the position of the remaining slider to be next to the other slider. Also sets the
    state of the slider to SKIP_N_WAIT.

    Args:
        rail (list[Slider]): List of sliders on the same rail.
        beams (Beam): The beam object containing the beam information.
        side (int): The side of the slider to set.
    """
    if rail[side].status in (WAITING, SKIPPED):
        "If a slider is in waiting state, it needs to follow its neighbors"
        pass

    else:
        rail[side].status = SKIP_N_WAIT

    DoI = beams.direction
    sign = 1 if np.abs(side) == 1 else -1

    coord1 = (
        rail[side - 1].targetPosition[:2]
        + sign * (rail[side].width + rail[side].safetyMargin)
    ) * np.abs(DoI)

    coord2 = rail[side].position[:2] * np.abs(DoI[::-1])
    rail[side].targetPosition = np.add(coord1, coord2)
