import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from time import time
from description.objects import *
from description.constants import *
from scripts.json_handler import writeHistory, saveHistory, saveStat
from scripts.trajectoryControl import setExtraLookingRange

import scripts.pickControl as pick
import scripts.dropControl as drop
import scripts.compute_trajectory as move
import scripts.plotter as plotter
import description.config as cfg


def initRuckig(*args: Object):
    for obj in args:
        if isinstance(obj, list):
            initRuckig(*obj)
        else:
            move.initRuckig(obj)


def updateConveyor(conveyors: Conveyor):
    pass


def updateSliders(
    sliders: list[list[Slider]], conveyors: Conveyor, beams: Beam
) -> None:
    """Update the state of the sliders.

    Args:
        sliders (list[list[Slider]]): list of the rails, which is a list of sliders
        conveyors (Conveyor): Conveyor object containing information about the conveyors.
        beams (Beam): Beam object containing beam information.
    """
    for railID, rail in enumerate(sliders):
        isDone = True

        for s in rail:
            move.updateRuckig(s)

            if beams.railStatus[railID] == PICKING and s.status == PICKING:
                errorPos = np.array(s.position[:-1]) - np.array(
                    conveyors.listPicks[s.trackedTargetID]["pos"]
                )
            elif beams.railStatus[railID] == PLACING and s.status == PLACING:
                errorPos = np.array(s.position[:-1]) - np.array(
                    conveyors.listDrops[s.trackedTargetID]["pos"]
                )
            else:
                errorPos = np.array(s.position[:-1]) - np.array(s.targetPosition[:2])

            if np.all(np.abs(errorPos) < conveyors.errorMargin) and np.all(
                np.abs(s.currentVelocity) <= conveyors.errorMargin
            ):
                "If the position has been reached, changed the slider's state."
                s.nextSliderState(conveyors, beams.railStatus[railID])

                if s.status == "Z_MVMT":
                    "Record the number of timesteps where a slider is moving"
                    cfg.listStat[-1]["workload"][s.ID] += 1
            else:
                "Record the number of timesteps where a slider is moving"
                cfg.listStat[-1]["workload"][s.ID] += 1

            if s.status in (Z_MVMT, PLACING, PICKING):
                isDone = False

        if isDone:
            beams.nextRailState(rail, conveyors)


def update(
    sliders: list[list[Slider]],
    conveyors: Conveyor,
    beams: Beam,
    plotEvery: int,
    max_time: int,
    isGifSaved: bool,
    isJsonSaved: bool,
    plot_elements=None,
    ax=None,
    fig_dim=None,
    frames=None,
):
    global t, history, running
    for _ in range(plotEvery):
        if t * cfg.dt >= max_time:
            break
        # if (t*cfg.dt) % 5 == 0:
        #     print(f"{bcolors.OKBLUE} Starting second {t*cfg.dt} {bcolors.ENDC}")
        # print("\r" + f"{LINE_START}Time: {t*cfg.dt:.2f}", end="")

        # cfg.listStat[-1]["dropsInRangePerT"].append(0)
        # findDropsInRange(conveyors, beams, sliders[-1])
        # findDropsInRange(conveyors, beams, sliders[-2])

        "Assign picks to sliders"
        pick.assignPicks(sliders, conveyors, beams)
        drop.assignDrops(sliders, conveyors, beams)

        "Update map"
        conveyors.moveConveyors(t)
        updateSliders(sliders, conveyors, beams)
        cfg.recordSlidersKinematics(sliders)
        if isJsonSaved:
            history = writeHistory(history, sliders, conveyors, beams, t)
        t += 1
        cfg.t = t
    if isGifSaved:
        "Update plot elements"
        updated_artists = plotter.updatePlot(conveyors, sliders, plot_elements)

        "Return updated elements for blitting"
        return updated_artists

    elif isPlottingLive:

        ax.cla()
        plotter.initializePlot(conveyors, sliders, beams, params, ax, isGifSaved)

        ax.set_xlim(-PLOT_MARGIN, fig_dim[0])
        ax.set_ylim(fig_dim[1], -PLOT_MARGIN)
        plt.pause(cfg.dt * plotEvery)


def initCode(
    history,
    params,
    isPlottingLive,
    isGifSaved,
    isJsonSaved,
    saveName,
):

    bu, end = bcolors.BU, bcolors.ENDC
    sliders, conveyors, beams = defineObjects(params)

    initRuckig(conveyors, sliders)
    setExtraLookingRange(sliders[0][0], conveyors)
    plotEvery = 5
    max_time = params["duration"]  # Time to render in [s]
    frames = int(max_time / cfg.dt) // plotEvery

    def on_key_press(event):
        global running
        if event.key == "q":
            print(
                f"{LINE_START}{bcolors.WARNING}Quit key pressed. Exiting...{bcolors.ENDC}"
            )
            running = False

    "Set up the plot"
    if isPlottingLive or isGifSaved:
        fig, ax, fig_dim, plot_elements = plotter.setupPlot(
            conveyors,
            sliders,
            beams,
            params,
            isGifSaved,
            on_key_press,
        )

    time_start = time()
    if isGifSaved:
        "Create the animation"
        ani = FuncAnimation(
            fig,
            update,
            fargs=(
                sliders,
                conveyors,
                beams,
                plot_elements,
                ax,
                fig_dim,
                plotEvery,
                max_time,
                isGifSaved,
                isJsonSaved,
            ),
            frames=frames,
            init_func=lambda: plot_elements["all_artists"],
            blit=True,
            repeat=False,
        )
        "Save the animation as a GIF"
        ani.save(
            "simulation_animation.gif",
            writer=PillowWriter(fps=1 / (1 * cfg.dt * plotEvery)),
        )  # Adjust fps as needed
        c = bcolors.OKGREEN
        print(f"{c}Time to compute: {bu}" + f"{time() - time_start:.2f} seconds{end}")

        print(f"{c}GIF created successfully!{end}")
    else:
        try:
            global running
            while t * cfg.dt < max_time and running:
                if isPlottingLive:
                    update(
                        sliders,
                        conveyors,
                        beams,
                        plotEvery,
                        max_time,
                        isGifSaved,
                        isJsonSaved,
                        plot_elements,
                        ax,
                        fig_dim,
                    )

                else:
                    update(
                        sliders,
                        conveyors,
                        beams,
                        plotEvery,
                        max_time,
                        isGifSaved,
                        isJsonSaved,
                    )
        except (KeyboardInterrupt, SystemExit):
            c = bcolors.WARNING
            print(f"{LINE_START}{c}Interrupted by user.{end}")

            running = False
            return "interupt"
        except Exception as e:
            print(f"An error occurred: {e}")
            return {e}

    c, b, bu, end = bcolors.OKGREEN, bcolors.BOLD, bcolors.BU, bcolors.ENDC
    print(LINE_START)
    print(
        f"{LINE_START}{c}Time to compute: {bu}"
        + f"{time() - time_start:.2f}{end}{c} seconds{end}"
    )
    c = bcolors.OKCYAN
    c2 = bcolors.FAIL
    if isJsonSaved:
        saveHistory(
            history, cfg.listStat, params, f"{saveName}_{i}" if nRuns > 1 else saveName
        )
    print(LINE_START)
    mp = cfg.listStat[-1]["missedPicks"]
    tp = cfg.listStat[-1]["totalPicks"]
    md = cfg.listStat[-1]["missedDrops"]
    td = cfg.listStat[-1]["totalDrops"]
    up = cfg.listStat[-1]["unfilledPackages"]
    tpk = cfg.listStat[-1]["totalPackages"]
    print(
        f"{LINE_START}{c}Total missed picks: {c2}{b}{mp} ({mp*100/tp:.4f}%){end}\n"
        + f"{LINE_START}{c}Total missed drops: {c2}{b}{md} ({md*100/td:.4f}%){end}\n"
        + f"{LINE_START}{c}Total unfilled boxes: {c2}{b}{up} ({up*100/tpk:.4f}%){end}"
    )


if __name__ == "__main__":
    ### TODO clean this mess
    args = cfg.parser()
    (
        params,
        isPlottingLive,
        isGifSaved,
        isJsonSaved,
        isCVSSaved,
        single_run,
        seed,
        saveName,
    ) = cfg.initParams(args)
    c, b, end = bcolors.HEADER, bcolors.BOLD, bcolors.ENDC

    cfg.statTemplate["dt"] = cfg.dt

    if single_run:
        nRuns = 1
        nRunsPerParameter = 1

    ####################################################################################
    ###
    ### Modify Here
    else:
        nRuns = 10
        nRunsPerParameter = 10

    # paramName = "scheduling"  # will be used as the entry's name in the stored data
    paramName = "conveyorSpeed"  # will be used as the entry's name in the stored data
    # paramName = "premove"  # will be used as the entry's name in the stored data
    # paramName = "packagesExtraDist"  # will be used as the entry's name in the stored data
    ####
    convInputSpeed = 4250 / 60
    if single_run or paramName != "conveyorSpeed":
        convInputSpeed *= 1.1

    else:
        startMultiplier = 0.7
        endMultiplier = 1.3

        multiplier = np.linspace(endMultiplier, startMultiplier, nRuns)

    ####
    if not single_run:
        if paramName == "scheduling":
            beam0Scheduling = ["FIFO", "LIFO", "SPT", "LPT"]
            beam1Scheduling = ["FIFO", "LIFO", "SPT", "LPT"]
            beam2Scheduling = ["FIFO", "LIFO", "SPT", "LPT"]
            beam3Scheduling = ["FIFO", "SPT", "LPT"]
            scheduling = (
                np.array(
                    np.meshgrid(
                        beam0Scheduling,
                        beam1Scheduling,
                        beam2Scheduling,
                        beam3Scheduling,
                    )
                )
                .T.reshape(-1, 4)
                .tolist()
            )
            nRuns = len(scheduling)

        ####

        if paramName == "packagesExtraDist":
            start = 80  # Starting extra distances values
            ending = 200  # Ending extra distances values (included in the testing)
            steps = 10  # The steps between each testing value
            extraDistances = np.linspace(start, ending, (ending - start) // steps + 1)
            nRuns = len(extraDistances)

    ###
    ###################################################################################

    # params["conveyor"]["packagesExtraSpacing"] = 180
    """ In reality, only the input conveyor speed is used. The output conveyor speed is computed
    to ensure equal flow between the two"""
    convInitialSpeed = cfg.defineOutSpeed(convInputSpeed, params)
    params["conveyor"]["speed"] = list(convInitialSpeed)
    total_time = time()
    global running
    running = True
    for i in range(nRuns):

        if not single_run:
            if paramName == "conveyorSpeed":
                variedParam = params["conveyor"]["speed"] = list(
                    convInitialSpeed * multiplier[i]
                )
            else:
                ####################################################################################
                ###
                ### Modify Here
                variedParam = params["conveyor"]["packagesExtraSpacing"] = (
                    extraDistances[i]
                )
                if paramName == "packagesExtraDist":
                    convInitialSpeed = cfg.defineOutSpeed(convInputSpeed, params)
                    params["conveyor"]["speed"] = list(convInitialSpeed)
                # variedParam = params["beam"]["scheduling"] = scheduling[i]
                # variedParam = params["dt"] = cfg.dt = test_dt[i]

        if isCVSSaved and not single_run:
            cfg.statTemplate[paramName] = variedParam

        ### Let the magic work
        ####################################################################################

        for j in range(nRunsPerParameter):
            print(SEPARATOR)
            print(SEPARATOR2)
            cfg.newStatEntry(params)

            err = 0
            # Note : We could try to use multithreading here, when runnning multiple parameters, to make the process faster
            while err is not None:
                history = {}
                t = 0
                print(
                    f"{LINE_START}{c}Starting run {i*nRunsPerParameter + j+1} / {nRuns*nRunsPerParameter}"
                    +f" [{(i*nRunsPerParameter + j+1) / (nRuns*nRunsPerParameter)*100:.2f}%]{end}"
                )
                if not single_run:
                    print(f"{LINE_START}{c}Using parameters {variedParam}{end}")

                cfg.newSeed(seed)

                err = initCode(
                    history, params, isPlottingLive, isGifSaved, isJsonSaved, saveName
                )
                if single_run:
                    err = None
                if err is None:
                    cfg.listStat[-1]["totalTimeSteps"] = t

                    print(SEPARATOR2)
                elif err == "interupt":
                    pass
                else:
                    cfg.newErrEntry(err, i, j, paramName, variedParam)

                if not running:
                    exit()
            if not running:
                break
        if not running:
            break

    if isCVSSaved:
        if nRuns == 1 and nRunsPerParameter == 1:
            params["seed"] = cfg.listStat[-1]["seed"]
        saveStat(cfg.listStat, params, saveName)

    print(SEPARATOR)
    c, bu = bcolors.WARNING, bcolors.BU

    print(
        f"\n{c}Total time for {nRuns*nRunsPerParameter} runs: {bu}"
        + f"{time() - total_time:.2f}{end}{c} seconds{end}"
    )
    print(f"{time() - total_time:.2f}")
    if len(cfg.listError) > 0:
        print(f"{c}{cfg.listError}{end}")
