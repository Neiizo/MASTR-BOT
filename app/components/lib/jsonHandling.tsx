interface settingsData {
  conveyor: Record<string, any>;
  slider: Record<string, any>;
  beam: Record<string, any>;
  target: Record<string, any>;
  timeStep: number;
}

interface Data {
  points: Point[];
}

interface Point {
  x: number;
  y: number;
  color: string;
}

interface FetchNamesProps {
  setNames: (names: string[]) => void;
}

interface SaveMapProps {
  fileName: string;
  data: Data;
  setMap: React.Dispatch<React.SetStateAction<string[]>>;
}

export const fetchMapNames = async ({ setNames }: FetchNamesProps) => {
  const response = await fetch("/api/handleMaps");
  const existingMaps = await response.json();
  console.log("Existing maps", existingMaps.names);
  setNames(existingMaps.names);
};

export const fetchHistNames = async (
  { setNames }: FetchNamesProps,
  additionnalName?: string
) => {
  const response = await fetch("/api/handleSettings");
  const existingMaps = await response.json();
  console.log("Existing histories", existingMaps.names);
  if (additionnalName) {
    setNames([additionnalName, ...existingMaps.names] as string[]);
  } else {
    setNames(existingMaps.names);
  }
};

export const saveMap = async ({ fileName, data, setMap }: SaveMapProps) => {
  const response = await fetch("/api/handleMaps", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fileName: fileName.replace(/\.json$/i, ""),
      data,
    }),
  });
  const postRes = await response.json();
  console.log(postRes);
  setMap((prevItems) => [...prevItems, `${postRes.name}.json`]);
};

export const saveSettings = async (data: settingsData) => {
  const response = await fetch("/api/handleSettings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fileName: "params",
      data,
    }),
  });
  const postRes = await response.json();
  console.log(postRes);
};

export const deleteMap = async (fileName: string) => {
  // delete the file
  const response = await fetch("/api/handleMaps", {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      fileName: fileName.replace(/\.json$/i, ""),
    }),
  });
  const deleteRes = await response.json();
  console.log(deleteRes);
};
