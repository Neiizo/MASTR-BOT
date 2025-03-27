import React from "react";

interface rectProp {
  xy: number[];
  rectSize: number[];
  fill: string;
  alpha: number;
  key: string;
  text?: string;
}

interface CreateRectProps {
  rect: rectProp;
  scaling: number;
  xyOffset: number[];
}

export const CreateRect = ({ rect, scaling, xyOffset }: CreateRectProps) => {
  const posX = (rect.xy[0] + xyOffset[0]) * scaling;
  const posY = (rect.xy[1] + xyOffset[1]) * scaling;
  const width = rect.rectSize[0] * scaling;
  const length = rect.rectSize[1] * scaling;
  return (
    <g>
      <rect
        x={posX}
        y={posY}
        width={width}
        height={length}
        opacity={rect.alpha}
        style={{
          fill: rect.fill,
          strokeWidth: 2,
          stroke: "rgb(0,0,0)",
        }}
      />
      <text
        x={posX + width / 2}
        y={posY + length / 2}
        fontFamily="Verdana"
        fontSize={35 * scaling}
        fill="blue"
        textAnchor="middle"
        alignmentBaseline="middle"
      >
        {rect.text}
      </text>
    </g>
  );
};

export default CreateRect;
