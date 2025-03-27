"use server";
import path from "path";
import { promises as fs } from "fs";

export async function loadFile(fileName: string, type: string) {
  var filePath: string = "";
  if (type === "map") {
    filePath = path.join(process.cwd(), "pages", "api", "maps", fileName);
  } else if (type === "settings") {
    filePath = path.join(process.cwd(), "pages", "api", fileName);
  } else {
    console.error("Invalid type provided");
    return;
  }
  console.log("Loading file from", filePath);
  const file = await fs.readFile(filePath, "utf-8");
  const data = JSON.parse(file);
  return data;
}
export default loadFile;
