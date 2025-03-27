// components/ParamArrayInput.tsx
"use client";
import React from "react";
import ParamInput from "./ParamInput";
import { useData } from "../context/DataContext";

interface ParamArrayInputProps {
  objType?: string;
  paramString: string;
  previousValue: number[];
  unit: string;
  onValueChange?: (newValue: number[]) => void;
}

const ParamArrayInput: React.FC<ParamArrayInputProps> = ({
  objType,
  paramString,
  previousValue,
  unit,
  onValueChange,
}) => {
  const { data, setData } = useData();
  const handleChange = (index: number, newValue: number | number[]) => {
    if (onValueChange) {
      if (typeof newValue === "number" || typeof newValue === "string") {
        const updatedArray = [...previousValue];
        updatedArray[index] = newValue;
        onValueChange(updatedArray);
      } else if (Array.isArray(newValue)) {
        onValueChange(newValue);
      }
    }
  };

  const coords: string[] = ["x", "y", "z"];
  return (
    <div className="w-full self-end ">
      <div className="label pb-1 pt-0 leading-5">
        <span>
          {paramString === "accel"
            ? "Acceleration"
            : paramString === "speed"
            ? "Speed"
            : paramString === "length"
            ? "Length"
            : paramString === "width"
            ? "Width"
            : paramString}
          {unit && unit !== "direction" && unit !== "scheduling" && (
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
          )}
          :
        </span>
      </div>
      {(() => {
        var unitTemp = "";
        var length = 0;
        var pString: Array<string> = [];
        switch (unit) {
          case "direction":
            return (
              <ParamInput
                key={paramString}
                paramString="" // changer ici
                previousValue={previousValue}
                unit={unit}
                onValueChange={(newVal) => handleChange(0, newVal)}
              />
            );
          case "scheduling":
            unitTemp = unit;
            break;
          default:
            break;
        }
        if (paramString === "workspaceSide" || paramString === "scheduling") {
          if (paramString === "scheduling") {
            length = data.beam.nbOfBeams;
            // length = data.beam.nbOfBeams * 2 ;
          } else {
            length = data.beam.nbOfBeams;
          }
          pString = Array.from({ length: length }, (_, idx) =>
            String(`Beam ${idx + 1}`)
          );
        } else if (
          paramString === "inWidth" ||
          paramString === "inItemsPerRow" ||
          paramString === "outWidth" ||
          paramString === "outItemsPerRow"
        ) {
          length = data.conveyor.nbInConveyor;
          pString = Array.from({ length: length }, (_, idx) =>
            String(`Conveyor ${idx + 1}`)
          );
        } else if (
          (paramString === "speed" || paramString === "accel") &&
          objType === "Conveyor"
        ) {
          length = previousValue.length;
          pString = ["In flow", "Out flow"];
        } else {
          length = previousValue.length;
          pString = coords;
        }
        var nbCols = Math.min(3, previousValue.length);
        return (
          <div className={`grid grid-cols-${nbCols} gap-1`}>
            {Array.from({ length: length }, (_, idx) => (
              <ParamInput
                key={`${paramString}-${idx}`}
                paramString={pString[idx]}
                previousValue={previousValue[idx] || 0}
                unit={unitTemp}
                onValueChange={(newVal) => handleChange(idx, newVal)}
              />
            ))}
          </div>
        );
      })()}
    </div>
  );
};

export default ParamArrayInput;
