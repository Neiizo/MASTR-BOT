"use client";
//TODO CLEAN THIS MESS.
import React, { useEffect, useState } from "react";
import ErrorAlert from "../components/ErrorAlert";
import { loadFile } from "../components/lib/loadFile";
import { useData } from "../context/DataContext";
import CreateCircle from "../components/svgFunctions/createCircle";
import CreateRect from "../components/svgFunctions/createRect";
import prepRectList from "../components/svgFunctions/prepRectList";
import ParamInput from "../components/ParamInput";
import BtnMenu from "../components/btnMenu";
import { fetchHistNames } from "../components/lib/jsonHandling";

import { statusColor, ColorPreview } from "../components/lib/dropTargetColor";
import BeamStatus from "../components/beamStatus";
import SliderStatus from "../components/sliderStatus";
import idToStatus from "../components/lib/idToStatus";
import { time } from "console";

interface Data {
  unit: Record<string, string>;
  conveyor: Record<string, any>;
  slider: Record<string, any>;
  beam: Record<string, any>;
  target: Record<string, any>;
  timeStep: number;
}

interface History {
  [key: string]: stepHistory;
}

interface stepHistory {
  targets: Record<string, any>;
  drops: Record<string, any>;
  sliders: Record<string, any>;
  beams: Record<string, any>;
}

interface circleProp {
  xy: number[];
  r: number;
  style: { fill: string; strokeWidth: number; stroke: string };
  alpha: number;
  key: string;
}

interface rectProp {
  xy: number[];
  rectSize: number[];
  fill: string;
  alpha: number;
  key: string;
  text?: string;
}

const Simulation = () => {
  // todo there s probably a way to reduce the amount of usestate, like a usestate per type of object
  const { data: currentParam } = useData();
  const [existingSim, setExistingSim] = useState<string[]>([]);
  const [showAlert, setShowAlert] = useState<boolean>(false);
  const [alertText, setAlertText] = useState<string>("");
  const [targetsPosition, setTargetsPosition] = useState<circleProp[]>([]);
  const [dropsPosition, setDropsPosition] = useState<circleProp[]>([]);
  const [scaling, setScaling] = useState<number>();
  const [listRect, setListRect] = useState<rectProp[]>([]);
  const [listSliders, setListSliders] = useState<rectProp[]>([]);
  const [listSlidersArm, setListSlidersArm] = useState<rectProp[]>([]);
  const [listSlidersHead, setListSlidersHead] = useState<circleProp[]>([]);
  const [timerStatus, setTimerStatus] = useState<boolean>(false);
  const [hist, setHist] = useState<History>();
  const [params, setParams] = useState<Data>();
  const [timeStep, setTimeStep] = useState<number>(0);
  const [totalTimesteps, setTotalTimesteps] = useState<number>(0);
  const [initialUpdateDone, setInitialUpdateDone] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(3);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadLastSim, setLoadLastSim] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<string>("");
  const [timerID, setTimerID] = useState<NodeJS.Timeout>();

  const dropTargetVariables = {
    // Note used to make code cleaner, as drawing a points or a target is the same, but the lists are separate
    targets: targetsPosition,
    drops: dropsPosition,
  };

  const setDropTargetVariables = {
    // Note used to make code cleaner, as drawing a points or a target is the same, but the lists are separate
    targets: setTargetsPosition,
    drops: setDropsPosition,
  };

  const xyOffset = [100, 80];
  const speeds = [0.25, 0.5, 0.75, 1];
  const sliderColor = "rgb(160,160,160)";
  const sliderColorPicked = "rgb(0,110,250)";
  const sliderAlpha = 0.8;
  useEffect(() => {
    // If the speed is changed while simulating, restarts the timer to adjust the speed live.
    if (initialUpdateDone && timerStatus) {
      clearInterval(timerID);
      startTimer();
    }
  }, [speed]); // also do this for the progress bar

  useEffect(() => {
    if (
      // Waits until the listSliders is properly initialized, to call updateSlider
      listSliders.length > 0 &&
      !initialUpdateDone
    ) {
      updateSliders(timeStep);
      setInitialUpdateDone(true);
    }
  }, [listSliders]);

  useEffect(() => {
    // Once the required data has been loaded, start setting up the page
    if (params) {
      console.log("Setting up the page");
      // defineRectList();
      prepRectList({
        setListRect,
        setScaling,
        params,
        xyOffset,
        divID: "big-SVG",
      });
      if (hist) {
        setSliders();
      } else {
        setInitialUpdateDone(true);
      }
    }
  }, [params, hist]);

  useEffect(() => {
    fetchHistNames({ setNames: setExistingSim }, "Current configuration");
  }, []);

  useEffect(() => {
    if (loadLastSim && existingSim.length > 0) {
      console.log("loading sim ", existingSim[existingSim.length - 1]);
      // setSelectedFile(existingSim[existingSim.length - 1]);
      const event = {
        target: { value: existingSim[existingSim.length - 1] },
      } as React.ChangeEvent<HTMLSelectElement>;
      handleSimulationLoading(event);
      setLoadLastSim(false);
    }
  }, [existingSim]);

  // window.addEventListener("keydown", onKeyDown, true);
  // function onKeyDown(e: KeyboardEvent) {
  //   if (e.key === "ArrowLeft" && timeStep > 0 && !timerStatus && hist) {
  //     nextPosition(timeStep - 1);
  //   } else if (
  //     e.key === "ArrowRight" &&
  //     timeStep < totalTimesteps &&
  //     !timerStatus &&
  //     hist
  //   ) {
  //     nextPosition(timeStep + 1);
  //   }
  // }

  const handleCloseAlert = () => {
    // NOTE currently useless, need to revisit alert for the whole project. Add them to the side of the screen
    setShowAlert(false);
    setAlertText("Unexpected behavior regarding the alert's text.");
  };

  const handleLastSim = async () => {
    await fetchHistNames({ setNames: setExistingSim }, "Current configuration");
    setLoadLastSim(true);
  };

  const handleSimulationLoading = async (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    setSelectedFile(event.target.value);
    // Shows the loading ring
    setIsLoading(true);
    // Resets all the variables and states
    setInitialUpdateDone(false);
    setTimeStep(0);
    clearInterval(timerID);
    setTargetsPosition([]);
    setDropsPosition([]);
    const selectedSimulation = event.target.value;
    if (!selectedSimulation) {
      setAlertText("Invalid file name.");
      return;
    }
    if (selectedSimulation === "Current configuration") {
      setParams(currentParam);
      setHist(undefined);
      setListSliders([]);
      setListSlidersArm([]);
      setListSlidersHead([]);
      setTotalTimesteps(0);
      setIsLoading(false);
    } else {
      await loadData(selectedSimulation); // Pass the folder directly
    }
  };

  const loadData = async (folderName: String) => {
    try {
      const history = (await loadFile(
        `history/${folderName}/history.json`,
        "settings"
      )) as History;
      const params = (await loadFile(
        `history/${folderName}/params.json`,
        "settings"
      )) as Data;
      setHist(history);
      setParams(params);
      setTotalTimesteps(Object.keys(history).length - 1);
      setIsLoading(false);
      // setAlertText("");
    } catch (err) {
      console.error("Error loading file:", err);
      // setShowAlert(true);
      // setAlertText("Error loading file.");
    }
  };

  const setSliders = () => {
    if (!params || !hist) return null;
    // Note Uses a different list as the beams and conveyor, as it will be actively updated
    var sliders: rectProp[] = [];

    const bDir = params.beam.direction;
    const sWidth = params.slider.width;
    const width = [Math.abs(sWidth * bDir[0]), Math.abs(sWidth * bDir[1])];

    const tempLength = (params.slider.reach + params.slider.reachOffset) / 2;
    const length = [
      Math.abs(tempLength * bDir[1]),
      Math.abs(tempLength * bDir[0]),
    ];
    const rectSize = [width[0] + length[0], width[1] + length[1]];
    const alpha = sliderAlpha;
    const fill = sliderColor;

    for (let i = 0; i < hist[0]["sliders"]["position"].length; i++) {
      sliders.push({
        xy: [-1, -1],
        rectSize,
        fill,
        alpha,
        key: `slider-${i}`,
        text: i.toString(),
      });
    }
    setListSliders(sliders);

    setSlidersArm();
    setSlidersHead();
  };

  const setSlidersArm = () => {
    if (!params || !hist) return null;

    var armList: rectProp[] = [];
    for (let i = 0; i < hist[0]["sliders"]["position"].length; i++) {
      armList.push({
        xy: [-1, -1],
        rectSize: [0, 0],
        fill: sliderColor,
        alpha: sliderAlpha,
        key: `slider-arm-${i}`,
      });
    }
    setListSlidersArm(armList);
  };

  const setSlidersHead = () => {
    if (!params || !hist) return null;

    var headList: circleProp[] = [];
    for (let i = 0; i < hist[0]["sliders"]["position"].length; i++) {
      const position = [...hist[0]["sliders"]["position"][i]];
      headList.push({
        xy: position,
        r: params.target.width / 2,
        style: {
          fill: sliderColor,
          strokeWidth: 2,
          stroke: "rgb(0,0,0)",
        },
        alpha: sliderAlpha,
        key: `slider-head-${i}`,
      });
    }
    setListSlidersHead(headList);
  };

  const createPoints = (
    //TODO Change this. Currently, it is being called ALL the time
    variableName: "drops" | "targets"
  ) => {
    // We can probably clean this, it is somewhat redundant
    if (!params || !hist) return null;

    const nbItems = hist[timeStep][variableName]["position"].length;
    const currNbItems = dropTargetVariables[variableName].length;

    if (currNbItems > nbItems) {
      setDropTargetVariables[variableName](
        dropTargetVariables[variableName].slice(0, nbItems)
      );
      // marche que pour les targets
    }
    for (let i = currNbItems; i < nbItems; i++) {
      const newPosition = {
        xy: hist[timeStep][variableName]["position"][i],
        r: params.target.width / 2,
        ...(statusColor(hist[timeStep][variableName]["status"][i]) as {
          style: { fill: string; strokeWidth: number; stroke: string };
          alpha: number;
        }),
        key: `${variableName}-${i + currNbItems}`,
      };
      setDropTargetVariables[variableName]((prevPositions) => [
        ...prevPositions,
        newPosition,
      ]);
    }
  };

  const updatePosition = (variableName: "drops" | "targets", t: number) => {
    if (!params || !hist) return null;

    const newPositions = hist[t][variableName]["position"];
    const newPositionsStatus = hist[t][variableName]["status"];
    const currNbPositions = dropTargetVariables[variableName].length;
    var tempPositions = [...dropTargetVariables[variableName]];
    for (let i = 0; i < Math.min(currNbPositions, newPositions.length); i++) {
      tempPositions[i] = {
        xy: newPositions[i],
        r: tempPositions[i].r,
        ...(statusColor(newPositionsStatus[i]) as {
          style: { fill: string; strokeWidth: number; stroke: string };
          alpha: number;
        }),
        key: tempPositions[i].key,
      };
    }
    setDropTargetVariables[variableName](tempPositions);
    // take the list of position "targetsPosition", and update with the new value
  };

  const updateSliders = (t: number) => {
    if (!params || !hist) return null;

    if (listSliders.length > 0) {
      var tempList = [...listSliders];
      var tempHeadList = [...listSlidersHead];
      var tempArmList = [...listSlidersArm];

      for (let i = 0; i < listSliders.length; i++) {
        if (i % 4 >= 2) {
          var side = 1;
        } else {
          var side = -1;
        }

        //! CHANGE HERE IF YOU NEED TO CHANGE THE DIRECTION OF THE PLOTS
        const sign =
          params.conveyor.inDirection[params.conveyor.inDirection[1]];
        const beamPos =
          params.beam.firstBeamPos +
          Math.floor(i / 4) * params.beam.spacing * sign;
        const tempLength =
          (params.slider.reach + params.slider.reachOffset) / 2;
        const bDir = params.beam.direction;
        const lengthOffset = side === 1 ? 0 : -tempLength;

        const position = hist[t]["sliders"]["position"][i];

        const defineXY = (j: number) => {
          return (
            (position[j] - params.slider.width / 2) * bDir[j] +
            (beamPos + lengthOffset + (params.beam.width * side) / 2) *
              bDir[1 - j]
          );
        };
        tempList[i].xy = [defineXY(0), defineXY(1)];

        // doesn't need to use setListSlidersHead, as it is a shallow copy

        var nextColor = sliderColor;
        // this if statement is good to capture the transition (so with timeSteps of 1)
        // but bad when jumping to an arbitrary timeStep, as it will not update the color of the slider
        if (idToStatus(hist[t]["sliders"]["status"][i]) === "Z_MVMT") {
          if (
            idToStatus(hist[t]["beams"]["status"][Math.floor(i / 2)]) ===
              "PICKING" &&
            t - timeStep > 0
          ) {
            nextColor = sliderColorPicked;
          } else if (
            idToStatus(hist[t]["beams"]["status"][Math.floor(i / 2)]) ===
              "PLACING" &&
            !(t - timeStep > 0)
          ) {
            nextColor = sliderColorPicked;
          }
        } else {
          nextColor = tempHeadList[i].style.fill;
        }

        if (nextColor !== tempHeadList[i].style.fill) {
          tempHeadList[i].style = {
            fill: nextColor,
            strokeWidth: 2,
            stroke: "rgb(0,0,0)",
          };
        }
        tempHeadList[i].xy = position;

        // armList
        const armWidth = [
          params.slider.armWidth * bDir[0],
          params.slider.armWidth * bDir[1],
        ];

        const defineArmLength = (idx: number, j: number) => {
          return Math.abs(
            bDir[1 - j] * (position[j] - tempList[idx].xy[j] - tempLength / 2)
          );
        };
        const armLength = [defineArmLength(i, 0), defineArmLength(i, 1)];

        const sideOffset = side === 1 ? [0, 0] : [-armLength[0], -armLength[1]];
        tempArmList[i].rectSize = [
          armWidth[0] + armLength[0],
          armWidth[1] + armLength[1],
        ];

        const setArmXY = (idx: number, j: number) => {
          return (
            position[j] -
            tempArmList[idx].rectSize[j] +
            (Math.abs(bDir[j]) * armWidth[j]) / 2 -
            sideOffset[j]
          );
        };

        tempArmList[i].xy = [setArmXY(i, 0), setArmXY(i, 1)];
      }
      // setListSliders(tempList); // doesn't need to use setListSliders, as it is a shallow copy
      setListSlidersHead(tempHeadList);
    }
  };

  const nextPosition = (t: number) => {
    setTimeStep(t);
    updatePosition("targets", t);
    updatePosition("drops", t);
    updateSliders(t);
  };

  const handleProgressBar = (event: React.ChangeEvent<HTMLInputElement>) => {
    nextPosition(parseInt(event.target.value));
    if (initialUpdateDone && timerStatus) {
      clearInterval(timerID);
      startTimer();
    }
  };

  const handleSpeedBar = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSpeed(parseInt(event.target.value));
  };

  if (params && hist) {
    createPoints("targets");
    createPoints("drops");
  }

  const startTimer = () => {
    if (!params || !hist) return null;

    let i = 0;
    var timeInterval = (params.timeStep * 1000) / speeds[speed];
    var frameInterval = 1;
    // as the timeStep is smaller, there are more updates to do, so it takes slower to complete a full second.
    // To fix this problem, we skip some frames, to stay under 30 fps.
    if (timeInterval < 15) {
      frameInterval = 4;
    } else if (timeInterval < 30) {
      frameInterval = 2;
    }

    const newTimerID = setInterval(() => {
      if (timeStep + i > totalTimesteps) {
        clearInterval(newTimerID);
        setTimerStatus(false);
      } else {
        setTimerStatus(true);
        nextPosition(timeStep + i);
        i += frameInterval;
      }
    }, (params.timeStep * 1000 * frameInterval) / speeds[speed]);
    setTimerID(newTimerID);
  };
  // const [screenHeight, setScreenHeight] = useState(0);

  // useEffect(() => {
  //   const updateHeight = () => setScreenHeight(window.screen.width*0.33);
  //   updateHeight(); // Set initial height
  //   window.addEventListener("resize", updateHeight); // Update on resize
  //   return () => window.removeEventListener("resize", updateHeight);
  // }, []);

  return (
    <div className="mx-auto w-full mt-2 h-screen ">
      {showAlert && (
        <ErrorAlert alertText={alertText} onClose={handleCloseAlert} />
      )}
      {isLoading && (
        <span className="absolute left-[50%] top-[370px] transform -translate-x-1/2 -translate-y-1/2 loading loading-ring loading-lg " />
      )}
      {!listRect.length && !initialUpdateDone && !isLoading && (
        <div className="absolute left-[50%] top-[370px] transform -translate-x-1/2 -translate-y-1/2">
          Load a file first
        </div>
      )}
      <div className="fixed md:left-[82%] lg:left-[82%] top-14 space-y-1m join join-vertical w-[17%]">
        <ColorPreview className=" join-item border-base-300 bg-base-200 border" />
        {hist && (
          <>
            <BeamStatus
              className="join-item border-base-300 bg-base-200 border"
              beams={hist[timeStep]["beams"]["status"]}
            />
            <SliderStatus
              className="join-item border-base-300 bg-base-200 border"
              sliders={hist[timeStep]["sliders"]["status"]}
            />
          </>
        )}
      </div>
      <div className="md:w-[95%] lg:w-[95%]" id="big-SVG">
        <svg
          width="100%"
          className="mt-14 card border-2 py-2 h-[33.5vw]"
          // style={{ height: `${screenHeight}px` }} // Use dynamic height
          // className="mt-14 card border-2 py-2 h-[650px] md:h-[650px] lg:h-[700px]"
        >
          {initialUpdateDone && (
            <>
              {listRect.map((val: rectProp) => (
                <React.Fragment key={val.key}>
                  <CreateRect
                    rect={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
              {targetsPosition.map((val: circleProp) => (
                <React.Fragment key={val.key}>
                  <CreateCircle
                    circle={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
              {dropsPosition.map((val: circleProp) => (
                <React.Fragment key={val.key}>
                  <CreateCircle
                    circle={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
              {listSlidersArm.map((val: rectProp) => (
                <React.Fragment key={val.key}>
                  <CreateRect
                    rect={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
              {listSliders.map((val: rectProp) => (
                <React.Fragment key={val.key}>
                  <CreateRect
                    rect={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
              {listSlidersHead.map((val: circleProp) => (
                <React.Fragment key={val.key}>
                  <CreateCircle
                    circle={val}
                    scaling={scaling!}
                    xyOffset={xyOffset}
                  />
                </React.Fragment>
              ))}
            </>
          )}
        </svg>
      </div>
      <div
        id="control-buttons"
        className="pt-4 space-x-2 flex justify-center items-center"
      >
        <button
          className="btn btn-active w-20"
          onClick={() => {
            if (timerStatus) {
              console.log("pausing");
              clearInterval(timerID);
              setTimerStatus(false);
            } else {
              startTimer();
            }
          }}
          disabled={!hist}
        >
          {timerStatus ? "Pause" : "Play"}
        </button>
        <button
          className="btn btn-active"
          onClick={() => {
            nextPosition(timeStep - 1);
          }}
          disabled={timeStep <= 0 || timerStatus || !hist}
        >
          Step backward
        </button>
        <button
          className="btn btn-active"
          onClick={() => {
            nextPosition(timeStep + 1);
          }}
          disabled={timeStep >= totalTimesteps || timerStatus || !hist}
        >
          Step forward
        </button>
        <div className="card border w-1/4 justify-between px-4 py-1 text-xs">
          Speed :
          <input
            type="range"
            min={0}
            max={speeds.length - 1}
            value={speed}
            className="range range-xs "
            onChange={handleSpeedBar}
            step="1"
          />
          <ul className="flex w-full justify-between">
            {speeds.map((val) => {
              return <li key={val}>x{val}</li>;
            })}
          </ul>
        </div>
        <BtnMenu
          options={existingSim}
          btnString="Select simulation"
          onClick={() =>
            fetchHistNames(
              { setNames: setExistingSim },
              "Current configuration"
            )
          }
          onChange={handleSimulationLoading}
          selectedFile={selectedFile}
        />
        <button className="btn btn-active" onClick={handleLastSim}>
          Last simulation
        </button>
      </div>
      <div>
        <ParamInput
          paramString="Time step"
          previousValue={timeStep}
          unit=""
          onValueChange={nextPosition}
        />
        <input
          type="range"
          min={0}
          max={totalTimesteps}
          value={timeStep}
          onChange={handleProgressBar}
          className="range range-xs"
        />
      </div>
    </div>
  );
};

export default Simulation;
