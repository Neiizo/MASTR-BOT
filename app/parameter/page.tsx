// components/Parameter.tsx
"use client";
import React, { useState, useEffect } from "react";
import ParamInput from "../components/ParamInput";
import ParamArrayInput from "../components/ParamArrayInput";
import ParamNestedArrayInput from "../components/ParamNestedArrayInput";
import { useData } from "../context/DataContext";
import ErrorAlert from "../components/ErrorAlert";
import FileButton from "../components/fileButton";
import { saveSettings } from "../components/lib/jsonHandling";
import CreateRect from "../components/svgFunctions/createRect";
import prepRectList from "../components/svgFunctions/prepRectList";

interface Data {
  unit: Record<string, string>;
  conveyor: Record<string, any>;
  slider: Record<string, any>;
  beam: Record<string, any>;
  target: Record<string, any>;
  timeStep: number;
  duration: number;
  seed: number;
}
interface rectProp {
  xy: number[];
  rectSize: number[];
  fill: string;
  alpha: number;
  key: string;
}

const Parameter = () => {
  const { data, setData } = useData();
  const [showAlert, setShowAlert] = useState<boolean>(false);
  const [alertText, setAlertText] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [listRect, setListRect] = useState<rectProp[]>([]);
  const [scaling, setScaling] = useState<number>();
  const [inputFlowRate, setInputFlowRate] = useState<number>(0);
  const [outputFlowRate, setOutputFlowRate] = useState<number>(0);
  const [saveName, setSaveName] = useState<string>("");

  const xyOffset = [100, 20];
  const handleCloseAlert = () => {
    setShowAlert(false);
    setAlertText("Unexpected behavior regarding the alert's text.");
  };

  const handleParamChange = (
    category: keyof Omit<Data, "timeStep" | "duration" | "seed">,
    key: string,
    newValue: any
  ) => {
    setData((prevData: Data | null) => {
      if (!prevData) return prevData;
      return {
        ...prevData,
        [category]: {
          ...prevData[category],
          [key]: newValue,
        },
      };
    });
  };

  const handleSpecificChange = (newValue: any, key: string) => {
    setData((prevData: Data | null) => {
      if (!prevData) return prevData;
      return {
        ...prevData,
        [key]: newValue,
      };
    });
  };

  const handleSaveClick = () => {
    if (!data) {
      setShowAlert(true);
      setAlertText("No data to save.");
      return;
    }
    // save current localData from packages.tsx
    saveSettings(data);
    console.log("Data saved", data);
  };

  const handleScript = async () => {
    setIsLoading(true);
    let string =
      "python script/main.py -save_hist -single_run -no_csv -pre_move -state_bouncing";
    if (data.seed >= 0) {
      string += ` -seed ${data.seed}`;
    }
    if (saveName !== "") {
      string += ` -name ${saveName}`;
    }
    console.log("Running Python script with args:", string);
    try {
      const response = await fetch("http://localhost:5000/run-python-script", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ args: string.split(" ") }),
      });

      if (!response.ok) {
        setIsLoading(false);
        throw new Error("Network response was not ok");
      }

      const result = await response.json();
      console.log("stdout:", result.stdout);
      console.log("stderr:", result.stderr);
      console.log("returncode:", result.returncode);
      setIsLoading(false);
    } catch (error) {
      console.error("Error running Python script:", error);
    }
  };

  // Helper function to determine the type of a parameter
  const getParamType = (value: any): "number" | "array" | "nestedArray" => {
    if (typeof value === "number") return "number";
    if (Array.isArray(value)) {
      if (value.length === 0) return "array"; // Default to array
      if (typeof value[0] === "number" || typeof value[0] === "string")
        return "array";
      if (Array.isArray(value[0])) return "nestedArray";
    }
    return "number"; // Default fallback
  };

  useEffect(() => {
    // Create the list of rectangles
    if (data) {
      prepRectList({
        setListRect,
        setScaling,
        params: data,
        xyOffset,
        divID: "small-SVG",
      });
      var inputFlowRate, outputFlowRate;
      var nbInItemsPerRows = 0;
      var nbOutItemsPerRows = 0;
      for (var i = 0; i < data.conveyor.nbInConveyor; i++) {
        nbInItemsPerRows += data.conveyor.inItemsPerRow[i];
      }
      for (var i = 0; i < data.conveyor.nbOutConveyor; i++) {
        nbOutItemsPerRows += data.conveyor.outItemsPerRow[i];
      }
      inputFlowRate =
        (data.conveyor.speed[0] / data.conveyor.inRowSpacing) *
        nbInItemsPerRows *
        (1 - data.conveyor.badProductRatio) *
        60;
      outputFlowRate =
        (data.conveyor.speed[1] /
          (data.conveyor.nPackagesRow * data.conveyor.packagesRowSpacing +
            data.conveyor.packagesExtraSpacing)) *
        nbOutItemsPerRows *
        data.conveyor.nPackagesRow *
        60;
      setInputFlowRate(inputFlowRate);
      setOutputFlowRate(outputFlowRate);
    }
  }, [data]);

  // todo add preview svg of the configuration
  // Note maybe it is better to hard code each parameter in JS, instead of loadJson.py
  return (
    <div className="mx-auto w-full mt-2">
      {showAlert && (
        <ErrorAlert alertText={alertText} onClose={handleCloseAlert} />
      )}
      <div className="fixed right-4 top-14 space-y-5 w-[17%]">
        <div>Preview:</div>
        <div className="w-[20em] card border" id="small-SVG">
          <svg>
            {listRect.map((val: rectProp) => (
              <React.Fragment key={val.key}>
                <CreateRect rect={val} scaling={scaling!} xyOffset={xyOffset} />
              </React.Fragment>
            ))}
          </svg>
        </div>
        <div>
          <p>Input flow rate: {inputFlowRate.toFixed(3)} pick/min</p>
          <p>Output flow rate: {outputFlowRate.toFixed(3)} pick/min</p>
        </div>
        <div className="card border flex w-40 p-3 space-y-1 place-self-end">
          <FileButton
            text="Save settings"
            onClick={handleSaveClick}
            btnType="btn-primary w-full"
          />
          <div className="divider" />
          <input
            type="test"
            placeholder="Enter a name"
            onChange={(e) => setSaveName(e.target.value)}
            className="input input-bordered w-full max-w-xs"
          />
          <button
            className="btn btn-primary w-full"
            onClick={handleScript}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading loading-dots loading-xs" />
            ) : (
              "Start python script"
            )}
          </button>
        </div>
      </div>
      <div className="py-5">
        <div className="card border p-4 md:w-[95%] lg:w-[95%]">
          <h1 className="pt-2 px-2 text-2xl font-bold">
            <u>Parameter configuration</u>
          </h1>
          {/* Handle timeStep separately */}
          {data && (
            <div className="mt-4 card border p-5 bg-slate-50">
              <h2 className="text-lg font-semibold">
                <u>General</u>
              </h2>
              <div className="grid grid-cols-3 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-2 content-evenly">
                <ParamInput
                  paramString="timeStep"
                  previousValue={data.timeStep}
                  unit="s"
                  onValueChange={(newVal) =>
                    handleSpecificChange(newVal, "timeStep")
                  }
                />
                <ParamInput
                  paramString="Simulation's duration"
                  previousValue={data.duration}
                  unit="s"
                  onValueChange={(newVal) =>
                    handleSpecificChange(newVal, "duration")
                  }
                />
                <ParamInput
                  paramString="Seed (-1 for random seed)"
                  previousValue={data.seed}
                  unit=""
                  onValueChange={(newVal) =>
                    handleSpecificChange(newVal, "seed")
                  }
                />
              </div>
            </div>
          )}

          {/* Iterate over each category except timeStep */}
          {data &&
            (Object.keys(data) as Array<keyof Data>).map((category) => {
              if (
                category === "timeStep" ||
                category === "duration" ||
                category === "unit" ||
                category === "seed"
              )
                return null; // Already handled
              const params = data[category] as Record<string, any>;
              return (
                <div
                  key={category}
                  className="mt-6 card border p-4 bg-slate-50"
                >
                  <h2 className="text-lg font-semibold capitalize">
                    <u>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </u>
                  </h2>
                  <div
                    className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 mt-2 "
                    key={`${category}-1000`}
                  >
                    {Object.entries(params).map(([key, value]) => {
                      const type = getParamType(value);
                      switch (type) {
                        case "number":
                          return (
                            <div
                              className="card border bg-slate-100 p-3"
                              key={`${category}-${key}`}
                            >
                              <ParamInput
                                paramString={key}
                                previousValue={value}
                                unit={data.unit[key]}
                                onValueChange={(newVal) =>
                                  handleParamChange(category, key, newVal)
                                }
                              />
                            </div>
                          );
                        case "array":
                          return (
                            <div
                              className="card border bg-slate-100 p-3"
                              key={`${category}-${key}`}
                            >
                              <ParamArrayInput
                                objType={
                                  category.toLowerCase() === "conveyor"
                                    ? "Conveyor"
                                    : undefined
                                }
                                paramString={key}
                                previousValue={value}
                                unit={data.unit[key]}
                                onValueChange={(newVal) =>
                                  handleParamChange(category, key, newVal)
                                }
                              />
                            </div>
                          );
                        case "nestedArray":
                          return (
                            <div
                              className="card border bg-slate-100 p-3"
                              key={`${category}-${key}`}
                            >
                              <ParamNestedArrayInput
                                paramString={key}
                                previousValue={value}
                                unit={data.unit[key]}
                                onValueChange={(newVal) =>
                                  handleParamChange(category, key, newVal)
                                }
                              />
                            </div>
                          );
                        default:
                          return (
                            <div
                              className="card border bg-slate-200 p-3"
                              key={`${category}-${key}`}
                            >
                              <ParamInput
                                paramString={key}
                                previousValue={value}
                                unit={data.unit[key]}
                                onValueChange={(newVal) =>
                                  handleParamChange(category, key, newVal)
                                }
                              />
                            </div>
                          );
                      }
                    })}
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};

export default Parameter;
