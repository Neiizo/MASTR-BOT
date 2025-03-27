import React from "react";

interface Data {
  unit: Record<string, string>;
  conveyor: Record<string, any>;
  slider: Record<string, any>;
  beam: Record<string, any>;
  target: Record<string, any>;
  timeStep: number;
}

interface rectProp {
  xy: number[];
  rectSize: number[];
  fill: string;
  alpha: number;
  key: string;
  text?: string;
}

interface prepRectListProps {
  setListRect: React.Dispatch<React.SetStateAction<rectProp[]>>;
  setScaling: React.Dispatch<React.SetStateAction<number | undefined>>;
  params: Data;
  xyOffset: number[];
  divID: string;
}

const setConveyor = (params: Data, c: string, idx: number) => {
  if (c === "in") {
    var width = params.conveyor.inWidth[idx];
    var direction = params.conveyor.inDirection;
    var endPosition = params.conveyor.inEndPos[idx];
    var fill = "rgb(170,250,210)";
  } else if (c === "out") {
    var width = params.conveyor.outWidth[idx];
    var direction = params.conveyor.outDirection;
    var endPosition = params.conveyor.outEndPos[idx];
    var fill = "rgb(250,170,170)";
  } else {
    console.warn("Error with the conveyor type when creating SVG object.");
    // setShowAlert(true);
    // setAlertText("Error with the conveyor type when creating SVG object.");
    return { xy: [0, 0], rectSize: [0, 0], fill: "", alpha: 0, key: "" };
  }

  width = [Math.abs(direction[1] * width), Math.abs(direction[0] * width)];
  const length = direction.map((val: number) => -val * params.conveyor.length);
  const rectSize = [width[0] + length[0], width[1] + length[1]];
  var xy = endPosition.map((val: number, idx: number) => val - width[idx] / 2);
  if (rectSize[0] < 0) {
    xy[0] = xy[0] + rectSize[0];
    rectSize[0] = -rectSize[0];
  }
  if (rectSize[1] < 0) {
    xy[1] = xy[1] + rectSize[1];
    rectSize[1] = -rectSize[1];
  }
  const key = `conveyor-${c}-${idx}`;
  return { xy, rectSize, fill, alpha: 1, key };
};

const setBeams = (
  params: Data,
  listRect: rectProp[],
  minX: number,
  maxX: number,
  minY: number,
  maxY: number,
  minMax: (i: number, min: number, max: number, newRect: rectProp) => number[]
) => {
  var beamPosition = params.beam.firstBeamPos;
  const bWidth = params.beam.width;
  const bLength = params.beam.length;
  for (let i = 0; i < params.beam.nbOfBeams; i++) {
    const direction = params.beam.direction;
    //! CHANGE HERE IF YOU NEED TO CHANGE THE DIRECTION OF THE PLOTS
    const sign = params.conveyor.inDirection[params.conveyor.inDirection[1]];
    const width = [bWidth * direction[1], bWidth * direction[0]];
    const length = [bLength * direction[0], bLength * direction[1]];
    const rectSize = [width[0] + length[0], width[1] + length[1]];
    const fill = "gray";
    const alpha = 0.3;
    beamPosition =
      params.beam.firstBeamPos + i * params.beam.spacing * sign - bWidth / 2;
    const xy = [
      direction[1] * beamPosition - direction[0] * 70,
      direction[0] * beamPosition - direction[1] * 70,
    ];

    const key = `beam-${i}`;
    const text = i.toString();
    const newRect = { xy, rectSize, fill, alpha, key, text };
    listRect.push(newRect);
    [minX, maxX] = minMax(0, minX, maxX, newRect);
    [minY, maxY] = minMax(1, minY, maxY, newRect);
  }
  return listRect;
};

const defineRectList = ({
  setListRect,
  setScaling,
  params,
  xyOffset,
  divID,
}: prepRectListProps) => {
  var listRect: rectProp[] = [];
  var minX = 0;
  var maxX = 0;
  var minY = 0;
  var maxY = 0;

  const minMax = (i: number, min: number, max: number, newRect: rectProp) => {
    if (newRect.xy[i] < min) min = newRect.xy[i];
    if (newRect.xy[i] + newRect.rectSize[i] < min)
      min = newRect.xy[i] + newRect.rectSize[i];
    if (newRect.xy[i] > max) max = newRect.xy[i];
    if (newRect.xy[i] + newRect.rectSize[i] > max)
      max = newRect.xy[i] + newRect.rectSize[i];
    return [min, max];
  };

  const newConveyor = (s: string, i: number) => {
    const newRect = setConveyor(params, s, i);
    listRect.push(newRect);
    [minX, maxX] = minMax(0, minX, maxX, newRect);
    [minY, maxY] = minMax(1, minY, maxY, newRect);
  };

  for (let i = 0; i < params.conveyor.nbInConveyor; i++) {
    newConveyor("in", i);
  }

  for (let i = 0; i < params.conveyor.nbOutConveyor; i++) {
    newConveyor("out", i);
  }

  // set Scaling, including some offsets
  listRect = setBeams(params, listRect, minX, maxX, minY, maxY, minMax);
  const width = maxX - minX + 2 * xyOffset[0];

  var w = document.getElementById(divID)?.offsetWidth!;
  // setScaling(1);
  setScaling(w / width);
  console.log("width w is ", w );
  //TODO maybe there's a function like in python, to find the minimum accross a list
  setListRect(listRect);
};

const prepRectList = ({
  setListRect,
  setScaling,
  params,
  xyOffset,
  divID,
}: prepRectListProps) => {
  defineRectList({ setListRect, setScaling, params, xyOffset, divID });
};

export default prepRectList;
