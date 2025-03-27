"use client";
import React from "react";

interface DropDownListProps {
  value: any;
  listString: string[];
  listStringValues: string[];
  onChange: (event: React.ChangeEvent<HTMLSelectElement>) => void;
}

const DropDownList = ({
  value,
  listString,
  listStringValues,
  onChange,
}: DropDownListProps) => {
  return (
    <select
    value={typeof value === "string" ? value : ""}
    onChange={onChange}
    className="select select-bordered w-24"
    >
      {listString.map((listString, idx) => (
        <option key={listString} value={listStringValues[idx]}>
          {listString}
        </option>
      ))}
    </select>
  );
};

export default DropDownList;
