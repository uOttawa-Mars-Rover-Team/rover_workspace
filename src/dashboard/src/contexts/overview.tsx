import React, { createContext, useContext } from "react";

import { useLocalStorage } from "../hooks";
import * as config from "../dashboardConfig.json";
import { RosContext } from "./ros";

interface CameraFeed {
  title: string;
  topicName: string;
  messageType: string;
}

interface AutoRefresh {
  nodes: boolean;
  params: boolean;
  services: boolean;
  topics: boolean;
}

interface ContextType {
  cameraFeeds: CameraFeed[];
  autoRefresh: AutoRefresh;
  dashboardConfig: () => any;
  addCameraFeed: (cameraFeed: CameraFeed) => void;
  removeCameraFeed: (index: number) => void;
  editCameraFeed: (cameraFeed: CameraFeed, index: number) => void;
}

const defaultValue: ContextType = {
  cameraFeeds: config.overview.cameraFeeds,
  autoRefresh: config.overview.autoRefresh,
  dashboardConfig: () => {},
  addCameraFeed: () => {},
  removeCameraFeed: () => {},
  editCameraFeed: () => {},
};

/**
 * React Context containing overview page data
 */
export const OverviewContext = createContext(defaultValue);

const OverviewProvider: React.FC = ({ children }) => {
  const [cameraFeeds, setCameraFeeds] = useLocalStorage(
    "cameraFeeds",
    defaultValue.cameraFeeds
  );
  const [autoRefresh] = useLocalStorage(
    "autoRefresh",
    defaultValue.autoRefresh
  );

  const { url }= useContext(RosContext);

  const dashboardConfig = () =>
    encodeURIComponent(
      JSON.stringify(
        {
          url,
          overview: {
            cameraFeeds,
            autoRefresh,
            autoRefreshFrequency: config.overview.autoRefreshFrequency,
          },
        },
        null,
        2
      )
    );

  const addCameraFeed = (cameraFeed: CameraFeed) => {
    setCameraFeeds((prev) => [...prev, cameraFeed]);
  };

  const removeCameraFeed = (index: number) => {
    setCameraFeeds((prev) => prev.filter((_, i) => i !== index));
  };

  const editCameraFeed = (cameraFeed: CameraFeed, index: number) => {
    setCameraFeeds((prev) =>
      prev.map((value, i) => (i === index ? cameraFeed : value))
    );
  };

  return (
    <OverviewContext.Provider
      value={{
        cameraFeeds,
        autoRefresh,
        dashboardConfig,
        addCameraFeed,
        removeCameraFeed,
        editCameraFeed,
      }}
    >
      {children}
    </OverviewContext.Provider>
  );
};

export default OverviewProvider;
