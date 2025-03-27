from IPython.display import display
from ipywidgets import widgets
import numpy as np
import pandas as pd


def selectFile(names: str, defaultValue=None):
    if defaultValue not in names:
        defaultValue = names[-1]
    file_dropdown = widgets.Dropdown(
        options=names,
        value=defaultValue if defaultValue is not None else names[0],
        description="Select the file to analyse:",
        disabled=False,
        layout=widgets.Layout(width="50%"),
        style={"description_width": "initial"},
    )

    display(file_dropdown)
    return file_dropdown


def format_data(selected_variable, nBeams, rounding, params, data):
    v = data[selected_variable].unique()

    workload_data = []
    pickPerSlider_data = []
    # Calculate the workload and pickPerSlider for each run
    for index, row in data.iterrows():
        total_time = row["totalTimeSteps"] - row["startRecordingTime"]
        workload_data.append(np.array(row["workload"]) / total_time)
        pickPerSlider_data.append(
            np.array(row["pickPerSlider"]) * 60 / (total_time * row["dt"])
        )

    formatted_data = pd.DataFrame(
        columns=[
            "missedPicks",
            "missedDrops",
            "unfilledPackages",
            "workload",
            "pickPerSlider",
            # "slidersVelocity",
            # "slidersAcceleration",
        ]
        + [f"beam_{idx}" for idx in range(nBeams)]
        + [selected_variable]
    )

    # Calculate the average stats per set of parameters
    for idx, val in enumerate(v):
        index = data[data[selected_variable] == val]["missedDrops"].index
        pickPerSlider_values = [pickPerSlider_data[i] for i in index]
        pickAvg = np.mean(pickPerSlider_values, axis=0)
        workload_values = [workload_data[i] for i in index]
        workloadAvg = np.mean(workload_values, axis=0)
        workloadSTD = np.std(workload_values, axis=0)

        missedPicks = (
            data[data[selected_variable] == val]["missedPicks"].values
            * 100
            / data[data[selected_variable] == val]["totalPicks"].values
        )

        missedPicksMean = round(missedPicks.mean(), rounding)
        missedPicksSTD = round(missedPicks.std(), rounding)

        missedDrops = (
            data[data[selected_variable] == val]["missedDrops"].values
            * 100
            / data[data[selected_variable] == val]["totalDrops"].values
        )

        missedDropsMean = round(missedDrops.mean(), rounding)
        missedDropsSTD = round(missedDrops.std(), rounding)
        unfilledPackages = round(
            (
                data[data[selected_variable] == val]["unfilledPackages"].values
                * 100
                / data[data[selected_variable] == val]["totalPackages"].values
            ).mean(),
            rounding,
        )

        # if "slidersVelocity" in data.columns:

        #     pass
        # if "slidersAcceleration" in data.columns:
        #     pass
        newRow = {
            "missedPicks": missedPicksMean,
            "missedPicksSTD": missedPicksSTD,
            "missedDrops": missedDropsMean,
            "missedDropsSTD": missedDropsSTD,
            "unfilledPackages": unfilledPackages,
            "workload": workloadAvg,
            "workloadSTD": workloadSTD,
            # "slidersVelocity":,
            # "slidersAcceleration":,
            "pickPerSlider": pickAvg,
            selected_variable: val,
        }

        for i in range(nBeams):
            if selected_variable == "scheduling":
                newRow[f"beam_{i}"] = eval(val)[i]
            else:
                newRow[f"beam_{i}"] = params["beam"]["scheduling"][i]
        formatted_data.loc[idx] = newRow
    return formatted_data
