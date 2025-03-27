import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

from description.constants import *

### Colors and alpha values for the plots. Placed here for easier change.
sliderColor = "black"
sliderAlpha = 0.6
beamColor = "gray"
beamAlpha = 0.2
inConveyorColor = "red"
inConveyorAlpha = 0.2
outConveyorColor = "green"
outConveyorAlpha = 0.2

pickSkippedColor = "gray"
pickAssignedColor = "orange"
pickFreeColor = "blue"
pickBadColor = "red"

dropNormalColor = "blue"
dropFlippedColor = "green"
dropAssignedColor = "red"



def xySliders(slider):
    # Compute the carriage's position
    position = np.array(slider.position)[:-1]
    sliderWidth = slider.width
    armWidth = slider.armWidth
    reach = slider.reach
    reachOffset = slider.reachOffset
    railPos = slider.railPos
    if slider.ID%4>=2:
        beamSide = 1
    else:
        beamSide = -1
    DoI = np.array(slider.direction)

    rectSize1 = DoI * sliderWidth
    rectSize2 = DoI[::-1] * (reachOffset + reach) / 2 * beamSide
    rectSize = np.add(rectSize1, rectSize2)

    new_carriage_xy = np.add((position - sliderWidth / 2) * DoI, railPos * DoI[::-1])

    # Compute the arm's position and size

    armSize1 = DoI * armWidth
    armSize2 = DoI[::-1] * (position - railPos - reachOffset * beamSide)

    armSize = np.add(armSize1, armSize2)
    arm_xy = np.add(
        (position - armWidth / 2) * DoI,
        (railPos + reachOffset * beamSide) * DoI[::-1],
    )
    return rectSize, new_carriage_xy, arm_xy, armSize, position


def plotBeams(conveyors, beams, ax, plot_elements):
    for pos in beams.listBeamPos:
        DoI = np.array(beams.direction)
        rectSize = np.add(
            DoI * beams.length,
            DoI[::-1] * beams.width,
        )
        beamRect = patches.Rectangle(
            (pos - beams.width / 2) * DoI[::-1],
            rectSize[0],
            rectSize[1],
            linewidth=1,
            edgecolor="black",
            facecolor=beamColor,
            alpha=beamAlpha,
        )
        ax.add_patch(beamRect)
        plot_elements["beams"].append(beamRect)
        ## TODO CHANGE THIS TO A MORE GENERAL DESCRIPTION
        workspaceSide = beams.workspaceSide[beams.listBeamPos.index(pos)]
        inConveyorWidth = conveyors.listInConveyor[workspaceSide]["width"]
        # TODO change here if we have multiple output conveyors

        for sign in [-1, 1]:
            rectSize = np.add(
                DoI
                * (
                    inConveyorWidth
                    + conveyors.listOutConveyor[0]["width"]
                    + conveyors.xOffset
                    - conveyors.conveyorOffset
                ),
                DoI[::-1] * beams.sliderReach * sign,
            )
            ## TODO CHANGE THIS TO A MORE GENERAL DESCRIPTION
            pickRect = patches.Rectangle(
                np.add(
                    DoI[::-1]
                    * (pos + sign * (beams.sliderReachOffset + beams.width / 2)),
                    DoI
                    * (
                        workspaceSide * (inConveyorWidth + conveyors.conveyorOffset)
                        + conveyors.xOffset
                        - conveyors.conveyorOffset
                    ),
                ),
                *rectSize,
                linewidth=1,
                edgecolor="black",
                facecolor=beamColor,
                linestyle="-.",
                alpha=beamAlpha,
            )
            ax.add_patch(pickRect)
            plot_elements["beams"].append(pickRect)
    return plot_elements


def plotConveyors(conveyors, ax, plot_elements):
    for conveyor in conveyors.listInConveyor:
        DoI = np.array(conveyors.inDirection)
        rectSize = np.add(
            -DoI * conveyors.length,
            np.abs(DoI[::-1] * conveyor["width"]),
        )
        inConveyorRect = patches.Rectangle(
            (conveyor["endPos"][0], conveyor["endPos"][1] - 387 / 2),
            *rectSize,
            linewidth=1,
            edgecolor="black",
            facecolor=inConveyorColor,
            alpha=inConveyorAlpha,
        )
        ax.add_patch(inConveyorRect)
        plot_elements["conveyors"].append(inConveyorRect)

    for conveyor in conveyors.listOutConveyor:
        DoI = np.array(conveyors.outDirection)
        rectSize = np.add(
            -DoI * conveyors.length,
            np.abs(DoI[::-1] * conveyor["width"]),
        )
        outConveyorRect = patches.Rectangle(
            (conveyor["endPos"][0], conveyor["endPos"][1] - 290 / 2),
            *rectSize,
            linewidth=1,
            edgecolor="black",
            facecolor=outConveyorColor,
            alpha=outConveyorAlpha,
        )
        ax.add_patch(outConveyorRect)
        plot_elements["conveyors"].append(outConveyorRect)
    return plot_elements


def colorPicks(status):
    if status == GONE:
        return False
    if status == FREE:
        color = pickFreeColor
    elif status == ASSIGNED:
        color = pickAssignedColor
    elif status == SKIPPED:
        color = pickSkippedColor
    else:
        color = pickBadColor
    return color


def colorDrops(status):
    if status == DONE:
        return False
    if status == NORMAL:
        color = dropNormalColor
    elif status == FLIPPED:
        color = dropFlippedColor
    elif status == ASSIGNED:
        color = dropAssignedColor
    elif status == SKIPPED:
        color = pickSkippedColor
    return color


def initializePlot(conveyors, sliders, beams, params, ax, animated=True):
    """Initialize all plot elements and store references."""
    plot_elements = {
        "conveyors": [],
        "beams": [],
        "sliders": [],
        "picks": [],
        "drops": [],
        "all_artists": [],
    }

    # Initialize conveyors
    plot_elements = plotConveyors(conveyors, ax, plot_elements)

    # Initialize beams
    plot_elements = plotBeams(conveyors, beams, ax, plot_elements)

    # Initialize sliders
    for slider in flatten(sliders):

        ### Plot slider's carriage
        sliderSize, slider_xy, arm_xy, armSize, cup_xy = xySliders(slider)

        sliderRect = patches.Rectangle(
            slider_xy,
            *sliderSize,
            linewidth=1,
            edgecolor="black",
            facecolor=sliderColor,
            alpha=sliderAlpha,
            animated=animated,
        )

        ax.add_patch(sliderRect)

        ### Plot slider's arm
        armRect = patches.Rectangle(
            arm_xy,
            *armSize,
            linewidth=1,
            edgecolor="black",
            facecolor=sliderColor,
            alpha=sliderAlpha,
            label="Slider region",
            animated=animated,
        )
        ax.add_patch(armRect)

        ### Plot slider's cup
        cupCircle = patches.Circle(
            (cup_xy),
            30,
            linewidth=1,
            edgecolor="black",
            facecolor=sliderColor,
            alpha=sliderAlpha,
            animated=animated,
        )
        ax.add_patch(cupCircle)

        plot_elements["sliders"].append(
            {"carriage": sliderRect, "arm": armRect, "cup": cupCircle}
        )

    # Initialize picks
    for picks in conveyors.listPicks.values():
        color = colorPicks(picks["status"])
        if color == False:
            continue
        scatter = ax.scatter(
            picks["pos"][0],
            picks["pos"][1],
            color=color,
            s=50,
            animated=animated,
        )
        plot_elements["picks"].append(scatter)

    # Initialize drops
    for drops in conveyors.listDrops.values():
        color = colorDrops(drops["status"])
        if color == False:
            color = "red"
            alpha = 0.6
        else:
            alpha = 0.3
        scatter = ax.scatter(
            drops["pos"][0],
            drops["pos"][1],
            color=color,
            s=50,
            edgecolor="black",
            alpha=alpha,
            animated=animated,
        )
        plot_elements["drops"].append(scatter)

    # Collect all artists for blitting
    all_artists = (
        plot_elements["conveyors"]
        + plot_elements["beams"]
        + [slider["carriage"] for slider in plot_elements["sliders"]]
        + [slider["arm"] for slider in plot_elements["sliders"]]
        + [slider["cup"] for slider in plot_elements["sliders"]]
        + plot_elements["picks"]
        + plot_elements["drops"]
    )

    plot_elements["all_artists"] = all_artists
    ax.invert_yaxis()

    return plot_elements


def updatePlot(conveyors, sliders, plot_elements):
    """Update the positions and properties of existing plot elements."""
    updated_artists = []

    # Update sliders
    for slider_patch, slider in zip(plot_elements["sliders"], flatten(sliders)):
        # Update carriage position
        _, new_slider_xy, arm_xy, armSize, cup_xy = xySliders(slider)
        slider_patch["carriage"].set_xy(new_slider_xy)

        slider_patch["arm"].set_xy(arm_xy)
        slider_patch["arm"].set_width(armSize[0])
        slider_patch["arm"].set_height(armSize[1])

        # Update cup position
        slider_patch["cup"].center = cup_xy

        # Collect updated artists
        updated_artists.extend(
            [slider_patch["carriage"], slider_patch["arm"], slider_patch["cup"]]
        )

    # Update picks
    ## change both of these loops. It updates the existings scatters, but doesnt add new ones
    for scatter, picks in zip(
        plot_elements["picks"],
        conveyors.listPicks.values(),
    ):
        # TODO peut etre plus simple à écrire
        scatter.set_offsets([picks["pos"][0], picks["pos"][1]])
        status = picks["status"]
        color = colorPicks(status)
        if color == False:
            scatter.set_visible(False)
        else:
            scatter.set_color(color)
        updated_artists.append(scatter)

    # Update drops
    for scatter, drops in zip(
        plot_elements["drops"],
        conveyors.listDrops.values(),
    ):
        scatter.set_offsets([drops["pos"][0], drops["pos"][1]])
        status = drops["status"]

        if status == DONE:
            scatter.set_alpha(0.6)
        updated_artists.append(scatter)

    return updated_artists


def flatten(nested_list):
    """Flatten a nested list of sliders."""
    return [slider for rail in nested_list for slider in rail]


# def liveUpdatePlot(conveyors, sliders, beams, params, dt, plotEvery, isGifSaved):
#     ax.cla()
#     initializePlot(conveyors, sliders, beams, params, isGifSaved)

#     ax.set_xlim(-PLOT_MARGIN, fig_dim[0])
#     ax.set_ylim(fig_dim[1], -PLOT_MARGIN)
#     plt.pause(dt * plotEvery)


def setupPlot(conveyors, sliders, beams, params, isGifSaved, quitFunc):
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_aspect("equal", adjustable="box")
    inDoI = np.array(conveyors.inDirection)
    inDoIID = inDoI[ORTHOG_DIR]
    temp1 = conveyors.length * inDoI
    dir1 = (
        np.array(conveyors.listInConveyor[-1]["endPos"])
        + conveyors.listInConveyor[-1]["width"]
        + 4 * PLOT_MARGIN
    ) * np.abs(inDoI[::-1])

    dir2 = (
        np.array(conveyors.listOutConveyor[-1]["endPos"])
        + conveyors.listOutConveyor[-1]["width"]
        + 4 * PLOT_MARGIN
    ) * np.abs(inDoI[::-1])

    if dir1[inDoIID] > dir2[inDoIID]:
        fig_dim = np.add(temp1, dir1)
    else:
        fig_dim = np.add(temp1, dir2)
    "Initialize plot elements"
    plot_elements = initializePlot(conveyors, sliders, beams, params, ax, isGifSaved)

    # fig.canvas.manager.window.wm_geometry("+185-1520")
    "Make plot full screen"
    # fig.canvas.manager.full_screen_toggle()



    fig.canvas.mpl_connect("key_press_event", quitFunc)
    return fig, ax, fig_dim, plot_elements
