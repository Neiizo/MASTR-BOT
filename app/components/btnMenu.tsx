"use client";
import React from "react";

interface btnMenuProps {
  options: string[];
  btnString: string;
  onClick?: React.MouseEventHandler<HTMLSelectElement>;
  onChange?: React.ChangeEventHandler<HTMLSelectElement>;
  className?: string;
  selectedFile?: string;
}

const BtnMenu = ({
  options,
  btnString,
  onClick,
  onChange,
  className,
  selectedFile,
}: btnMenuProps) => {
  return (
    <select
      className={`select select-bordered ${className}`}
      onChange={onChange}
      onClick={onClick}
      defaultValue={""}
    >
      <option disabled value="">
        {btnString}
      </option>
      {options.map((fileName) => (
        <option
          key={fileName}
          value={fileName}
          selected={fileName === selectedFile}
        >
          {fileName}
        </option>
      ))}
    </select>
  );
};
export default BtnMenu;

// <select className="select select-bordered w-full max-w-xs">
//   <option disabled selected>Who shot first?</option>
//   <option>Han Solo</option>
//   <option>Greedo</option>
// </select>
