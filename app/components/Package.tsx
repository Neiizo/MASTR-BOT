// components/DataBox.tsx
"use client";
import React, { useState, ChangeEvent } from "react";
import Plotly from "react-plotly.js";
import { ColorButton, MoveButton } from "./mapButton";
import CoordInput from "./coordInput";
import FileButton from "./fileButton";

interface Point {
  x: number;
  y: number;
  color: string;
}

interface Data {
  points: Point[];
  outline: Point[];
}

interface PackageProps {
  mapName: string;
  data: Data;
  setData: (field: string, value: Point[]) => void;
  setShowAlert: React.Dispatch<React.SetStateAction<boolean>>;
  setAlertText: React.Dispatch<React.SetStateAction<string>>;
}

const DataBox = ({
  mapName,
  data,
  setData,
  setShowAlert,
  setAlertText,
}: PackageProps) => {
  // Local state to manage points
  const colorList: string[] = ["red", "blue", "green", "yellow", "purple"]; // change here if we move to colorCode
  const [currColor, setCurrColor] = useState<string>("");
  const [moveSelected, setMoveSelected] = useState<boolean>(false); // defines wether the move button is selected or not
  const [selectedPointID, setSelectedPointID] = useState<number | null>(null);

  const handleClickColor = (event: ChangeEvent<HTMLInputElement>) => {
    const colorName = event.currentTarget.value;
    setCurrColor(colorName); // change here if we move to colorCode
    setMoveSelected(false);
  };

  const handleClickMove = () => {
    console.log("Move button clicked!");
    setCurrColor("");
    setMoveSelected(true);
  };

  const handlePlotClick = (event: any) => {
    console.log("Plot clicked!");
    if (event.points && event.points.length > 0) {
      const clickedPoint = event.points[0];
      const pointIndex = clickedPoint.pointIndex; // Index in the data array

      setSelectedPointID(pointIndex);
      console.log(`Clicked point ID: ${pointIndex}`);

      if (currColor) {
        const updatedPoints: Point[] = data.points.map((point, index) => {
          if (index === pointIndex) {
            console.log("color", point.color, "using ", currColor);
            return {
              ...point,
              color: (point.color = currColor), // change here if we move to colorCode
            };
          }
          return point;
        });
        setData("points", updatedPoints);
      }
    }
  };

  const handleCoordChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newCoord = Number(event.target.value);

    if (selectedPointID !== null) {
      if (event.target.id == "x") {
        var newXVal = newCoord;
        var newYVal = data.points[selectedPointID].y;
      } else {
        var newXVal = data.points[selectedPointID].x;
        var newYVal = newCoord;
      }

      const updatedPoints: Point[] = data.points.map((point, index) => {
        if (index === selectedPointID) {
          return {
            ...point,
            x: (point.x = newXVal),
            y: (point.y = newYVal),
          };
        }
        return point;
      });
      setData("points", updatedPoints);
    }
  };

  const handleAddPoint = () => {
    const updatedPoints = data.points;
    updatedPoints.push({ x: 10, y: 10, color: "red" });
    setData("points", updatedPoints);
    setSelectedPointID(data.points.length - 1);
    return;
  };

  const handleDeletePoint = () => {
    if (selectedPointID === null) {
      setAlertText("You need to select a point to delete !");
      setShowAlert(true);
      return;
    }
    console.log("Deleting point...");

    const updatedPoints: Point[] = data.points.filter(
      (_, index) => index !== selectedPointID
    );
    setData("points", updatedPoints);
    setSelectedPointID(null);
  };

  // Format data to work with Plotly. Maybe change original data structure to fit Plotly's requirements?
  const plotData: Plotly.Data[] = [
    {
      x: data.points.map((point) => point.x),
      y: data.points.map((point) => point.y),
      mode: "markers",
      type: "scatter",
      name: "Targets",
      marker: {
        color: data.points.map((point) => point.color),
        size: 10,
      },
    },
    {
      x: data.outline.map((outlinePoint) => outlinePoint.x),
      y: data.outline.map((outlinePoint) => outlinePoint.y),
      mode: "lines",
      name: "Package",
    },
  ];

  // Plotly layout. Make it fixed, and try to make background transparent, to match the card's background
  const layout: Partial<Plotly.Layout> = {
    title: `Configuration from ${mapName}`,
    xaxis: {
      title: "X-axis",
      gridcolor: "#d3d3d3", // Light gray grid lines
      zerolinecolor: "#d3d3d3", // Color for the zero line
      tickfont: {
        color: "#333", // Tick labels color
      },
      fixedrange: true, // Disable zooming/panning on x-axis
      range: [0, 300],
      dtick: 50,
      ticklen: 5,
      autotick: false,
      scaleanchor: "y", // Anchor x-axis scaling to y-axis
      scaleratio: 1, // Maintain 1:1 scaling ratio
    },
    yaxis: {
      title: "Y-axis",
      gridcolor: "#d3d3d3", // Light gray grid lines
      zerolinecolor: "#d3d3d3", // Color for the zero line
      tickfont: {
        color: "#333", // Tick labels color
      },
      fixedrange: true, // Disable zooming/panning on y-axis
      range: [0, 300],
      dtick: 50,
      ticklen: 5,
      autotick: false,
    },
    plot_bgcolor: "rgba(0,0,0,0)", // Transparent plotting area
    paper_bgcolor: "rgba(0,0,0,0)", // Transparent paper area
    dragmode: false, // Disable drag interactions (zooming, panning)
    width: 500,
    height: 500,
    // autosize: true,
    margin: { l: 50, r: 50, t: 50, b: 50 },
    shapes:
      selectedPointID !== null
        ? [
            {
              type: "circle",
              xref: "x",
              yref: "y",
              x0: data.points[selectedPointID].x - 5, // Adjust radius as needed
              y0: data.points[selectedPointID].y - 5,
              x1: data.points[selectedPointID].x + 5,
              y1: data.points[selectedPointID].y + 5,
              line: {
                color: "black",
                width: 2,
              },
            },
          ]
        : [],
  };

  const config = {
    displayModeBar: false, // Remove the mode bar
    scrollZoom: false, // Disable zooming via scroll
    // editable: true, // Enable editing (e.g., dragging points)
  };

  return (
    <div className="card shadow-xl card-body bg-gray-50 h-full w-full">
      {data.points.length != 0 ? (
        <div className="flex flex-col">
          <div className="flex flex-grow">
            <div className="flex-grow">
              <Plotly
                data={plotData}
                layout={layout}
                onClick={handlePlotClick}
                config={config}
              />
            </div>
            <div className="flex flex-col h-full justify-center align-middle gap-2">
              {colorList.map((color) => (
                <ColorButton
                  colorName={color}
                  onChange={handleClickColor}
                  key={color}
                />
              ))}
              <MoveButton
                onChange={handleClickMove}
                selected={moveSelected}
                key="move"
              />
              <FileButton
                text="Add point"
                btnType="btn-outline w-20"
                onClick={handleAddPoint}
              />
              <FileButton
                text="Delete point"
                btnType="btn-outline w-20"
                onClick={handleDeletePoint}
              />
            </div>
          </div>
          <div className="flex justify-center items-center -ml-16 space-x-4">
            <CoordInput
              axis="x"
              coord={
                selectedPointID !== null
                  ? data.points[selectedPointID].x
                  : undefined
              }
              onChange={handleCoordChange}
            />
            <CoordInput
              axis="y"
              coord={
                selectedPointID !== null
                  ? data.points[selectedPointID].y
                  : undefined
              }
              onChange={handleCoordChange}
            />
          </div>
        </div>
      ) : (
        <p className="text-center align-middle text-red-500 mt-16">
          <b>
            No data to display. <br />
            Select a configuration's description on the left.
          </b>
        </p>
      )}
    </div>
  );
};

export default DataBox;
