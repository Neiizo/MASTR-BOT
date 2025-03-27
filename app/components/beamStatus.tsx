import React from "react";
import idToStatus from "./lib/idToStatus";

interface beamStatusProps {
  beams: Record<string, any>;
  className: string;
}


const BeamStatus = ({ beams, className }: beamStatusProps) => {
  return (
    <div className={` ${className}`}>
      <div className="collapse collapse-arrow">
        <input type="checkbox" />
        <div className="collapse-title text-xl font-medium">
          <u>Rail status : </u>
        </div>
        <div className="collapse-content">
          {beams.map((status: number, idx: number) => (
            <div key={idx} className="flex items-center">
              <div
                className={`w-4 h-4 rounded-full mr-2 ${
                  status == 20 || status === 22
                    ? "bg-green-500"
                    : status === 2
                    ? "bg-orange-200"
                    : status === 32
                    ? "bg-yellow-600"
                    : status === 21 || status === 23
                    ? "bg-blue-500"
                    : "bg-red-500"
                }`}
              ></div>
              <div>
                Rail n°{idx}'s : {idToStatus(status)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BeamStatus;
