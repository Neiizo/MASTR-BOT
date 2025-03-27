import numpy as np
import json
import logging
import TargetPickUp as pick
import TargetDrop as drop
from math_func import *

from constants import *


class Map:
    """
    This is the class that defines the environment of the robot. It contains the limit of the
    environement, and everything inside of it
    """

    ###-----------------Private methods-----------------###

    def __init__(self, jupyter: bool = False):
        """
        The constructor for MyClass class.

        Args:
            jupyter (bool) : Param used in case we want to call this from a jupyter notebook. This
            changes the path requires to load and save the parameters.
        """
        if jupyter:
            with open("map_param.json", "r") as f:
                self.param = json.load(f)
        else:
            with open("ExcenterAlgoPython/map_param.json", "r") as f:
                self.param = json.load(f)

        self.__moveCounter = 0  # Counter that keeps track of the conveyor's movement and add targets when needed

        self.listTarget = np.empty((0, 2))
        self.targetStatus = np.zeros(0)
        self.axisYPosList = []
        self.sliders = []
        self.axisYPosList = []

        self.carriageSafetyMargin = (
            self.param["slider"]["safetyMargin"] + self.param["slider"]["carriageWidth"]
        )
        self.pickUpSafetyMargin = (
            self.param["slider"]["safetyMargin"] + self.param["slider"]["pickUpArea"]
        )
        self.__createSliderList()
        self.__generateTargets()
        self.__generateDropLocationsPattern()
        self.railStatus = np.ones(len(self.sliders)) * CAN_PICK

    def __createSliderList(self):
        """
        Initializes the list of sliders, using the parameters defined in the map_param.json file
        """
        for i in range(self.param["beam"]["nbYAxis"]):
            axisCenter = (
                self.param["beam"]["firstAxisYPos"]
                + self.param["beam"]["axisSpacing"] * i
            )
            if self.param["beam"]["isDualRailPerAxis"]:
                self.axisYPosList.append(axisCenter - self.param["beam"]["railOffset"])
                self.axisYPosList.append(axisCenter + self.param["beam"]["railOffset"])
            else:
                self.axisYPosList.append(axisCenter)

        for i, yPos in enumerate(self.axisYPosList):
            slider_temp = []
            for j in range(self.param["beam"]["nbSliderPerRail"]):
                slider_temp.append(Slider(yPos=yPos))
                slider_temp[-1].xPos = (
                    self.param["slider"]["carriageWidth"] / 2
                    + j * self.carriageSafetyMargin
                )

                slider_temp[-1].armAngle = (
                    self.sign(i) * np.pi / 2
                )  ## make this dynamic with the side of the sliders wrt the axis
            self.sliders.append(slider_temp)

    def __generateTargets(self):
        """
        Generates a new line of target, according to the specification of the map_param.json
        The format of listTarget will be Nx2.
        The format of targetStatus will be Nx1.
        This will be replaced by the target detection in a later date
        """
        conveyorStart = (
            self.param["conveyor"]["endXPosition"] - self.param["conveyor"]["width"]
        )
        for i in range(self.param["target"]["targetPerRow"]):
            xPos = (
                conveyorStart
                + i * self.param["target"]["targetXSpacing"]
                + np.random.normal(scale=np.sqrt(3**2))
                + self.param["target"]["xOffset"]
            )
            # Sets it outside of the map, simply for better visualization. It serves no other purpose.
            yPos = -5 + np.random.normal(scale=np.sqrt(3**2))
            self.listTarget = np.append(self.listTarget, [[xPos, yPos]], axis=0)
            self.targetStatus = np.append(self.targetStatus, 0)

    def __generateDropLocationsPattern(self):

        dropRegionStart = self.param["dropRegion"]["startXPosition"]
        xOffset = self.param["dropTarget"]["xOffset"]
        nbRow = self.param["beam"]["nbYAxis"]

        ### Generate / import pattern
        if self.param["dropTarget"]["pattern"] == "imported":
            try:
                pattern = np.load("ExcenterAlgoPython/pattern.npz")
            except:
                raise Exception(
                    "The pattern provided is not valid. Please provide a valid pattern"
                )
        else:
            try:
                pattern = globals()[
                    "interpolate_" + self.param["dropTarget"]["pattern"]
                ](
                    self.param["dropTarget"]["patternWidth"],
                    self.param["dropTarget"]["nbTargetPerPattern"],
                )
            except:
                raise Exception(
                    "The pattern provided is not valid. Please provide a valid pattern"
                )

        ### create a single row, and keeps the layout stored, to create new patterns in the future
        pattern += (
            xOffset + dropRegionStart,
            self.param["beam"]["firstAxisYPos"]
            + self.param["beam"]["axisSpacing"] * (nbRow - 1),
        )
        self.basePattern = pattern.copy()
        for _ in range(1, self.param["dropTarget"]["nbPatternPerRow"]):
            pattern[:, 0] += self.param["dropTarget"]["patternSpacing"]
            self.basePattern = np.append(self.basePattern, pattern, axis=0)

        self.listDrop = np.repeat(self.basePattern[np.newaxis, :, :], nbRow, axis=0)
        for row in range(nbRow):
            self.listDrop[row, :, 1] -= self.param["beam"]["axisSpacing"] * row

        self.dropStatus = np.ones(self.listDrop.shape[:2]) * FREE

    def __generateDropLocations(self):
        """
        Generates new drop locations for the targets, by using self.basePattern. This also means
        removing one row of drop locations.
        To be called when a line is full !! TODO
        """
        self.listDrop = self.listDrop[1:, :, :]
        self.dropStatus = self.dropStatus[1:, :]

        self.listDrop[:, :, 1] -= self.param["beam"]["axisSpacing"]
        self.listDrop = np.append(
            self.listDrop, self.basePattern[np.newaxis, :, :], axis=0
        )

        self.dropStatus = np.append(
            self.dropStatus, np.ones(self.basePattern.shape[0]) * FREE, axis=0
        )

    def __moveTargets(self, dist: float):
        """Moves the targets by a certain distance

        Args:
            dist (float): Distance to move the target by. Supposed to be the conveyor's distance
            travelled since the last itteration.
        """
        self.listTarget[:, 1] += dist

    #    ###-----------------Public methods-----------------###

    def update(self, dist: float = 100):
        """
        Updates the map by moving the targets by a certain distance
        """
        self.__moveCounter += dist
        self.__moveTargets(dist)
        if self.__moveCounter > self.param["target"]["targetYSpacing"]:
            self.__moveCounter = 0
            self.__generateTargets()
        pick.assignSlider(self)
        drop.assignDestination(self)

        ## Simulates the state changing. This will be done via code later
        for railID in range(len(self.sliders)):
            ## match case doesn't seem to work with constants, for some reasons. There will be the waiting, and travelling states
            # we could use itertools.cycle instead
            if self.railStatus[railID] == PICKING:
                self.railStatus[railID] = CAN_PICK  # MAYBE THATS WHY IT DOESNT DROP YET
            elif self.railStatus[railID] == PLACING:
                self.railStatus[railID] = DONE_PLACING
                # EXECUTE BUFFER HERE INSTEAD
            elif self.railStatus[railID] == DONE_PLACING:
                self.railStatus[railID] = CAN_PICK

    def sign(self, railID: int):
        if self.param["beam"]["isDualRailPerAxis"]:
            sign = -1 if railID % 2 == 0 else 1
        else:
            sign = -1
        return sign


class Slider:
    def __init__(self, yPos):
        self.xPos = 0
        self.yPos = yPos
        self.armAngle = 0  ## WARNING, THE ANGLE IS ONLY REVERSED FOR THE VISUALISATION, IN REAL TIME IT'S DIFFERENT
        self.maxPos = 0
        self.minPos = 0
        self.height = 0  # TODO
        self.headRotation = None  # TODO
        self.speed = 0  # TODO
        self.accel = 0  # TODO
        self.jerk = 0  # TODO

        self.state = CAN_PICK  # States are described in constants.py
