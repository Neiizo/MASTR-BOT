import React from "react";

const idToStatus = (id: number) => {
  switch (id) {
    case 2:
      return "SKIPPED";
    case 20:
      return "CAN_PICK";
    case 21:
      return "PICKING";
    case 22:
      return "CAN_PLACE";
    case 23:
      return "PLACING";
    case 24:
      return "DONE_PLACING";
    case 25:
      return "WAIT_CONVEYOR";
    case 30:
      return "IDLE";
    case 31:
      return "TRAVELING";
    case 32:
      return "SKIP_N_WAIT";
    case 33:
      return "DROPPED";
    case 34:
      return "WAITING";
    case 35:
      return "Z_MVMT";
    default:
      return `UNKNOWN ${id}`;
  }
};

export default idToStatus;
