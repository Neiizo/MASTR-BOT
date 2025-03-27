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
  const mapsDirectory = path.join(process.cwd(), "pages", "api", "maps");
  try {
    await fsPromises.mkdir(mapsDirectory, { recursive: true });
  } catch (dirErr) {
    console.error("Error creating maps directory:", dirErr);
    return res.status(500).json({ message: "Internal Server Error" });
  }
  if (req.method === "GET") {
    try {
      // Read all files in the maps directory
      const files = await fsPromises.readdir(mapsDirectory);

      // Filter JSON files
      const jsonFiles = files.filter((file) => path.extname(file) === ".json");
      res.status(200).json({
        message: "Files retrieved successfully",
        names: jsonFiles,
      });
    } catch (err) {
      console.error("Error reading maps directory:", err);
      res.status(500).json({ message: "Error reading maps directory" });
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
    const filePath = path.join(mapsDirectory, `${sanitizedFileName}.json`);

    try {
      // Convert the object back to a JSON string
      const jsonData = JSON.stringify(data, null, 2);
      await fsPromises.writeFile(filePath, jsonData, "utf-8");
      res
        .status(200)
        .json({ message: "Data stored successfully", name: sanitizedFileName });
    } catch (writeErr) {
      console.error("Error writing file:", writeErr);
      // Send a success response
      res.status(500).json({ message: "Error storing data" });
    }
  } else if (req.method === "DELETE") {
    const { fileName } = req.body;

    if (!fileName) {
      return res.status(400).json({ message: "fileName is required" });
    }

    const sanitizedFileName = fileName.replace(/[^a-zA-Z0-9-_]/g, "");
    if (!sanitizedFileName) {
      return res.status(400).json({ message: "Invalid fileName provided" });
    }
    const filePath = path.join(mapsDirectory, `${sanitizedFileName}.json`);

    try {
      // Convert the object back to a JSON string
      await fsPromises.unlink(filePath);
      res
        .status(200)
        .json({ message: "Map successfully", name: sanitizedFileName });
    } catch (unlinkErr) {
      console.error("Error writing file:", unlinkErr);
      // Send a success response
      res.status(500).json({ message: "Error deleting map" });
    }
  } else {
    res.setHeader("Allow", ["GET", "POST", "DELETE"]);
    res.status(405).json({ message: `Method ${req.method} Not Allowed` });
  }
}
