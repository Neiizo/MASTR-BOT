import React from "react";

import { CreateCircle } from "../svgFunctions/createCircle";

interface colorPreviewProps {
  className: string;
}

interface circleProp {
  xy: number[];
  r: number;
  style: { fill: string; strokeWidth: number; stroke: string };
  alpha: number;
  key: string;
}

const colorMap = [
  { id: 0, fill: "rgb(130,230,230)", alpha: 1, name: "FREE" },
  { id: 1, fill: "rgb(250, 250, 130)", alpha: 1, name: "ASSIGNED" },
  // { id: 1, fill: "rgb(200, 200, 130)", alpha: 1, name: "ASSIGNED" },
  { id: 2, fill: "rgb(230,130,130)", alpha: 1, name: "SKIPPED" },
  { id: 3, fill: "rgb(0,0,0)", alpha: 0, name: "GONE" },
  { id: 4, fill: "rgb(110,110,110)", alpha: 1, name: "BAD" },
  { id: 10, fill: "rgb(230,170,120)", alpha: 1, name: "NORMAL" },
  { id: 11, fill: "rgb(130,230,130)", alpha: 1, name: "FLIPPED" },
  { id: 13, fill: "rgb(255, 255, 255)", alpha: 1, name: "FILLED" },
];

export const ColorPreview = ({ className }: colorPreviewProps) => {
  var listColors: circleProp[] = [];
  Array.from(colorMap).forEach((element) => {
    const res = statusColor(element.id, "test");
    listColors.push({
      r: 10,
      xy: [11, 11],
      style: res.style,
      alpha: res.alpha,
      key: res.name as string,
    });
  });

  return (
    <div className={`${className}`}>
      <div className="collapse collapse-arrow">
        <input type="checkbox" />
        <div className="collapse-title text-xl font-medium">
          <u>Color preview : </u>
        </div>
        <div className="collapse-content">
          {listColors.map((val: circleProp) => (
            <React.Fragment key={val.key}>
              <div className="grid grid-cols-5">
                <svg width="25" height="25" className="col-span-1">
                  <CreateCircle circle={val} scaling={1} xyOffset={[0, 0]} />
                </svg>
                <span className="col-span-3">: {val.key}</span>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};

export const statusColor = (ID: number, test?: string) => {
  const color = colorMap.find((color) => color.id === ID);
  if (!color) {
    return {
      style: { fill: "rgb(0,0,0)", strokeWidth: 2, stroke: "rgb(0,0,0)" },
      alpha: 1,
    };
  }
  const style = { fill: color.fill, strokeWidth: 2, stroke: "rgb(0,0,0)" };
  if (test === "test") {
    return { style, alpha: color.alpha, name: color.name };
  } else {
    return { style, alpha: color.alpha };
  }
};
