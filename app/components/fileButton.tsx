"use client";
import React from "react";

interface fileButtonProps {
  text: string;
  onClick: () => void;
  btnType?: string;
}

const fileButton = ({
  text,
  onClick,
  btnType = "btn-primary",
}: fileButtonProps) => {
  return (
    <button className={`btn ${btnType}`} onClick={onClick}>
      {text}
    </button>
  );
};

export default fileButton;
