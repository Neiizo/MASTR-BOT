"use client";
import React, { ChangeEvent, MouseEvent } from "react";

interface MapInputProps {
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
  className?: string;
}

const mapInput = ({ onChange, className }: MapInputProps) => {
  return (
    <div>
      <p className={`text-gray-700 mb-2 ${className}`}>
        Select the file describing the package's configuration. <br />
        It must be a JSON-filetype.
      </p>
      <input
        type="file"
        accept=".json"
        className="file-input file-input-bordered w-full max-w-xs file-input-sm"
        onChange={(e) => onChange(e)}
      />
    </div>
  );
};

export default mapInput;
