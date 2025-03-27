import React from "react";
import idToStatus from "./lib/idToStatus";

interface sliderStatusProps {
  sliders: Record<string, any>;
  className: string;
}


const SliderStatus = ({ sliders, className }: sliderStatusProps) => {
  return (
    <div className={` ${className}`}>
      <div className="collapse collapse-arrow">
        <input type="checkbox" />
        <div className="collapse-title text-xl font-medium">
          <u>Slider status : </u>
        </div>
        <div className="collapse-content">
          {sliders.map((status: number, idx: number) => (
            <div key={idx} className="flex items-center">
              <div
                className={`w-4 h-4 rounded-full mr-2 ${
                  status == 30
                    ? "bg-green-500"
                    : status === 2
                    ? "bg-orange-200"
                    : status === 32 || status === 34
                    ? "bg-yellow-600"
                    : status === 21 || status === 23
                    ? "bg-blue-500"
                    : "bg-red-500"
                }`}
              ></div>
              <div>
                Slider n°{idx}'s : {idToStatus(status)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SliderStatus;
