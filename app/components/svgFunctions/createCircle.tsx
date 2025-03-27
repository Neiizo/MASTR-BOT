import React from "react";

interface circleProp {
  // x: number;
  // y: number;
  xy: number[];
  r: number;
  style: { fill: string; strokeWidth: number; stroke: string };
  alpha: number;
  key: string;
}

interface CreateCircleProps {
  circle: circleProp;
  scaling: number;
  xyOffset: number[];
}

export const CreateCircle = ({
  circle,
  scaling,
  xyOffset,
}: CreateCircleProps) => {
  const radius = circle.r * scaling;
  const posX = (circle.xy[0] + xyOffset[0]) * scaling;
  const posY = (circle.xy[1] + xyOffset[1]) * scaling;

  return (
    <circle
      cx={posX}
      cy={posY}
      r={radius}
      opacity={circle.alpha}
      style={circle.style}
    />
  );
};
export default CreateCircle;
