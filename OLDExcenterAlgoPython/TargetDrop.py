import numpy as np
import logging

import math_func as mf
from constants import *


###-----------------Private methods-----------------###
def __isRailReady(self, railID: int):
    """
    Checks if all sliders are ready to depart
    """
    for slider in self.sliders[railID]:
        if slider.state != "Ready":
            print(f"Sliders not ready")
            return False
    return True


def __slidersDeparture(self, railID: int):

    if self.param["beam"]["isDualRailPerAxis"]:
        sign = -1 if railID % 2 == 0 else 1
    else:
        sign = -1

    for slider in self.sliders[railID]:
        slider.arm_angle = sign * np.pi / 2
        slider.state = TRAVELING


def __availableSlots(self, railID: int):
    """Finds all the drop locations that are available for the sliders to drop the targets

    Args:
        railID (int): ID of the rail in self.sliders
    """
    tempList = np.argwhere(self.dropStatus[railID] == FREE).squeeze()
    self.listAvailableDropID = tempList[
        np.argsort(self.listDrop[railID, tempList][:, 0], axis=0)
    ]


def __checkInRange(self, railID: int):
    """Search along the list of drop location, which one are in range of the sub axis, and returns them

    Args:
        railID (int): ID of the rail in self.sliders

    Returns:
        listDropInRange (list_iterator ): List iterator of drop location that are in range of the sub axis
    """

    listDropInRange = []
    for id in self.listAvailableDropID:
        relativePosition = self.listDrop[railID, id][:, 1] - self.axisYPosList[railID]
        if np.abs(relativePosition) < self.param["slider"]["armLength"]:
            listDropInRange.append(id)
    return iter(listDropInRange)


def __dropLocationAssignement(self, railID: int, sliderID: int):
    """
    Assigns a destination to the sliders, for them to drop the targets.
    """

    if (
        self.sliders[railID][sliderID].state == SKIPPED
        or self.sliders[railID][sliderID].state == DROPPED
    ):
        ## The slider is free and will have a dynamic position to help the rest
        return
    listDropInRange = __checkInRange(self, railID)
    while True:
        dropID = next(listDropInRange)
        xProj, angle = mf.compute_dist_angle(
            self.param["slider"]["armLength"],
            self.axisYPosList[railID],
            self.listDrop[dropID, 1],
        )
        if sliderID == 0:
            __firstSliderDrop(self, dropID, railID, sliderID, xProj, angle)
        else:
            if self.sliders[railID][sliderID - 1].state == WAITING:
                self.sliders[railID][sliderID].state = WAITING
            __nextSliderDrop(self, dropID, railID, sliderID, xProj, angle)

        if self.dropStatus[dropID] == ASSIGNED:
            # As opposite to the pick process, we don't remove skipped position, as this part is sequential
            self.listAvailableDropID = np.delete(
                self.listAvailableDropID, dropID, axis=0
            )
            break
        if dropID == self.listAvailableDropID[-1]:
            ## We start over, but with a flag indicated it will be the next sequence
            self.sliders[railID][sliderID].state = WAITING
            self.sliders[railID][sliderID].firstWait = True
            listDropInRange = __checkInRange(self, railID)
        elif self.sliders[railID][sliderID].state == SKIP_N_WAIT:
            listDropInRange = __checkInRange(self, railID)

    ### ADD scenario where there are no drop lefts


def __firstSliderDrop(
    self, dropID: int, railID: int, sliderID: int, xProj: float, angle: float
):
    """Assigns the first possible drop location to the first slider. It should always work, as we are
    close to the origin. However, the securities are still here, in case the setup were to be modified
    in the future. But the drop should ALWAYS be in range for PLACING, per design

    Args:
        dropID (int): ID of the target in the self.listDrop list
        railID (int): ID of the rail in self.sliders
        sliderID (int): ID of the slider in self.sliders
        xProj (float): Projection of the target on the X-axis
        angle (float): Angle required to reach the target

    Raises:
        ValueError: This function should only be called for the first slider. If it is not the case,
        it will raise an error
    """
    if sliderID != 0:
        raise ValueError(
            "⛔⚡This function should only be called for the first slider⚡⛔"
        )

    minCond = self.carriageSafetyMargin
    maxCond = (
        self.param["slider"]["firstCableLength"] - self.param["slider"]["safetyMargin"]
    )

    relativePos_armForward = self.listDrop[dropID, 1] - xProj

    if relativePos_armForward > maxCond:
        raise Exception(
            "⛔⚡Target out of range. Per the original design, this should NOT happen⚡⛔"
        )
        logging.debug(
            f"[{railID}.{sliderID}] - Drop Location out of range, going to the next slider"
        )
        newPos = minCond
        __assignSlider(
            self,
            dropID,
            railID,
            sliderID,
            newPos,
            isAssignedTarget=False,
            maxPos=maxCond,
            minPos=minCond,
        )

    elif relativePos_armForward < self.param["slider"]["firstCableLength"]:
        newPos = relativePos_armForward
        newAngle = angle
        __assignSlider(self, dropID, railID, sliderID, newPos, angle=newAngle)
        logging.debug(
            f"[{railID}.{sliderID}] - First slider assigned to Drop Location assigned to "
            f"{dropID}, pos is {self.listDrop[dropID]:.2f}"
        )
    else:
        __fullDebugPrint(self, railID, dropID, xProj, maxCond, minCond, sliderID)
        raise Exception("This should not happen")


def __nextSliderDrop(
    self, dropID: int, railID: int, sliderID: int, xProj: float, angle: float
):
    """TODO

    Args:
        dropID (int): ID of the target in the self.targetObj list
        railID (int): ID of the rail in self.sliders
        sliderID (int): ID of the slider in self.sliders
        xProj (float): Projection of the target on the X-axis
        angle (float): Angle required to reach the target

    Raises:
        ValueError: This function should only be called for the non-first slider. If it is not the case,
        it will raise an error
    """
    if sliderID == 0:
        raise ValueError(
            "⛔⚡This function should only be called for the subsequent sliders⚡⛔"
        )

    minPos, maxPos = __getMinMaxPos(self, sliderID, railID)
    relativePos_armBackward = self.listTarget[dropID, 0] + xProj
    relativePos_armForward = self.listTarget[dropID, 0] - xProj

    # Check if the target is too close to the previous slider
    if relativePos_armBackward < minPos:
        logging.debug(
            f"[{railID}.{sliderID}] - Target too close to the previous slider. Skipping it"
        )
        return

    # Check if the target is too far for the current slider.
    if relativePos_armForward > maxPos:
        logging.debug(
            f"[{railID}.{sliderID}] - Target out of range, going to the next slider"
        )
        newPos = minPos
        __assignSlider(
            self,
            dropID,
            railID,
            sliderID,
            newPos,
            isAssignedTarget=False,
            maxPos=maxPos,
            minPos=minPos,
        )

        self.sliders[railID][sliderID].state = SKIP_N_WAIT
        if not (
            self.sliders[railID][sliderID - 1].firstWait
        ):  ### vraiment nul ca, tres tres nul, surtout si on a 100 slider
            self.sliders[railID][sliderID].firstWait = True
        return

    elif relativePos_armForward > minPos:
        logging.debug(
            f"[{railID}.{sliderID}] - Going for the closest possible position for target {dropID}"
        )
        newPos = relativePos_armForward
        newAngle = angle
        __assignSlider(self, dropID, railID, sliderID, newPos, newAngle)

    elif relativePos_armBackward < maxPos:
        logging.debug(
            f"[{railID}.{sliderID}] - Going for the furthest possible position for target {dropID}"
        )
        newPos = relativePos_armBackward
        newAngle = np.pi - angle
        __assignSlider(self, dropID, railID, sliderID, newPos, newAngle)

    else:
        logging.error(f"[{railID}.{sliderID}] - ⛔⚡UNEXPECTED BEHAVIOR⚡⛔")
        __fullDebugPrint(self, railID, dropID, xProj, maxPos, minPos, sliderID)
        raise ValueError("Unexpected behavior")

    # Current toolhead was assigned, now we need to position the previous slider, if it was skipped
    if (
        self.sliders[railID][sliderID - 1].state == SKIPPED
        or self.sliders[railID][sliderID - 1].state == SKIP_N_WAIT
    ):
        __setPreviousSlider(self, railID, sliderID - 1)


def __getMinMaxPos(self, sliderID: int, railID: int):
    if self.sliders[railID][sliderID].firstWait:
        minPos = self.param["slider"]["firstCableLength"] + sliderID * (
            self.param["slider"]["cableLength"] - self.param["slider"]["safetyMargin"]
        )
        maxPos = (
            minPos
            + self.param["slider"]["cableLength"]
            - self.param["slider"]["safetyMargin"]
        )
    else:
        # First condition is to prevent collision with the previous slider
        minCond1 = self.sliders[railID][sliderID - 1].xPos + self.carriageSafetyMargin
        # Second condition is to prevent collision with the previous slider's arm
        previousSliderTarget = self.sliders[railID][sliderID - 1].xPos + self.param[
            "slider"
        ]["armLength"] * np.cos(self.sliders[railID][sliderID - 1].armAngle)
        minCond2 = previousSliderTarget + self.pickUpSafetyMargin
        minPos = max(minCond1, minCond2)

        # First condition is to prevent going beyong the cable limit
        maxCond1 = (
            self.sliders[railID][sliderID - 1].maxPos
            + self.param["slider"]["cableLength"]
            - self.param["slider"]["safetyMargin"]
        )
        # Second condition is to prevent going out of the working area.
        maxCond2 = (
            self.param["map"]["maxX"]
            - (self.param["beam"]["nbSliderPerRail"] - sliderID - 1)
            * self.carriageSafetyMargin
        )
        if maxCond2 < maxCond1:
            print(f"Using second condition for maxCond {maxCond2}")
        maxPos = min(maxCond1, maxCond2)
    return minPos, maxPos


def __setPreviousSlider(self, railID, sliderID):
    """Sets the position of the previous ID if it was skipped."""
    newPos = (
        self.sliders[railID][sliderID + 1].xPos
        - self.param["slider"]["cableLength"]
        + self.param["slider"]["safetyMargin"]
    )

    if newPos > self.sliders[railID][sliderID].minPos:
        self.sliders[railID][sliderID].xPos = newPos
    else:
        self.sliders[railID][sliderID].xPos = self.sliders[railID][sliderID].minPos

    if sliderID != 0:
        if (
            self.sliders[railID][sliderID - 1].state == SKIPPED
            or self.sliders[railID][sliderID - 1].state == SKIP_N_WAIT
        ):
            __setPreviousSlider(self, railID, sliderID - 1)


def __assignSlider(
    self,
    dropID: int,
    railID: int,
    sliderID: int,
    pos: float,
    dropPos: float = None,
    angle: float = None,
    isAssignedDrop: bool = True,
    maxPos: float = None,
    minPos: float = None,
):
    """
    Assigns the slider to the target, and updates the target's status.
    If isAssignedTarget is set to false, the angle doesn't need to be provided, as it will be
    defaulted to pi/2.
    """

    if (
        self.sliders[railID][sliderID].state == SKIP_N_WAIT
        or self.sliders[railID][sliderID].state == WAITING
    ):
        self.sliders[railID][sliderID].dropPos = dropPos

    self.sliders[railID][sliderID].xPos = pos

    if isAssignedDrop:
        if angle is None:
            raise ValueError("Angle must be provided when assigning a drop location")
        self.sliders[railID][sliderID].maxPos = pos
        self.sliders[railID][sliderID].armAngle = angle
        self.sliders[railID][sliderID].state = PLACING
        self.dropStatus[dropID] = ASSIGNED
    else:
        self.sliders[railID][sliderID].armAngle = self.sign(railID) * np.pi / 2
        if maxPos is None or minPos is None:
            raise ValueError(
                "Max and Min position must be provided when skipping a target"
            )
        self.sliders[railID][sliderID].maxPos = maxPos
        self.sliders[railID][
            sliderID
        ].minPos = minPos  ## be careful, this may be bad in case we have 3+
        # sliders, and we are on slider 1, for instance (the minimum would prevent next sliders to reach
        # some drop locations)

        # add case where a slider skips bcs pos is out of range, but it still has a target to drop


def __fullDebugPrint(self, railID, dropID, xProj, maxPos, minPos, sliderID):
    logging.debug(
        f"\nTarget ID: {dropID}, position: {self.listDrop[dropID]}. \n"
        f"Current slider ID:{sliderID} \n"
        f"Last slider's position : {self.sliders[railID][sliderID-1].xPos:.2f}, Last "
        f"slider's maxPos is {self.sliders[railID][sliderID-1].maxPos:.2f}\n"
        f"xProj : {xProj:.2f}, MaxPos is {maxPos:.2f}, Min pos : {minPos:.2f}."
    )


###-----------------Public methods-----------------###


def assignDestination(self):
    """
    Assigns a destination to the sliders, for them to drop the targets.
    """
    for railID in range(len(self.sliders)):
        if self.railStatus[railID] != CAN_PLACE:
            continue

        __availableSlots(self, railID)
        for sliderID in range(self.param["beam"]["nbSliderPerRail"]):
            if self.listAvailableDropID.size == 0:
                self.railStatus[railID] = WAIT_CONVEYOR
                return

            self.railStatus[railID] = PLACING
            __dropLocationAssignement(self, railID, sliderID)

    # checks if all sliders are ready (useful in the real world scenarios)


""" TODO
- Create a function that assigns a destination to the sliders, for them to drop the targets.
- Then create a queue of event for each slider, as they may not be able to drop their target at the same time
- Create a function that will prepare the sliders for the travel
- Use the states of the sliders
"""
