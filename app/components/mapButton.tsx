import React from "react";

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

interface ColorButtonProps {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  colorName: string;
}

interface MoveButtonProps {}

export const ColorButton = ({ colorName, onChange }: ColorButtonProps) => {
  return (
    <input
      aria-label={colorName}
      type="radio"
      className="btn btn-outline"
      value={colorName}
      onChange={onChange}
      name="modifyPoint"
    />
  );
};

interface MoveButtonProps {
  onChange: () => void;
  selected: boolean;
}

export const MoveButton = ({ onChange, selected }: MoveButtonProps) => {
  return (
    <label
      className={`flex items-center cursor-pointer square mt-5 mb-5 btn ${
        selected ? " btn-primary" : " btn-outline "
      }`}
    >
      <input
        type="radio"
        name="modifyPoint"
        onChange={onChange}
        className="hidden"
      />
      <FontAwesomeIcon icon="arrows" className="mr-1 text-xl align-center" />
    </label>
  );
};
