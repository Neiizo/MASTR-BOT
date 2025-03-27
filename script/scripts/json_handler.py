import json
from time import time
from itertools import chain
import numpy as np
import os
import pandas as pd

from description.constants import *

# from description.config import stat


def loadJson(resetParams=False):

    #### Writes the parameters to a json file
    if resetParams:
        params = {}
        params["unit"] = {}
        unit = params["unit"]
        params["timeStep"] = 0.01
        params["duration"] = 60.0
        params["seed"] = 0

        ### Define the conveyors
        params["conveyor"] = {}
        conveyor = params["conveyor"]
        conveyor["speed"] = [4250.0 / 60, 3 * 4250.0 / 60]  # [inSpeed, outSpeed]
        unit["speed"] = "mm/s"
        conveyor["accel"] = [20.0e3] * 2  # [inAccel, outAccel]
        unit["accel"] = "mm/s^2"
        conveyor["length"] = 3000.0
        unit["length"] = "mm"
        conveyor["nbInConveyor"] = 2
        unit["nbInConveyor"] = ""
        conveyor["nbOutConveyor"] = 1
        unit["nbOutConveyor"] = ""
        conveyor["inDirection"] = [-1, 0]
        unit["inDirection"] = "direction"
        conveyor["inEndPos"] = []
        unit["inEndPos"] = "mm"
        conveyor["outEndPos"] = []
        unit["outEndPos"] = "mm"
        conveyor["outDirection"] = [-1, 0]
        unit["outDirection"] = "direction"
        conveyor["inItemsPerRow"] = []
        unit["inItemsPerRow"] = ""
        conveyor["inWidth"] = []
        unit["inWidth"] = "mm"
        conveyor["isSingleColor"] = True
        unit["isSingleColor"] = "bool"
        conveyor["inRowSpacing"] = 60.0
        unit["inRowSpacing"] = "mm"
        conveyor["conveyorOffset"] = 25.0
        unit["conveyorOffset"] = "mm"
        conveyor["xOffset"] = 100.0
        unit["xOffset"] = "mm"

        conveyor["badProductRatio"] = 0.2
        unit["badProductRatio"] = ""
        conveyor["errorMargin"] = 1.5
        unit["errorMargin"] = "mm"
        for i in range(conveyor["nbInConveyor"]):
            conveyor["inItemsPerRow"].append(6)
            conveyor["inEndPos"].append(
                [
                    0.0,
                    387.0 / 2
                    + i * 677
                    + conveyor["conveyorOffset"] * i * 2
                    + conveyor["xOffset"],
                ]
            )
            conveyor["inWidth"].append(387.0)

        conveyor["nPackagesRow"] = 3  # should be 3 4 or 5
        unit["nPackagesRow"] = ""
        conveyor["packagesRowSplitting"] = (
            True  # HAS to be false with nPackagesRow = 4 or 5
        )
        unit["packagesRowSplitting"] = "bool"
        conveyor["packagesRowSplitSpacing"] = 40.0
        unit["packagesRowSplitSpacing"] = "mm"
        conveyor["packagesRowSpacing"] = 60.0
        unit["packagesRowSpacing"] = "mm"
        conveyor["outItemsPerRow"] = []
        unit["outItemsPerRow"] = ""
        conveyor["outWidth"] = []
        unit["outWidth"] = "mm"
        for i in range(conveyor["nbOutConveyor"]):
            conveyor["outItemsPerRow"].append(4)
            conveyor["outEndPos"].append(
                [
                    0.0,
                    387.0 + 290 / 2 + conveyor["xOffset"] + conveyor["conveyorOffset"],
                ]
            )
            conveyor["outWidth"].append(290.0)
        conveyor["dropOffset"] = 50.0
        unit["dropOffset"] = "mm"

        ### Define the sliders
        params["slider"] = {}
        slider = params["slider"]
        slider["speed"] = [2500.0, 5000.0, 5000.0]
        slider["accel"] = [20.0e3, 40.0e3, 40.0e3]
        slider["max_jerk"] = [2.5e5, 4.0e5, 4.0e5]
        unit["max_jerk"] = "mm/s^3"
        slider["width"] = 120.0
        unit["width"] = "mm"
        slider["armWidth"] = 20.0
        unit["armWidth"] = "mm"
        slider["reach"] = 100.0
        unit["reach"] = "mm"
        slider["reachOffset"] = 40.0
        unit["reachOffset"] = "mm"
        slider["depth"] = 100.0
        unit["depth"] = "mm"
        slider["slidersPerRail"] = 2
        unit["slidersPerRail"] = ""
        # Note : This is the number of sliders per rail, not beams !!!
        slider["safetyMargin"] = 10.0
        unit["safetyMargin"] = "mm"
        # TODO change in the future to have a dynamic list, so each beam can have an independant nb of sliders, as well as preferred side

        params["beam"] = {}
        beam = params["beam"]
        beam["spacing"] = 420.0
        unit["spacing"] = "mm"
        beam["width"] = 100.0
        beam["length"] = 1300.0
        beam["nbOfBeams"] = 6
        unit["nbOfBeams"] = ""
        beam["workspaceSide"] = [0] * (beam["nbOfBeams"] // 2) + [1] * (
            (beam["nbOfBeams"] + 1) // 2
        )
        beam["scheduling"] = ["FIFO"] * beam["nbOfBeams"]
        unit["scheduling"] = "scheduling"
        beam["direction"] = [0, 1]  # has to be positive
        unit["direction"] = "direction"
        unit["workspaceSide"] = ""
        beam["firstBeamPos"] = 600.0
        unit["firstBeamPos"] = "mm"

        params["target"] = {}
        target = params["target"]
        target["width"] = 50.0

        with open("pages/api/params.json", "w") as f:
            json.dump(params, f, indent=4)

    #### Loads the parameters from a json file
    try:
        with open("pages/api/params.json", "r") as f:
            params = json.load(f)
    except FileNotFoundError:
        raise Exception("File not found")

    return params


def writeHistory(history, s, c, b, t):
    """Makes a snapshot of the current state of the system and saves it in the history dictionary.

    Args:
        history (dict): description of the position and status of every object at every timeSteps
        s (List[List[Slider]]): List of a list of sliders. The first dimension is the list of rails, and the second is the list of sliders on said rail
        c (Conveyors): Description of the conveyors
        b (Beams): Description of the beams
        t (float): current timeStep
    """

    # changer les arrondis pour mettre 2 décimals
    history[t] = {
        "targets": {
            "position": np.round(
                [pick["pos"] for pick in c.listPicks.values()],
                decimals=ROUNDING_JSON,
            ).tolist(),
            "status": [pick["status"] for pick in c.listPicks.values()],
        },
        "drops": {
            "position": np.round(
                [drop["pos"].tolist() for drop in c.listDrops.values()],
                decimals=ROUNDING_JSON,
            ).tolist(),
            "status": [drop["status"] for drop in c.listDrops.values()],
        },
        "sliders": {
            "position": np.round(
                [
                    [coord for coord in slider.position]
                    for slider in chain.from_iterable(s)
                ],
                decimals=ROUNDING_JSON,
            ).tolist(),
            "status": [slider.status for rail in s for slider in rail],
        },
        "beams": {
            "status": [b.railStatus[railID] for railID in range(len(b.railStatus))],
        },
    }
    return history


def saveHistory(history, stat, params, saveName):
    """Saves the history and the parameters used for the running simulation inside a folder
    bearing the name of the current date, or the desired name if indicated.

    Args:
        history (dict): description of the position and status of every object at every timeSteps
        params (dict): description of the parameters used for the simulation
        saveName (str): Name under which to save the simulation
    """
    c, bu, end = bcolors.OKCYAN, bcolors.BU, bcolors.ENDC
    print(LINE_START)
    print(f"{LINE_START}{c+bcolors.BOLD}Saving history{end}")

    time_start = time()
    os.makedirs(f"pages/api/history/{saveName}", exist_ok=True)
    with open(f"pages/api/history/{saveName}/history.json", "w") as f:
        json.dump(history, f, separators=(",", ":"))

    saveStat(stat, params, saveName, folderName="history")

    c = bcolors.OKGREEN
    print(
        f"{LINE_START}{c}History saved in {bu}{time() - time_start:.2f}{end+c} seconds at :\n"
        + f"{LINE_START}{c+bu}pages/api/history/{saveName}/{end}"
    )


def saveStat(stat, params, saveName, folderName="stats"):
    """Saves the stats and the parameters used for the running simulation inside a folder
    bearing the name of the current date, or the desired name if indicated.

    Args:
        stat (dict): List of all the data collected during the simulation
        params (dict): description of the parameters used for the simulation
        saveName (str): Name under which to save the simulation
    """
    if folderName == "stats":
        c, bu, end = bcolors.OKCYAN, bcolors.BU, bcolors.ENDC
        print(LINE_START)
        print(f"{LINE_START}{c+bcolors.BOLD}Saving stats{end}")

        os.makedirs(f"pages/api/{folderName}/{saveName}", exist_ok=True)

    with open(f"pages/api/{folderName}/{saveName}/params.json", "w") as f:
        json.dump(params, f, separators=(",", ":"))

    df = pd.DataFrame(stat)
    pd.DataFrame.to_csv(df, f"pages/api/{folderName}/{saveName}/stat.csv", index=False)

    if folderName == "stats":
        c = bcolors.OKGREEN
        print(
            f"{LINE_START}{c}Stats saved at :\n"
            + f"{LINE_START}{c+bu}pages/api/{folderName}/{saveName}/{end}"
        )
        print(LINE_START)
