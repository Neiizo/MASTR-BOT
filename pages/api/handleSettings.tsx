import type { NextApiRequest, NextApiResponse } from "next";
import fsPromises from "fs/promises";
import path from "path";

type ResponseData = {
  message: string;
  names?: string[];
  name?: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  const settingsDirectory = path.join(process.cwd(), "pages", "api");
  try {
    await fsPromises.mkdir(settingsDirectory, { recursive: true });
  } catch (dirErr) {
    console.error("Error creating maps directory:", dirErr);
    return res.status(500).json({ message: "Internal Server Error" });
  }
  if (req.method === "GET") {
    // console.log("GET settings request NOT programmed yet");
    try {
      // Read all files in the maps directory
      const histDirectory = path.join(process.cwd(), "pages", "api", "history");
      const files = await fsPromises.readdir(histDirectory);
      console.log(files);

      res.status(200).json({
        message: "Files retrieved successfully",
        names: files,
      });
    } catch (err) {
      console.error("Error reading hist directory:", err);
      res.status(500).json({ message: "Error reading hist directory" });
    }
  } else if (req.method === "POST") {
    const { fileName, data } = req.body;

    if (!fileName || !data) {
      return res
        .status(400)
        .json({ message: "fileName and data are required" });
    }

    // Write the updated data to the JSON file
    const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9-_]/g, "");
    if (!sanitizedFileName) {
      return res.status(400).json({ message: "Invalid fileName provided" });
    }
    const filePath = path.join(settingsDirectory, `${sanitizedFileName}.json`);

    try {
      // Convert the object back to a JSON string
      const jsonData = JSON.stringify(data, null, 4);
      await fsPromises.writeFile(filePath, jsonData, "utf-8");
      res
        .status(200)
        .json({ message: "Data stored successfully", name: sanitizedFileName });
    } catch (writeErr) {
      console.error("Error writing file:", writeErr);
      // Send a success response
      res.status(500).json({ message: "Error storing data" });
    }
  } else {
    res.setHeader("Allow", ["GET", "POST"]);
    res.status(405).json({ message: `Method ${req.method} Not Allowed` });
  }
}
