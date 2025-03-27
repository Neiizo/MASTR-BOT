"use client";
import ErrorAlert from "./components/ErrorAlert";
import React, { useState, MouseEvent, useEffect, ChangeEvent } from "react";

import FileButton from "./components/fileButton";
import MapInput from "./components/mapInput";
import BtnMenu from "./components/btnMenu";
import { loadFile } from "./components/lib/loadFile";
import {
  saveMap,
  deleteMap,
  fetchMapNames,
} from "./components/lib/jsonHandling";
import DataBox from "./components/Package";
import SaveTextInput from "./components/saveTextInput";

import { library } from "@fortawesome/fontawesome-svg-core";
import { faArrows } from "@fortawesome/free-solid-svg-icons";

library.add(faArrows);

interface Point {
  x: number;
  y: number;
  color: string;
}

interface DataPackages {
  points: Point[]; // list of targets
  outline: Point[]; // list of points defining the contour/shape of the map
}

export default function App() {
  const [dataPackages, setDataPackages] = useState<DataPackages>({
    points: [],
    outline: [],
  });

  // const [dataPackages, DataPackages] = useState<Data | null>(null);
  const [fileName, setFileName] = useState<string>("map.json");
  const [existingMaps, setExistingMaps] = useState<string[]>([]);
  const [newFileName, setNewFileName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [showAlert, setShowAlert] = useState<boolean>(false);
  const [alertText, setAlertText] = useState<string>("");

  const updateData = (field: string, value: Point[]) => {
    setDataPackages((prevData) => ({
      ...prevData,
      [field]: value,
    }));
  };

  const disableMap = () => {
    setDataPackages(() => ({
      points: [],
      outline: [],
    }));
    setFileName("");
  };

  const handleFileInput = (event: any) => {
    const newFile = event.target.files?.[0];
    if (!newFile) {
      setAlertText("No file selected.");
      setShowAlert(true);
      disableMap();
      return;
    }

    setFileName(newFile.name);
    const reader = new FileReader();

    reader.onload = (e) => {
      const content = e.target?.result;

      if (typeof content === "string") {
        try {
          const parsedData: DataPackages = JSON.parse(content);
          setDataPackages(parsedData);
          setAlertText("");
        } catch (err) {
          setAlertText("Invalid JSON file.");
          setShowAlert(true);
          disableMap();
        }
      } else {
        setAlertText("Unable to read file.");
        setShowAlert(true);
        disableMap();
      }
    };

    reader.onerror = () => {
      setAlertText("Error reading file.");
      setShowAlert(true);
      disableMap();
    };

    reader.readAsText(newFile);
  };

  const handleStartClick = () => {
    // Start the python code
    if (!fileName) {
      setShowAlert(true);
      setAlertText("You must select a package's configuration first !");
      return;
    }
    console.log("Starting python code...");
  };

  const handleCloseAlert = () => {
    setShowAlert(false);
    setAlertText("Unexpected behavior regarding the alert's text.");
  };

  const handleFetchClick = () => {
    fetchMapNames({ setNames: setExistingMaps });
  };

  const handleNewFileNameChange = (event: ChangeEvent<HTMLInputElement>) => {
    setNewFileName(event.target.value);
  };

  const handleSaveClick = () => {
    if (!fileName) {
      setShowAlert(true);
      setAlertText("You must select a package's configuration first !");
      return;
    }
    if (!newFileName) {
      setShowAlert(true);
      setAlertText("You must provide a file name first !");
      return;
    }
    if (newFileName.includes(".")) {
      setNewFileName(newFileName.split(".")[0]);
      setShowAlert(true);
      setAlertText(
        "The file's extension was removed. File is automatically saved to .json format."
      );
    }
    // save current localData from packages.tsx
    saveMap({
      fileName: newFileName,
      data: dataPackages,
      setMap: setExistingMaps,
    });
  };

  const handleDeleteClick = async () => {
    // delete the file
    deleteMap(fileName);
    fetchMapNames({ setNames: setExistingMaps }); // faire mieux, refaire la liste plutot
  };

  const onChangeMapSelection = async (
    event: React.ChangeEvent<HTMLSelectElement>
  ) => {
    // const button = event.target
    const selectedFileName = event.target.value;
    if (!selectedFileName) {
      setAlertText("Invalid file name.");
      return;
    }
    setFileName(selectedFileName);
    await loadMap(selectedFileName); // Pass the filename directly
  };

  const loadMap = async (selectedFileName: string) => {
    try {
      const loadedFile = (await loadFile(
        selectedFileName,
        "map"
      )) as DataPackages;
      console.log("loadedFile", loadedFile);
      setDataPackages(loadedFile);
      setAlertText("");
    } catch (err) {
      console.error("Error loading file:", err);
      setAlertText("Error loading file.");
      disableMap();
    }
  };

  useEffect(() => {
    fetchMapNames({ setNames: setExistingMaps });
    if (fileName) {
      loadMap(fileName);
    }
  }, []);
  // todo make alert show on the side of the screen instead of the top, it would be cleaner

  return (
    <div className="mx-auto w-[90%] mt-2">
      {/* Applies to the whole page */}
      {showAlert && (
        <ErrorAlert alertText={alertText} onClose={handleCloseAlert} />
      )}
      <div className=" flex space-x-10">
        <div className="flex flex-wrap flex-col gap-2 md:w-2/5 mt-10">
          <MapInput onChange={handleFileInput} className="" />
          <BtnMenu
            options={existingMaps}
            btnString="Select an existing configuration file."
            onChange={onChangeMapSelection}
            className=""
          />
          <div className="flex flex-wrap flex-row flex-initial gap-1 my-10">
            <FileButton
              text="Fetch"
              onClick={handleFetchClick}
              btnType="btn-primary px-7"
            />
            <FileButton
              text="Delete configuration"
              onClick={handleDeleteClick}
              btnType={`btn px-7 ${
                dataPackages ? " btn-primary" : " btn-disable "
              }`}
            />
            <div className="flex flex-row items-end">
              <SaveTextInput onChange={handleNewFileNameChange} />
              <FileButton text="Save" onClick={handleSaveClick} />
            </div>
          </div>
          <FileButton text="Start python script" onClick={handleStartClick} />
        </div>
        <div className="w-1/2 h-[37.7rem]">
          {/* Display error message if any */}
          {error && <p className="text-red-500">{error}</p>}

          <DataBox
            mapName={fileName}
            data={dataPackages}
            setData={updateData}
            setShowAlert={setShowAlert} // add a way to integrate the alert
            setAlertText={setAlertText} // add a way to integrate text from the call
          />
        </div>
      </div>
    </div>
  );
}
