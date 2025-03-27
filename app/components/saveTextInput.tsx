import React, { ChangeEvent } from "react";

interface SaveTextInputProps {
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
}

const SaveTextInput = ({ onChange }: SaveTextInputProps) => {
  return (
    <label className="form-control w-full max-w-xs">
      <div className="label">
        <span className="label-text-alt -mb-1.5">
          Save current configuration as
        </span>
      </div>
      <input
        type="text"
        placeholder="Desired file name"
        className="input input-bordered w-full max-w-xs"
        onChange={onChange}
      />
    </label>
  );
};

export default SaveTextInput;
