import numpy as np
import logging
import math_func as mf

from constants import *

def __checkInRange(self, railID:int): 
    """
    Checks if there are any object in the range of the target rail

    Args:
        railID (int): Select the corresponding rail

    Returns:
        listAvailableTargetID(list): List of indices of listTarget that are in the range of the rail
    """
    sign = self.sign(railID)
    relativePosition = sign * (self.axisYPosList[railID] - self.listTarget[:,1])
    
    condition1 = self.param['slider']['armLength']
    condition2 = self.param['beam']['railOffset'] - self.pickUpSafetyMargin/2
    
    listTemp1 = np.argwhere(-relativePosition < condition1)
    listTemp2 = np.argwhere( relativePosition < condition2)
    self.listAvailableTargetID = np.intersect1d(listTemp1, listTemp2)
    
    if self.listAvailableTargetID.size > 0:
        tempList = self.listAvailableTargetID
        tempList = tempList[np.where(self.targetStatus[tempList] == FREE)]
        ## Sorts the list. Necessary ! Sets the priority for the search.
        self.listAvailableTargetID = tempList[np.argsort(self.listTarget[tempList][:,0], axis=0)]


def __sliderAssignment(self, railID:int, sliderID:int):
    """
    Assigns the slider to the closest object, and the second slider to the second closest object if 
    there is one, and so on.

    Args:
        listAvailableTargetID (list): List of indices of listTarget that are in the range of the rail
        railID (int): ID of the coresponding rail
    """         
    while True:
        # We take the first element of the list, as all the 'busy' one are removed progressively
        targetID = self.listAvailableTargetID[0] 
        xProj, angle = mf.compute_dist_angle(self.param['slider']['armLength'], 
                                             self.axisYPosList[railID], 
                                             self.listTarget[targetID,1])
        if sliderID == 0:
            __firstSliderPick(self, targetID, railID, sliderID, xProj, angle)
        else:
            __nextSliderPick(self, targetID, railID, sliderID, xProj, angle)
        
        if not(self.targetStatus[targetID] == FREE): 
            self.listAvailableTargetID = np.delete(self.listAvailableTargetID, 0, axis=0) 
            
        if not(self.targetStatus[targetID] == SKIPPED):
            break 
        
        if len(self.listAvailableTargetID) == 0: 
            __setRemainingPosition(self, railID, sliderID)
            break

            
def __firstSliderPick(self, targetID:int, railID:int, sliderID:int, xProj:float, angle:float):
    """Checks if the desired target is valid for the first slider. If it is, picks it up, otherwise, 
    skips it. If it is out of range, it skips the sliders instead

    Args:
    
        targetID (int): ID of the target in the self.listTarget list
        railID (int): ID of the rail in self.sliders
        sliderID (int): ID of the slider in self.sliders
        xProj (float): Projection of the target on the X-axis
        angle (float): Angle required to reach the target

    Raises:
        ValueError: This function should only be called for the first slider. If it is not the case,
        it will raise an error
    """
    if sliderID != 0:
        raise ValueError('This function should only be called for the first slider')
    
    minCond = self.param['conveyor']['endXPosition'] - self.param['conveyor']['width']
    maxCond = self.param['slider']['firstCableLength'] - self.param['slider']['safetyMargin']

    relativePos_armForward  = self.listTarget[targetID,0] - xProj
    
    if relativePos_armForward > maxCond:
        logging.debug(f"[{railID}.{sliderID}] - Target out of range, going to the next slider")
        newPos = minCond
        __assignSlider(self, targetID, railID, sliderID, newPos, isAssignedTarget=False, 
                       maxPos=maxCond, minPos=minCond) 
        
    elif relativePos_armForward < self.param['slider']['firstCableLength']:
        newPos = relativePos_armForward
        newAngle = angle
        __assignSlider(self, targetID, railID, sliderID, newPos, newAngle)
        logging.debug(f"[{railID}.{sliderID}] - First slider assigned to target {targetID}. Target "
                      f"pos is {self.listTarget[targetID,0]:.2f}")
    else:
        logging.debug(f"[{railID}.{sliderID}] - First slider skipped the target {targetID}. Target "
                      f"pos is {self.listTarget[targetID,0]:.2f}")
        self.targetStatus[targetID] = SKIPPED
    
    
def __nextSliderPick(self, targetID:int, railID:int, sliderID:int, xProj:float, angle:float):
    """Checks if the desired target is valid for the non-first slider. If it is, picks it up, otherwise,
    skips it.  If it is out of range, it skips the sliders instead

    Args:
        targetID (int): ID of the target in the self.listTarget list
        railID (int): ID of the rail in self.sliders
        sliderID (int): ID of the slider in self.sliders
        xProj (float): Projection of the target on the X-axis
        angle (float): Angle required to reach the target

    Raises:
        ValueError: This function should only be called for the non-first slider. If it is not the case,
        it will raise an error
    """
    if sliderID == 0:
        raise ValueError('This function should only be called for the first slider')
    minPos, maxPos = __getMinMaxPos(self, sliderID, railID)
    relativePos_armBackward = self.listTarget[targetID,0] + xProj
    relativePos_armForward  = self.listTarget[targetID,0] - xProj
    
    # Check if the target is too close to the previous slider
    if relativePos_armBackward < minPos:
        self.targetStatus[targetID] = SKIPPED
        logging.debug(f"[{railID}.{sliderID}] - Target too close to the previous slider. Skipping it")
        return 
    
    # Check if the target is too far for the current slider. 
    if relativePos_armForward > maxPos:
        logging.debug(f"[{railID}.{sliderID}] - Target out of range, going to the next slider")
        newPos = minPos
        __assignSlider(self, targetID, railID, sliderID, newPos, isAssignedTarget=False, 
                       maxPos=maxPos, minPos=minPos)
        return
    
    elif relativePos_armForward > minPos:
        logging.debug(f"[{railID}.{sliderID}] - Going for the closest possible position for target {targetID}")
        newPos   = relativePos_armForward
        newAngle = angle
        __assignSlider(self, targetID, railID, sliderID, newPos, newAngle)
        
    elif relativePos_armBackward < maxPos:
        logging.debug(f"[{railID}.{sliderID}] - Going for the furthest possible position for target {targetID}")
        newPos   = relativePos_armBackward
        newAngle = np.pi - angle
        __assignSlider(self, targetID, railID, sliderID, newPos, newAngle)
        
    else:
        logging.error(f"[{railID}.{sliderID}] - ⛔⚡UNEXPECTED BEHAVIOR⚡⛔")
        __fullDebugPrint(self, railID, targetID, xProj, maxPos, minPos, sliderID)
        raise ValueError("Unexpected behavior")
    
    # Current toolhead was assigned, now we need to position the previous slider, if it was skipped
    if self.sliders[railID][sliderID-1].state == SKIPPED:
        __setPreviousSlider(self, railID, sliderID-1)


def __getMinMaxPos(self, sliderID, railID):
    # First condition is to prevent collision with the previous slider
    minCond1 = self.sliders[railID][sliderID-1].xPos + self.carriageSafetyMargin
    # Second condition is to prevent collision with the previous slider's arm
    previousSliderTarget = self.sliders[railID][sliderID-1].xPos + \
                           self.param['slider']['armLength'] * \
                           np.cos(self.sliders[railID][sliderID-1].armAngle)
    minCond2 = previousSliderTarget + self.pickUpSafetyMargin
    minPos = max(minCond1, minCond2)
    
    # First condition is to prevent going beyong the cable limit
    maxCond1 = self.sliders[railID][sliderID-1].maxPos + \
               self.param['slider']['cableLength'] - \
               self.param['slider']['safetyMargin']
    # Second condition is to prevent going out of the working area.
    maxCond2 = self.param['map']['maxX'] - \
               (self.param['beam']['nbSliderPerRail'] - sliderID - 1) * \
               self.carriageSafetyMargin
    if maxCond2 < maxCond1:
        print(f"Using second condition for maxCond {maxCond2}")
    maxPos = min(maxCond1, maxCond2)
    return minPos, maxPos


def __setPreviousSlider(self, railID, sliderID):
    """Sets the position of the previous ID if it was skipped."""
    newPos = self.sliders[railID][sliderID+1].xPos - \
             self.param['slider']['cableLength'] + \
             self.param['slider']['safetyMargin']
             
    if newPos > self.sliders[railID][sliderID].minPos:
        self.sliders[railID][sliderID].xPos = newPos
    else:
        self.sliders[railID][sliderID].xPos = self.sliders[railID][sliderID].minPos
        
    if sliderID != 0:
        if self.sliders[railID][sliderID-1].state == SKIPPED:
            __setPreviousSlider(self, railID, sliderID-1)
        

def __setRemainingPosition(self, railID: int, sliderID: int):
    """
    Assigns the slider's position when there's no more target available

    Args:
        railID (int): ID of the rail it should use. Starts at 0.
        slider (int): ID of the slider it should use. Starts at 0.
    """
    if sliderID == 0:
        self.sliders[railID][sliderID].xPos = self.param['slider']['carriageWidth']/2
    else:
        self.sliders[railID][sliderID].xPos = self.sliders[railID][sliderID-1].xPos + \
                                            self.carriageSafetyMargin
                                
    self.sliders[railID][sliderID].armAngle = self.sign(railID) * np.pi/2 
    
    
def __assignSlider(self, targetID:int, railID:int, sliderID:int, pos:float, angle:float = None, 
                   isAssignedTarget:bool = True, maxPos:float = None, minPos:float = None):
    """
    Assigns the slider to the target, and updates the target's status. 
    If isAssignedTarget is set to false, the angle doesn't need to be provided, as it will be 
    defaulted to pi/2.
    """
    self.sliders[railID][sliderID].xPos = pos
        
    if isAssignedTarget:
        if angle is None:
            raise ValueError('Angle must be provided when assigning a target')
        self.sliders[railID][sliderID].maxPos   = pos
        self.sliders[railID][sliderID].armAngle = angle
        self.sliders[railID][sliderID].state    = PICKING
        self.targetStatus[targetID]             = ASSIGNED
    else:
        self.sliders[railID][sliderID].armAngle = self.sign(railID) * np.pi/2
        self.sliders[railID][sliderID].state    = SKIPPED
        if maxPos is None or minPos is None:
            raise ValueError('Max and Min position must be provided when skipping a target')
        self.sliders[railID][sliderID].maxPos = maxPos
        self.sliders[railID][sliderID].minPos = minPos
        
        
def __fullDebugPrint(self, railID, targetID, xProj, maxPos, minPos, sliderID):
    logging.debug(f"\nTarget ID: {targetID}, position: {self.listTarget[targetID]}. \n"
                    f"Current slider ID:{sliderID} \n"
                    f"Last slider\'s position : {self.sliders[railID][sliderID-1].xPos:.2f}, Last "
                    f"slider\'s maxPos is {self.sliders[railID][sliderID-1].maxPos:.2f}\n"
                    f"xProj : {xProj:.2f}, MaxPos is {maxPos:.2f}, Min pos : {minPos:.2f}.")
        
###-----------------Public methods-----------------###
        
def assignSlider(self):
    """The strategy we will first adopt is to take the closest object to the side, and assign it
    to the first slider. Then, we check for the second closest object. If it won't generate a 
    collision with the first slider, we assign it to the second slider, otherwise we skip it. 
    However, we must make sure the distance doesn't exceed the cable length + the arm's 
    length, while taking into consideration the angle of both arm. If it does, we skip the 
    object."""
    for railID in range(len(self.sliders)): 
        if self.railStatus[railID] != CAN_PICK:
            continue
        
        __checkInRange(self, railID)
        for sliderID in range(self.param['beam']['nbSliderPerRail']):
            if self.listAvailableTargetID.size > 0:
                self.railStatus[railID] = PICKING
                __sliderAssignment(self, railID, sliderID)
            else:
                __setRemainingPosition(self, railID, sliderID)
            logging.debug(f"#-------------- Slider {sliderID} - Done--------------#")
        logging.debug(f"#--------------- Rail {railID} - Done---------------#")
    logging.debug("#--------------------------------------------------#")
