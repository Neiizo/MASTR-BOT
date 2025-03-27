// components/ParamInput.tsx
"use client";
import DropDownList from "../components/dropDownList";
import React, { useState, useEffect, ChangeEvent, KeyboardEvent } from "react";

interface ParamInputProps {
  paramString: string;
  previousValue: any;
  unit: string;
  onValueChange?: (newValue: any) => void;
}

const ParamInput: React.FC<ParamInputProps> = ({
  paramString,
  previousValue,
  unit,
  onValueChange,
}) => {
  const listScheduling = ["FIFO", "LIFO", "SPT", "LPT"];
  const listArrows = ["↑", "↓", "←", "→"];
  const listDirections = ["0,1", "0,-1", "-1,0", "1,0"];

  const [value, setValue] = useState<string | boolean | number[] | number>(
    () => {
      if (typeof previousValue === "boolean") {
        return previousValue;
      }
      return Array.isArray(previousValue)
        ? previousValue.join(",") // Use comma-separated string for arrays
        : String(previousValue);
    }
  );

  useEffect(() => {
    // Update the value if previousValue changes externally
    if (typeof previousValue === "boolean") {
      setValue(previousValue);
    } else {
      setValue(
        Array.isArray(previousValue)
          ? previousValue.join(",")
          : String(previousValue)
      );
    }
  }, [previousValue]);

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.type === "checkbox") {
      console.log("event.target.checked", event.target.checked);
      const checked = event.target.checked;
      setValue(checked);
      if (onValueChange) {
        onValueChange(checked);
      }
    } else {
      setValue(event.target.value);
    }
  };

  const handleDirectionChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = event.target.value; // e.g., "0,1"
    const directionArray = selectedValue.split(",").map(Number);
    setValue(selectedValue);
    if (onValueChange) {
      onValueChange(directionArray);
    }
  };

  const handleSchedulingChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const selectedValue = event.target.value;
    console.log("new value is ", selectedValue);
    setValue(selectedValue);
    if (onValueChange) {
      onValueChange(selectedValue);
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter") {
      event.preventDefault();
      if (onValueChange) {
        // Attempt to parse as number, else keep as string
        const parsedValue = isNaN(Number(value)) ? value : Number(value);
        onValueChange(parsedValue);
      }
    }
  };

  const handleBlur = () => {
    if (onValueChange) {
      const parsedValue = isNaN(Number(value)) ? value : Number(value);
      onValueChange(parsedValue);
    }
  };
  // TODO make a function for nbOfBeams, where it changes all the other value's length, same for nbInConveyors and nbOutConveyors
  // TODO change display so it uses columns, with appropriate heights, it will make the display more elegant and readable
  // TODO make the save button always visible
  return (
    <label className="w-full md:w-full self-end">
      {paramString && (
        <div className="label pb-1 pt-0 leading-5">
          <span>
            {paramString === "accel"
              ? "Acceleration"
              : paramString === "speed"
              ? "Speed"
              : paramString}
            {unit &&
              unit !== "bool" &&
              unit !== "direction" &&
              unit !== "scheduling" && (
                <>
                  {" "}
                  [
                  {(() => {
                    const match = unit.match(/\^(\d+)/);
                    if (match) {
                      const exp = match[1];
                      const baseUnit = unit.replace(`^${exp}`, "");
                      return (
                        <>
                          {baseUnit}
                          <sup>{exp}</sup>
                        </>
                      );
                    }
                    return unit;
                  })()}
                  ]
                </>
              )}{" "}
            :
          </span>
        </div>
      )}
      {(() => {
        switch (unit) {
          case "bool":
            return (
              <input
                type="checkbox"
                value="boolean"
                checked={typeof value === "boolean" ? value : false}
                onChange={handleChange}
                className="checkbox mx-2"
              />
            );
          case "direction":
            return (
              <DropDownList
                value={value}
                listString={listArrows}
                listStringValues={listDirections}
                onChange={handleDirectionChange}
              />
            );
          case "scheduling":
            return (
              <DropDownList
                value={value}
                listString={listScheduling}
                listStringValues={listScheduling}
                onChange={handleSchedulingChange}
              />
            );
          default:
            return (
              <input
                type="number"
                step={paramString == "timeStep" ? "0.01" : 1} // Set the step to 0.01
                value={Number(value)}
                onChange={handleChange}
                onKeyDown={handleKeyDown}
                onBlur={handleBlur}
                className="input input-bordered w-full justify-center max-w-xs"
                onWheel={(e) => e.currentTarget.blur()} // Disable scrolling for changing the value
              />
            );
        }
      })()}
    </label>
  );
};

export default ParamInput;
