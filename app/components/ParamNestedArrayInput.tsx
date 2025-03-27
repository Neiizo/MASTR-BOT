// components/ParamNestedArrayInput.tsx
"use client";
import React from "react";
import ParamArrayInput from "./ParamArrayInput";
import { useData } from "../context/DataContext";

interface ParamNestedArrayInputProps {
  paramString: string;
  previousValue: number[][];
  unit: string;
  onValueChange?: (newValue: number[][]) => void;
}

const ParamNestedArrayInput: React.FC<ParamNestedArrayInputProps> = ({
  paramString,
  previousValue,
  unit,
  onValueChange,
}) => {
  const { data } = useData();
  const handleChange = (index: number, newValue: number[]) => {
    if (onValueChange) {
      const updatedNestedArray = [...previousValue];
      updatedNestedArray[index] = newValue;
      onValueChange(updatedNestedArray);
      data;
    }
  };

  return (
    <div className="w-full self-end ">
      <div className="label pb-1 pt-0 leading-5">
        <span>
          {paramString} [{unit}] :
        </span>
      </div>
      {(() => {
        let length = 0;
        var pString: Array<string> = [];
        switch (paramString) {
          case "inEndPos":
            length = data.conveyor.nbInConveyor;
            pString = Array.from(
              { length: length },
              (_, idx) => `Conveyor ${idx + 1}`
            );
            break;
          case "outEndPos":
            length = data.conveyor.nbOutConveyor;
            pString = Array.from(
              { length: length },
              (_, idx) => `Conveyor ${idx + 1}`
            );
            break;
          default:
            length = previousValue.length;
            pString = Array.from(
              { length: length },
              (_, idx) => `Position ${idx + 1}`
            );
            break;
        }

        return (
          <div className="flex flex-col gap-2">
            {Array.from({ length: length }, (_, idx) => (
              <ParamArrayInput
                key={`${paramString}-${idx}`}
                paramString={pString[idx]}
                previousValue={previousValue[idx] || [0, 0]}
                unit=""
                onValueChange={(newVal) => handleChange(idx, newVal)}
              />
            ))}
          </div>
        );
      })()}
    </div>
  );
};

export default ParamNestedArrayInput;
