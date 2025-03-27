import React from "react";

interface CoordInputProps {
  axis: string;
  coord: number | undefined;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

const CoordInput = ({ axis, coord, onChange }: CoordInputProps) => {
  return (
    <div className="flex justify-center items-center">
      <p className="w-5">{axis.toUpperCase()}: </p>
      <input
        type="text"
        onChange={onChange}
        id={axis}
        value={coord !== undefined ? coord.toString() : ""}
        className="input input-bordered w-20 h-8 -px-4"
        disabled={coord === undefined}
      />
    </div>
  );
};

export default CoordInput;
