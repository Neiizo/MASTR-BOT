"use client";
import React, {
  createContext,
  useState,
  useContext,
  ReactNode,
  useEffect,
} from "react";
import { loadFile } from "../components/lib/loadFile";

interface DataContextProps {
  data: any;
  setData: React.Dispatch<React.SetStateAction<any>>;
}
interface Data {
  unit: Record<string, string>;
  conveyor: Record<string, any>;
  slider: Record<string, any>;
  beam: Record<string, any>;
  target: Record<string, any>;
  timeStep: number;
  duration: number;
}
const DataContext = createContext<DataContextProps | undefined>(undefined);

export const DataProvider = ({ children }: { children: ReactNode }) => {
  const [data, setData] = useState<any>(null);

  const loadSettings = async () => {
    try {
      const loadedFile = (await loadFile("params.json", "settings")) as Data;
      console.log("loadedFile", loadedFile);
      setData(loadedFile);
      // setAlertText("");
    } catch (err) {
      console.error("Error loading file:", err);
      // setShowAlert(true);
      // setAlertText("Error loading file.");
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  return (
    <DataContext.Provider value={{ data, setData }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error("useData must be used within a DataProvider");
  }
  return context;
};
