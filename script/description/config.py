import numpy as np
import argparse
import random
from datetime import datetime
import argparse
import copy

from description.constants import *
from scripts.json_handler import loadJson


statTemplate = {
    "missedPicks": 0,
    "missedDrops": 0,
    "unfilledPackages": 0,
    "totalPicks": 0,
    "totalDrops": 0,
    "totalPackages": 0,
    "timeMissedPicks": [],
    "timeMissedDrops": [],
    "seed": 0,
    "preMove": False,
    "workload": None,
    "pickPerSlider": None,
    "slidersVelocity": None,
    "slidersAcceleration": None,
    "startRecordingTime": 0,
    "startRecordingTime_2": 0,
    "totalTimeSteps": 0,
    "dropsInRangePerT": [],
}

listStat = []
listError = []


def newStatEntry(params):
    listStat.append(copy.deepcopy(statTemplate))
    
    listStat[-1]["workload"] = (
        [0]
        * params["slider"]["slidersPerRail"]
        * params["beam"]["nbOfBeams"]
        * 2
    )
    listStat[-1]["pickPerSlider"] = (
        [0]
        * params["slider"]["slidersPerRail"]
        * params["beam"]["nbOfBeams"]
        * 2
    )
    listStat[-1]["slidersVelocity"] = (
        [None]
        * params["slider"]["slidersPerRail"]
        * params["beam"]["nbOfBeams"]
        * 2
    )
    listStat[-1]["slidersAcceleration"] = (
        [None]
        * params["slider"]["slidersPerRail"]
        * params["beam"]["nbOfBeams"]
        * 2
    )


def newErrEntry(e, i, j, paramName, variedParam):

    print(
        f"{LINE_START}{bcolors.FAIL}Error detected at nRuns {i} and \n"
        + f"nRunsParameter {j} ({paramName} value : {variedParam}). Retrying {bcolors.ENDC}"
    )
    subList = {
        "error": e,
        "seed": listStat[-1]["seed"],
        "nRunsIdx": i,
        "nRunsParameterIdx": j,
    }
    listError.append(subList)


def defineOutSpeed(inSpeed, params):

    inRowSpacing = params["conveyor"]["inRowSpacing"]
    packagesRowSpacing = params["conveyor"]["packagesRowSpacing"]
    nPackagesRow = params["conveyor"]["nPackagesRow"]
    patternOffset = params["conveyor"]["packagesExtraSpacing"]
    badRatio = params["conveyor"]["badProductRatio"]

    inItemPerRow = 0
    for i in range(params["conveyor"]["nbInConveyor"]):
        inItemPerRow += params["conveyor"]["inItemsPerRow"][i]
    outItemPerRow = 0
    for i in range(params["conveyor"]["nbOutConveyor"]):
        outItemPerRow += params["conveyor"]["outItemsPerRow"][i]
    temp1 = (
        inSpeed
        * inItemPerRow
        * (1 - badRatio)
        * (nPackagesRow * packagesRowSpacing + patternOffset)
    )
    temp2 = inRowSpacing * outItemPerRow * nPackagesRow
    outSpeed = temp1 / temp2

    return np.array([inSpeed, outSpeed])


def newSeed(seed=None):
    c, bu, end = bcolors.OKCYAN, bcolors.BU, bcolors.ENDC
    seed = random.randrange(2**32 - 1) if seed is None else seed
    
    print(f"{LINE_START}{c}New seed : {bu}{seed}{end}")
    listStat[-1]["seed"] = seed
    random.seed(seed)
    np.random.seed(seed)


def recordSlidersKinematics(sliders):
    for rail in sliders:
        for slider in rail:
            velVal = [
                slider.currentVelocity[slider.direction[SAME_DIR]],
                slider.currentVelocity[slider.direction[ORTHOG_DIR]],
                slider.currentVelocity[2],
            ]
            accelVal = [
                slider.currentAcceleration[slider.direction[SAME_DIR]],
                slider.currentAcceleration[slider.direction[ORTHOG_DIR]],
                slider.currentAcceleration[2],
            ]
            # if it doesn't exist, we create it
            if listStat[-1]["slidersVelocity"][slider.ID] is None:
                listStat[-1]["slidersVelocity"][slider.ID] = [velVal]
            else:
                listStat[-1]["slidersVelocity"][slider.ID].append(velVal)

            if listStat[-1]["slidersAcceleration"][slider.ID] is None:
                listStat[-1]["slidersAcceleration"][slider.ID] = [accelVal]
            else:
                listStat[-1]["slidersAcceleration"][slider.ID].append(accelVal)


def promptUserValue(string: str, returnType, currentValue):
    # c, bu, end = bcolors.OKCYAN, bcolors.BU, bcolors.ENDC

    print(string)
    if returnType == bool:
        while True:
            user_input = input().strip().lower()
            if user_input == "y":
                return True
            elif user_input == "n":
                return False
            elif user_input == "":
                return currentValue
            else:
                print("Please enter y or n or leave empty to keep the current value !")
    elif returnType == str:
        newVal = input()
        if newVal == "":
            return currentValue
        return newVal
    elif returnType == int:
        while True:
            user_input = input()
            if user_input == "":
                return currentValue
            elif user_input.isdigit():
                return int(user_input)
            else:
                print("Please enter number or leave empty to keep the current value !")


def parser(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a simulation, based on the given parameters, for the excenter machine."
    )
    parser.add_argument(
        "-buildHelper",
        action="store_true",
        help="Use this argument if you want to utiliser the build helper",
    )
    parser.add_argument(
        "-plot",
        type=str,
        default="no",
        help="decide wether you want to save as a gif('save'), show the plot live('show') or do nothing ('no'))",
    )
    parser.add_argument(
        "-save_hist",
        action="store_true",
        help="Save the simulation as a series of timepoint, for the typescript to read",
    )
    # parser.add_argument(
    #     "-reset_params",
    #     action="store_true",
    #     help="Resets the parameters to what is defined in loadJson.py",
    # )
    parser.add_argument(
        "-seed",
        type=int,
        help="Decide which seed to use for the randomness (noise and bad target generation)",
    )

    parser.add_argument(
        "-name",
        type=str,
        default=datetime.now().strftime("%Y%m%d_%H%M%S"),
        help="Name under which to save the simulation",
    )
    parser.add_argument(
        "-single_run",
        action="store_true",
        # action="store_false",
        help="make a single simulation run",
    )
    parser.add_argument(
        "-no_csv",
        action="store_true",
        # action="store_false",
        help="Save the data collected during the simulation",
    )
    parser.add_argument(
        "-state_bouncing",
        action="store_true",
        # action="store_false",
        help="Save the data collected during the simulation",
    )
    parser.add_argument(
        "-pre_move",
        action="store_true",
        # action="store_false",
        help="Save the data collected during the simulation",
    )
    c, c2, cw, b, bu, end = (
        bcolors.OKCYAN,
        bcolors.OKBLUE,
        bcolors.WARNING,
        bcolors.BOLD,
        bcolors.BU,
        bcolors.ENDC,
    )

    args = parser.parse_args(argv)
    if args.buildHelper:
        cmd_line = "python script/main.py"
        for arg in vars(args):
            if arg != "buildHelper":
                help_string = parser._option_string_actions[f"-{arg}"].help
                defaultValue = parser._option_string_actions[f"-{arg}"].default
                currentValue = getattr(args, arg)
                varType = type(currentValue)
                if varType is type(None):
                    "{...}.type doesn't work with booleans, that's why we first do type(currentValue)"
                    varType = parser._option_string_actions[f"-{arg}"].type

                if varType == bool:
                    startStr = (
                        f"{c}{bu}Do you want to use {arg} ?{end} {c}{b}(y/n){end} \n"
                    )
                else:
                    startStr = f"{c}{bu}What value do you want to set for {arg} ?{end} {c}{b}(Leave empty to keep the current value){end} \n"
                printStr = (
                    startStr
                    + f"{c2}{b}Description:{end}{c2} {help_string}{end}\n"
                    + f"{c2}{b}Current value:{end}{c2} {currentValue}{end}\n"
                )
                user_input = promptUserValue(
                    printStr, returnType=varType, currentValue=currentValue
                )
                if user_input != defaultValue:
                    cmd_line += f" -{arg}"
                    if type(user_input) != bool:
                        cmd_line += f" {user_input}"

                setattr(args, arg, user_input)
        print(
            f"{cw}{bu}Command line to reproduce the simulation{end} : \n{c2}{b}{cmd_line}{end}"
        )
    return args


def initParams(args: argparse.Namespace):
    global dt
    global t
    t = 0
    isPlottingLive = False
    isGifSaved = False

    c, bu, end = bcolors.OKCYAN, bcolors.BU, bcolors.ENDC
    if args.plot == "show":
        isPlottingLive = True

    elif args.plot == "save":
        isGifSaved = True

    elif args.plot != "no":
        print(f"{bcolors.FAIL}Plotting option not recognized. Exiting...{end}")
        exit()

    if args.seed:
        print(f"{c}Random noise and random bad target generation disabled{end}")

    else:
        print(f"{c}Random noise and random bad target generation enabled{end}")

    print(f"{c}Plotting option : {bu}{args.plot}{end}")
    params = loadJson(False)
    dt = params["timeStep"]  # Time step in [s]

    global preMove, stateBouncing
    statTemplate["preMove"] = preMove = args.pre_move
    statTemplate["stateBouncing"] = stateBouncing = args.state_bouncing

    return (
        params,
        isPlottingLive,
        isGifSaved,
        args.save_hist,
        not (args.no_csv),
        args.single_run,
        args.seed,
        args.name,
    )
