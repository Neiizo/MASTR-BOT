import numpy as np
from description.constants import *
import description.config as cfg


class Object:
    def __init__(self, param, DoF):
        """This is the interface for using ruckig. Every variables necessary for computing
        trajectories using this library are defined here.


        Args:
            param (dict): Dictionary containing the parameters of the object
            DoF (int): Degree of freedom of the object
        """
        self.DoF = DoF
        self.position = [0] * DoF  # Coords are [x] or [x, y, z]
        self.currentVelocity = [0] * DoF  # Coords are [v_int, v_out] or [v_x, v_y, v_z]
        if "max_jerk" in param:
            self.maxJerk = [val for val in param["max_jerk"]]
            self.currentAcceleration = [0] * DoF  # Coords are [a_x] or [a_x, a_y, a_z]
        self.targetPosition = [0] * DoF  # Coords are [x] or [x, y, z].

        # Shouldn't be changed at first
        self.maxVelocity = [val for val in param["speed"]]
        self.maxAccel = [val for val in param["accel"]]

        self.new_position = [0] * DoF
        self.deltaMove = [0] * DoF


class Conveyor(Object):
    # NOTE maybe change this so every conveyor is an object, instead of inside a list inside conveyor. makes it future proof

    def __init__(self, params):
        param = params["conveyor"]
        super().__init__(param, 2)

        self.deltaMove = [val * params["timeStep"] for val in param["speed"]]
        # Movement's parameters

        self.inDirection = param["inDirection"]
        self.outDirection = param["outDirection"]
        self.xOffset = param["xOffset"]
        self.conveyorOffset = param["conveyorOffset"]

        # Conveyor's paramters
        self.length = param["length"]
        self.isSingleColor = param["isSingleColor"]
        self.inRowSpacing = param["inRowSpacing"]
        self.packagesRowSpacing = param["packagesRowSpacing"]

        self.listOutConveyor = []
        self.listInConveyor = []
        self.listPicks = {}
        self.listDrops = {}
        self.listUnfilledPackages = []
        self.badProductRatio = param["badProductRatio"]
        self.nPickGenerations = self.nDropGenerations = 0
        self.pickWidth = params["target"]["width"]
        self.tOffset = None
        self.rowInOffsetID = 0
        for i in range(param["nbInConveyor"]):
            temp = {
                "stepStatus": "idle",  ## define the status in an external file
                "width": param["inWidth"][i],
                "itemsPerRow": param["inItemsPerRow"][i],
                "endPos": [val for val in param["inEndPos"][i]],
                "patternRowPos": None,
                "patternIDs": None,
            }
            self.rowInOffsetID += temp["itemsPerRow"]
            self.listInConveyor.append(temp)

        self.errorMargin = param["errorMargin"]
        self.packageOffsetID = 0
        for i in range(param["nbOutConveyor"]):
            temp = {
                "stepStatus": "idle",  ## define the status in an external file
                "width": param["outWidth"][i],
                "itemsPerRow": param["outItemsPerRow"][i],
                "endPos": [val for val in param["outEndPos"][i]],
                "patternPackagesPos": None,
                "patternPackagesIDs": None,
                "patternRowIDs": None,
            }
            self.listOutConveyor.append(temp)
            self.packageOffsetID += temp["itemsPerRow"] * param["nPackagesRow"]
        self.nPackagesRow = param["nPackagesRow"]
        self.packagesRowSplitting = param["packagesRowSplitting"]
        self.packagesRowSplitSpacing = param["packagesRowSplitSpacing"]
        self.dropSideOffset = param["dropSideOffset"]
        self.packagesExtraSpacing = param["packagesExtraSpacing"]
        self.deltaConveyorPos = (
            self.listInConveyor[-1]["endPos"][self.inDirection[ORTHOG_DIR]]
            - self.listOutConveyor[-1]["endPos"][self.outDirection[ORTHOG_DIR]]
        )
        self.extraLookingRange = None

    def generatePicks(self, offsetDistance):
        """Generate a new row of picks for each input conveyor, using the generated pattern

        Args:
            offsetDistance (float): Distance offset from the starting position for the new generation
        """
        for idx, conveyor in enumerate(self.listInConveyor):
            "Generate the pick's pattern if it hasn't already been done"
            if conveyor["patternRowPos"] is None:
                self.generatePickPattern(conveyor, idx)

            "Computes the new position of the picks using the pattern generated"
            DoI = np.array(self.inDirection)
            startPos = conveyor["endPos"] - DoI * (self.length + offsetDistance)
            itemsPerRow = conveyor["itemsPerRow"]
            rowPosPattern = conveyor["patternRowPos"]
            newPos = (
                rowPosPattern
                + startPos
                + np.random.normal(scale=np.sqrt(0.5), size=(itemsPerRow, 2))
            )

            "Determines the quality of the products."
            badCondition = np.random.random_sample(itemsPerRow) < self.badProductRatio
            newStatus = np.where(badCondition, BAD, FREE).tolist()

            "Generate new entries for each picks"
            for i in range(len(rowPosPattern)):
                newID = self.nPickGenerations * self.rowInOffsetID + i
                self.listPicks[newID] = {
                    "pos": newPos[i],
                    "status": newStatus[i],
                    "rowID": self.nPickGenerations,
                    "conveyorID": idx,
                }

        self.nPickGenerations += 1

    def generateDrops(self, offsetDistance):
        for conveyor in self.listOutConveyor:
            "Generate the package's pattern if it hasn't already been done"
            if conveyor["patternPackagesPos"] is None:
                self.generateDropPattern(conveyor)

            "Computes the new position of the drops using the pattern generated"
            DoI = np.array(self.outDirection)
            startPos = (
                conveyor["endPos"]
                - DoI * (self.length + offsetDistance)
                - DoI * self.packagesExtraSpacing
            )
            # * pourquoi il y a extra dist encore ici
            "Generate new entries for each drops"
            for i in range(len(conveyor["patternPackagesPos"])):
                newID = self.nDropGenerations * self.packageOffsetID + i
                self.listDrops[newID] = {
                    "pos": conveyor["patternPackagesPos"][i] + startPos,
                    "status": NORMAL,
                    "packageID": self.nDropGenerations * conveyor["newIDOffset"]
                    + conveyor["patternPackagesIDs"][i],
                    "rowID": conveyor["patternRowIDs"][i]
                    + self.nDropGenerations * self.nPackagesRow,
                }

        self.nDropGenerations += 1

    def generatePickPattern(self, conveyor, idx):
        """Generate the pattern for a given input conveyor

        Args:
            conveyor (dict): Item from the list self.listInConveyor
            idx (int): indices of the given conveyor inside self.listInConveyor
        """
        DoI = np.array(self.inDirection)
        nPickPerRow = conveyor["itemsPerRow"]
        width = conveyor["width"]
        pickWidth = self.pickWidth
        inRowPos = np.linspace(
            -(width - pickWidth) / 2, (width - pickWidth) / 2, nPickPerRow
        )
        if np.abs(DoI[1]) == 1:
            rowPatternPos = np.array(np.meshgrid(inRowPos, [0])).T.reshape(-1, 2)
        else:
            rowPatternPos = np.array(np.meshgrid([0], inRowPos)).T.reshape(-1, 2)
        patternIDs = np.arange(0, nPickPerRow)

        conveyor["patternRowPos"] = rowPatternPos
        conveyor["patternIDs"] = patternIDs
        if idx == 0:
            conveyor["IDOffset"] = 0
        else:
            conveyor["IDOffset"] = self.listInConveyor[idx - 1]["IDOffset"] + (
                self.listInConveyor[idx - 1]["itemsPerRow"]
            )

    def generateDropPattern(self, conveyor):
        """Generate the pattern for a given output conveyor

        Args:
            conveyor (dict): Item from the list self.listOutConveyor
        """
        nDropPerRow = conveyor["itemsPerRow"]
        rowSpacing = self.packagesRowSpacing
        packageSpacing = (
            self.packagesRowSplitSpacing if self.packagesRowSplitting else None
        )
        sideOffset = self.dropSideOffset
        nRow = self.nPackagesRow
        DoI = np.array(self.outDirection)
        width = conveyor["width"]
        halfWidth = (width - sideOffset - packageSpacing) / 2
        yPos = np.linspace(-halfWidth, halfWidth, nDropPerRow)
        if packageSpacing is not None:
            yPos += np.where(yPos > 0, packageSpacing / 2, -packageSpacing / 2)

        xPos = np.linspace(0, (nRow - 1) * rowSpacing * DoI[DoI[SAME_DIR]], nRow)

        if np.abs(DoI[SAME_DIR]) == 1:
            packagePattern = np.array(np.meshgrid(yPos, xPos)).T.reshape(-1, 2)
        else:
            packagePattern = np.array(np.meshgrid(xPos, yPos)).T.reshape(-1, 2)

        if packageSpacing is not None:
            dropPackageID = np.where(packagePattern[:, DoI[ORTHOG_DIR]] > 0, 1, 0)
            newIDOffset = 2
        else:
            dropPackageID = np.zeros(len(packagePattern))
            newIDOffset = 1

        conveyor["patternPackagesPos"] = packagePattern
        conveyor["patternPackagesIDs"] = dropPackageID
        conveyor["patternRowIDs"] = np.digitize(packagePattern[:, DoI[SAME_DIR]], xPos)
        conveyor["newIDOffset"] = newIDOffset

    def moveConveyors(self, t: int, start=False):
        """Computes the delta position between the last and the current frame, and apply it to
        the list of picks and drops.

        Args:
            t (int): current time frame of the simulation
        """
        " Computes an offset in time, to make sure both feeds meet at an adequate timing"
        if self.tOffset is None:
            meetingDistance = (
                self.deltaMove[1]
                / (self.deltaMove[0] + self.deltaMove[1])
                * self.length
            )
            # meetingDistance = self.length / 2
            self.tOffset = meetingDistance * (
                1 / (self.deltaMove[0]) - 1 / (self.deltaMove[1])
            )

        ## only works for one type of direction TEST
        if not (t < -self.tOffset > 0):
            "Moves the picks if the tOffset is respected, and generates new ones when needed"
            self.new_position[0] = self.new_position[0] + self.deltaMove[0]
            distanceSinceLastGen = (
                self.new_position[0] - self.inRowSpacing * self.nPickGenerations
            )
            if distanceSinceLastGen > 0:
                self.generatePicks(distanceSinceLastGen)
            self.movePicks(t, self.deltaMove[0] * np.array(self.inDirection))

        if not (t < self.tOffset > 0):
            "Moves the drops if the tOffset is respected, and generates new ones when needed"
            self.new_position[1] = self.new_position[1] + self.deltaMove[1]
            distanceSinceLastGen = (
                self.new_position[1]
                - (
                    self.packagesRowSpacing * (self.nPackagesRow)
                    + self.packagesExtraSpacing
                )
                * self.nDropGenerations
            )
            if distanceSinceLastGen > 0:
                self.generateDrops(distanceSinceLastGen)
            self.moveDrops(t, self.deltaMove[1] * np.array(self.outDirection))

        if (
            self.new_position[1] > self.length
            and cfg.listStat[-1]["startRecordingTime"] == 0
        ):
            """Register the time a full length has been reached with packages. Used to track stats
            and ignore the launch offset in performance"""
            cfg.listStat[-1]["startRecordingTime"] = t
        if (
            self.new_position[0] > self.length
            and cfg.listStat[-1]["startRecordingTime_2"] == 0
        ):
            """Register the time a full length has been reached with packages. Used to track stats
            and ignore the launch offset in performance"""
            cfg.listStat[-1]["startRecordingTime_2"] = t

    def movePicks(self, t, dist):
        """Checks if each pick is still inside the workspace, deletes the ones that are not
        and apply the deltaMove to the ones that are"""
        pickToDelete = []
        idToDel = []
        DoI = self.inDirection[SAME_DIR]
        signDoI = self.inDirection[DoI]
        posLimit1 = self.listInConveyor[-1]["endPos"][DoI]
        posLimit2 = self.listInConveyor[-1]["endPos"][DoI] - self.length * signDoI
        minPos = min(posLimit1, posLimit2)
        maxPos = max(posLimit1, posLimit2)

        for pickID in self.listPicks:
            self.listPicks[pickID]["pos"] += dist
            pos = self.listPicks[pickID]["pos"]
            rowID = self.listPicks[pickID]["rowID"]
            condMax = maxPos + BORDER_TOLERANCE
            condMin = minPos - BORDER_TOLERANCE

            if not (condMin < pos[DoI] < condMax) and rowID not in idToDel:
                idToDel.append(rowID)

            if rowID in idToDel:
                pickToDelete.append(pickID)
                if self.listPicks[pickID]["status"] not in (GONE, BAD):
                    cfg.listStat[-1]["missedPicks"] += 1
                    cfg.listStat[-1]["timeMissedPicks"].append(t)

        self.deletePick(pickToDelete)

    def moveDrops(self, t, dist):
        """Checks if each packages is still inside the workspace, deletes the ones that are not
        and apply the deltaMove to the ones that are"""
        DoI = self.outDirection[SAME_DIR]
        signDoI = self.outDirection[DoI]
        posLimit1 = self.listOutConveyor[-1]["endPos"][DoI]
        posLimit2 = self.listOutConveyor[-1]["endPos"][DoI] - self.length * signDoI
        minPos = min(posLimit1, posLimit2)
        maxPos = max(posLimit1, posLimit2)
        dropToDelete = []
        idToDel = []
        for dropID in (
            reversed(list(self.listDrops.keys())) if signDoI < 0 else self.listDrops
        ):
            self.listDrops[dropID]["pos"] += dist
            pos = self.listDrops[dropID]["pos"]
            # NOTE: The + 1 is because even if a position is 1000, there is a small imprecision
            # NOTE: making it balance around that value
            condMax = maxPos + (2 * self.packagesExtraSpacing + 1)
            condMin = minPos - (self.packagesExtraSpacing + 1)
            packageID = self.listDrops[dropID]["packageID"]

            if not (condMin < pos[DoI] < condMax) and packageID not in idToDel:
                idToDel.append(packageID)
                cfg.listStat[-1]["totalPackages"] += 1

            if packageID in idToDel:
                dropToDelete.append(dropID)
                if self.listDrops[dropID]["status"] != DONE:
                    cfg.listStat[-1]["missedDrops"] += 1
                    cfg.listStat[-1]["timeMissedDrops"].append(t)
                    if packageID not in self.listUnfilledPackages:
                        self.listUnfilledPackages.append(packageID)
                        cfg.listStat[-1]["unfilledPackages"] += 1
                        # cfg.listStat[-1]["totalPackages"] += 1

        self.deleteDrop(dropToDelete, endCourse=True)

    def deletePick(self, pickID, endCourse=False):
        """Deletes the desired picks from the list of picks

        Args:
            pickID (int or list[int]): the ID of the picks to delete
            endCourse (bool, optional): Wether this is called because we are at the end of the
            conveyor line or no. This is relevant for the stats. Defaults to False.
        """

        def _deletePick(pickID):
            if self.listPicks[pickID]["status"] != BAD:
                cfg.listStat[-1]["totalPicks"] += 1
            del self.listPicks[pickID]

        if isinstance(pickID, list):
            for ID in pickID:
                _deletePick(ID)
        else:
            _deletePick(pickID)

    def deleteDrop(self, dropID, endCourse=False):
        """Deletes the desired drops from the list of drops

        Args:
            dropID (int or list[int]): the ID of the drops to delete
            endCourse (bool, optional): Wether this is called because we are at the end of the
            conveyor line or no. This is relevant for the stats, and because filled drops are
            still shown, until they leave the conveyors. Defaults to False.
        """

        def _deleteDrop(dropID, endCourse=False):
            if endCourse:
                del self.listDrops[dropID]
                cfg.listStat[-1]["totalDrops"] += 1

            else:
                self.listDrops[dropID]["status"] = DONE

        if isinstance(dropID, list):
            for ID in dropID:
                _deleteDrop(ID, endCourse)
        else:
            _deleteDrop(dropID, endCourse)


class Slider(Object):
    def __init__(self, params, ID):
        slider = params["slider"]
        super().__init__(slider, 3)
        self.direction = params["beam"]["direction"]
        self.transformProfile()
        self.ID = ID
        # TODO  Maybe we can do without. it's used once in plotter.py
        self.railPos = None
        # TODO  Maybe we can do without. it's used once in plotter.py
        self.reach = slider["reach"]
        # TODO  Maybe we can do without. it's used once in plotter.py
        self.reachOffset = slider["reachOffset"]
        # TODO  Maybe we can do without. it's used once in plotter.py
        self.depth = slider["depth"]
        self.width = slider["width"]
        self.armWidth = slider["armWidth"]

        self.trackedTargetID = None
        self.safetyMargin = slider["safetyMargin"]
        self.minPosition = [0, slider["reachOffset"], 0]
        self.maxPosition = np.concatenate(
            (
                np.add(
                    np.array(self.direction) * params["beam"]["length"],
                    np.array(self.direction[::-1])
                    * (slider["reach"] + slider["reachOffset"]),
                ),
                [slider["depth"]],
            ),
            axis=0,
        )

        self.status = None
        self.scheduling = None
        self.inScheduling = None
        self.outScheduling = None
        self.start_z_move = 0

    def transformProfile(self):
        """Transforms the profile of the slider to match the direction of the beam"""
        if abs(self.direction[0]) == 1 and abs(self.direction[1]) == 1:
            raise ValueError("The direction of the slider cannot be [1,1]")

        if abs(self.direction[0]) == 0:

            if not abs(self.direction[1]) == 1:
                raise ValueError("The direction of the slider cannot be [0,0]")

            self.maxVelocity = [
                self.maxVelocity[self.direction[SAME_DIR]],
                self.maxVelocity[self.direction[ORTHOG_DIR]],
                self.maxVelocity[-1],
            ]
            self.maxAccel = [
                self.maxAccel[self.direction[SAME_DIR]],
                self.maxAccel[self.direction[ORTHOG_DIR]],
                self.maxAccel[-1],
            ]
        try:  
            self.maxJerk = [
                self.maxJerk[self.direction[SAME_DIR]],
                self.maxJerk[self.direction[ORTHOG_DIR]],
                self.maxJerk[-1],
            ]
        except:
            pass
        # print(self.direction)
        # print(self.maxVelocity)
        # print(self.maxAccel)
        # exit()

    def inverseTransformProfile(self):
        """Transforms the profile of the slider to match the direction of the beam"""
        if abs(self.direction[0]) == 1 and abs(self.direction[1]) == 1:
            raise ValueError("The direction of the slider cannot be [1,1]")

        if abs(self.direction[0]) == 0:

            if not abs(self.direction[1]) == 1:
                raise ValueError("The direction of the slider cannot be [0,0]")

            self.maxVelocity = [
                self.maxVelocity[self.direction[ORTHOG_DIR]],
                self.maxVelocity[self.direction[SAME_DIR]],
                self.maxVelocity[-1],
            ]
            self.maxAccel = [
                self.maxAccel[self.direction[ORTHOG_DIR]],
                self.maxAccel[self.direction[SAME_DIR]],
                self.maxAccel[-1],
            ]
        try:  
            self.maxJerk = [
                self.maxJerk[self.direction[ORTHOG_DIR]],
                self.maxJerk[self.direction[SAME_DIR]],
                self.maxJerk[-1],
            ]
        except:
            pass

    def nextSliderState(self, conveyors: Conveyor, railState: int):
        """State cycles contains the incoming state on the first column, and the upcoming state in
        the second column, if the condition(if there is one) is met."""
        if railState == PICKING:
            stateCycle = np.array(
                [
                    [PICKING, Z_MVMT],  ## different from the picking, here
                    [Z_MVMT, IDLE],
                    [SKIPPED, SKIPPED],
                    [SKIP_N_WAIT, SKIP_N_WAIT],
                    [WAITING, IDLE],
                ]
            )
            deleteTarget = conveyors.deletePick
        elif railState == PLACING:
            stateCycle = np.array(
                [
                    [PLACING, Z_MVMT],
                    [Z_MVMT, IDLE],
                    [SKIPPED, IDLE],  ## different from the picking, here
                    [SKIP_N_WAIT, SKIP_N_WAIT],
                    [WAITING, IDLE],
                ]
            )
            deleteTarget = conveyors.deleteDrop
        else:
            return

        def nextState(currentState):
            return int(stateCycle[:, 1][np.isin(stateCycle[:, 0], currentState)][0])

        if self.status in (PICKING, PLACING):
            self.start_z_move = cfg.t
            deleteTarget(self.trackedTargetID)
            self.trackedTargetID = None

            # if railState == PICKING:
            # TODO modify this for 2 states input
            # self.trackedTargetID = (
            #     NORMAL if beams.workspaceSide[railID // 2] == 0 else NORMAL
            # )
            if railState == PLACING:

                "Register that a Pick&Place has been done"
                cfg.listStat[-1]["pickPerSlider"][self.ID] += 1

            self.status = nextState(self.status)

        elif self.status == Z_MVMT:
            if (cfg.t - self.start_z_move) * cfg.dt > TIME_Z_MOVE:
                self.status = nextState(self.status)

        elif self.status in (stateCycle[:, 0]):
            self.status = nextState(self.status)


class Beam:
    def __init__(self, params):
        beam = params["beam"]
        self.width = beam["width"]
        self.length = beam["length"]
        self.spacing = beam["spacing"]
        self.direction = beam["direction"]
        self.listBeamPos = []
        self.workspaceSide = beam["workspaceSide"]

        self.sliderReachOffset = params["slider"]["reachOffset"]
        self.sliderReach = params["slider"]["reach"]
        for beamsID in range(beam["nbOfBeams"]):
            self.listBeamPos.append(beam["firstBeamPos"] + beamsID * self.spacing)
        self.railStatus = np.ones(len(self.listBeamPos) * 2) * CAN_PICK
        self.bouncingInitState = np.zeros(len(self.listBeamPos) * 2)

    def nextRailState(self, rail: list[Slider], conveyors: Conveyor):
        railID = rail[0].ID // 2
        if self.railStatus[railID] == PICKING:
            nextState = CAN_PLACE
            repeatState = CAN_PICK
            inOrOut = "out"  # for the next preMove (with slider.nextState)
        elif self.railStatus[railID] == PLACING:
            nextState = CAN_PICK
            repeatState = CAN_PLACE
            inOrOut = "in"  # for the next preMove (with slider.nextState)
        else:
            return

        if SKIP_N_WAIT in (rail[0].status, rail[1].status):
            self.railStatus[railID] = repeatState

            # "If the state bouncing argument is enabled, make the outer beams bounce states"
            # if cfg.stateBouncing and rail[0].ID // 4 in (0, len(self.listBeamPos) - 1):
            #     "State bouncing is enabled by giving an initial bouncing state"
            #     self.bouncingInitState[railID] = repeatState
                
            "If the state bouncing argument is enabled, make the beams bounce states"
            if cfg.stateBouncing:
                "State bouncing is enabled by giving an initial bouncing state"
                self.bouncingInitState[railID] = repeatState

            if rail[0].status == SKIP_N_WAIT:
                rail[0].status = IDLE
                rail[1].status = WAITING

            elif rail[1].status == SKIP_N_WAIT:
                rail[0].status = WAITING
                rail[1].status = IDLE
        else:
            self.railStatus[railID] = nextState
            # "If the premove argument is enabled, make the outer beams pre move"
            # if cfg.preMove and rail[0].ID // 4 in (0, len(self.listBeamPos) - 1):
            #     self.preMove(rail, conveyors, self.workspaceSide[railID // 2], inOrOut)

            "If the premove argument is enabled, make the beams pre move"
            if cfg.preMove :
                self.preMove(rail, conveyors, self.workspaceSide[railID // 2], inOrOut)

    def preMove(
        self,
        sliders: list[Slider],
        conveyors: Conveyor,
        conveyorSide: int,
        inOrOut: str,
    ):
        DoI = np.array(getattr(conveyors, f"{inOrOut}Direction"))
        signDoI = DoI[DoI[SAME_DIR]]
        if inOrOut == "in":
            centerConveyor = conveyors.listInConveyor[conveyorSide]["endPos"][SAME_DIR]
        elif inOrOut == "out":
            centerConveyor = conveyors.listOutConveyor[conveyorSide]["endPos"][SAME_DIR]
        else:
            raise ValueError("inOrOut must be either 'in' or 'out'")
        halfSpacing = 0.5 * sliders[0].width + sliders[0].safetyMargin
        coord11 = (centerConveyor - halfSpacing) * np.abs(DoI[::-1])
        coord12 = (centerConveyor + halfSpacing) * np.abs(DoI[::-1])
        if signDoI == 1:
            coord2 = sliders[0].minPosition[ORTHOG_DIR] * np.abs(DoI)
        else:
            coord2 = sliders[0].maxPosition[ORTHOG_DIR] * np.abs(DoI)

        sliders[0].targetPosition[:2] = coord11 + coord2
        sliders[1].targetPosition[:2] = coord12 + coord2


def defineObjects(params):
    conveyors = Conveyor(params)
    beams = Beam(params)
    sliders = []

    def defineRail(side: int):
        ## todo UGLY, clean this mess
        tempSliders = []
        DoI = np.array(beams.direction)

        for j in range(params["slider"]["slidersPerRail"]):
            sliderID = 4 * i + 2 * ((side + 1) // 2) + j
            tempSliders.append(Slider(params, ID=sliderID))
            beamPos = beams.listBeamPos[i]
            halfWidth = beams.width / 2
            # TODO change _offset to constants with a name
            # TODO change 250 and 160 to constants with a name
            newPos = np.add(
                DoI * (250 * j + conveyors.xOffset),
                DoI[::-1] * (side * 160 + beamPos),
            ).tolist()
            tempSliders[-1].position[:-1] = tempSliders[-1].targetPosition[:-1] = newPos
            tempSliders[-1].railPos = beamPos + side * halfWidth

            "Defines the limits of the slider"
            "Extremas of the arm, horizontally"
            posArmExtrema1 = beamPos + side * (halfWidth + tempSliders[-1].reachOffset)
            posArmExtrema2 = posArmExtrema1 + side * tempSliders[-1].reach

            "Extremas of the slider, horizontally"
            posSliderExtrema1 = 0
            posSliderExtrema2 = (
                conveyors.listInConveyor[-1]["endPos"][
                    conveyors.inDirection[ORTHOG_DIR]
                ]
                + conveyors.listInConveyor[-1]["width"]
            )

            "Extremas of the arm, vertically"
            posHeightMaximum = tempSliders[-1].depth
            posHeightMinimum = 0

            tempSliders[-1].minPosition = np.append(
                np.add(
                    min(posArmExtrema1, posArmExtrema2) * DoI[::-1],
                    min(posSliderExtrema1, posSliderExtrema2) * DoI,
                ),
                posHeightMinimum,
            )
            tempSliders[-1].maxPosition = np.append(
                np.add(
                    max(posArmExtrema1, posArmExtrema2) * DoI[::-1],
                    max(posSliderExtrema1, posSliderExtrema2) * DoI,
                ),
                posHeightMaximum,
            )
            tempSliders[-1].status = IDLE
            # tempSliders[-1].scheduling = params["beam"]["scheduling"][i]
            schedulings = params["beam"]["scheduling"][: params["beam"]["nbOfBeams"]]

            tempSliders[-1].inScheduling = schedulings[i]
            tempSliders[-1].outScheduling = schedulings[-i - 1]
            # tempSliders[-1].outScheduling = schedulings[params["beam"]["nbOfBeams"]-i]
            # idx = 2*i+j
            # tempSliders[-1].inScheduling = schedulings[idx]
            # tempSliders[-1].outScheduling = schedulings[-idx-1]

        sliders.append(tempSliders)

    for i in range(params["beam"]["nbOfBeams"]):
        defineRail(-1)
        defineRail(1)
    conveyors.generatePicks(0)
    conveyors.generateDrops(0)

    # ## start offset:
    # while conveyors.new_position[1] < conveyors.length * 0.6:
    #     deltaDist = (
    #         conveyors.packagesRowSpacing * (conveyors.nPackagesRow - 1)
    #         + conveyors.packagesExtraSpacing
    #     )
    #     conveyors.new_position[1] += deltaDist
    #     conveyors.moveDrops(0, deltaDist* np.array(conveyors.outDirection))
    #     conveyors.generateDrops(0)
    #     # we should disable the deltaMove for the output conveyor until it actually move

    return sliders, conveyors, beams
