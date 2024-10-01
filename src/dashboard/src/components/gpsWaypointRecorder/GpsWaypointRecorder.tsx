import { Button, Input, Space, notification } from "antd";
import { useState } from "react";
import { GPSMessage } from "../navigation/Navigation";

type csvDataPointType = string | number;
type waypointDataType = {
  [key: string]: csvDataPointType[]; // Each key maps to an array
};

// Stores the values waiting to be put into the csv file
const waypointData: waypointDataType = {
  latitude: [],
  longitude: [],
  comment: [],
};

export default function GpsWaypointRecorder(props: { message: GPSMessage }) {
  // Note: does not account for different array sizes, may cause issues if the csv array is somehow modified externally
  const [comment, setComment] = useState<string>("");

  const csvHandler = (data: waypointDataType): string => {
    const csvRows: string[] = [];

    // Extract the headers
    const headers = Object.keys(data);
    csvRows.push(headers.join(","));

    // Check if any of the arrays are non-empty and return only header if empty
    const nonEmptyArrays = headers.filter((header) => data[header].length > 0);
    if (nonEmptyArrays.length === 0) {
      return csvRows.join("\n");
    }

    const numRows = data[nonEmptyArrays[0]].length;
    for (let i = 0; i < numRows; i++) {
      const rowValues = headers.map((header) => data[header][i] || ""); // Handle potential undefined values
      csvRows.push(rowValues.join(","));
    }

    return csvRows.join("\n");
  };

  // Downloads the csv file
  const csvDownloader = (data: waypointDataType) => {
    const csv = csvHandler(data);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);

    // Makes a new anchor and clicks it
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "waypoints.csv";
    notification.success({
      message: "Download Started",
    });
    anchor.click();
  };

  // Recording the values by simply pushing them into the array
  function recordHandler(waypoint: GPSMessage): void {
    waypointData.comment.push(comment);
    waypointData.latitude.push(waypoint.latitude);
    waypointData.longitude.push(waypoint.longitude);
    notification.success({
      message: "Successfully recorded waypoint",
    });
    setComment("");
  }

  return (
    <Space>
      <Input
        placeholder="Waypoint Comment"
        value={comment}
        onChange={(event) => {
          setComment(event.target.value);
        }}
      />

      <Button onClick={() => recordHandler(props.message)}>
        Record Waypoint
      </Button>
      <Button
        type="primary"
        htmlType="submit"
        onClick={() => csvDownloader(waypointData)}
      >
        Download
      </Button>
    </Space>
  );
}
