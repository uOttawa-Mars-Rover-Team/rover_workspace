import { createContext, useEffect, useState } from "react";
import { notification } from "antd";
import { Ros } from "roslib";

import { useLocalStorage } from "../hooks";
import * as config from "../dashboardConfig.json";

interface ContextType {
  url: string;
  rosClient?: Ros;
  connected: boolean;
  error: boolean;
  setUrl: React.Dispatch<React.SetStateAction<string>>;
  connect: () => void;
  disconnect: () => void;
}

const defaultValue: ContextType = {
  url: config.url,
  rosClient: undefined,
  connected: false,
  error: false,
  setUrl: () => {},
  connect: () => {},
  disconnect: () => {},
};

/**
 * React Context containing ROS related data
 */
export const RosContext = createContext(defaultValue);

type RosProviderProps = {
  children: React.ReactNode;
};

const RosProvider: React.FC<RosProviderProps> = ({ children }) => {
  const [url, setUrl] = useLocalStorage("url", defaultValue.url);
  const [rosClient, setRosClient] = useState(defaultValue.rosClient);
  const [connected, setConnected] = useState(defaultValue.connected);
  const [error, setError] = useState(defaultValue.error);

  const connect = () => {
    if (url) {
      try {
        setRosClient(new Ros({ url }));
      } catch (e) {
        notification.error({
          message: "Error connecting to ROS",
          description: `Cannot establish a connection at ${url}. Make sure the URL is correct. Is ROS and the webserver running?`,
        });
      }
    }
  };

  const disconnect = () => {
    if (rosClient) {
      rosClient.close();
    }
  };

  useEffect(() => {
    if (rosClient) {
      rosClient.on("error", () => {
        setError(true);
        notification.error({
          message: "Error connecting to ROS",
          description: `Cannot establish a connection at ${url}. Make sure the URL is correct. Is ROS and the webserver running?`,
        });
      });

      rosClient.on("connection", () => {
        setConnected(true);
        setError(false);
        notification.success({
          message: "Connected to ROS",
          description: `Established a websocket connection at ${url}.`,
        });
      });

      rosClient.on("close", () => {
        setConnected(false);
        notification.info({ message: "Disconnected from ROS" });
      });
    }
  }, [rosClient, url]);

  return (
    <RosContext.Provider
      value={{ url, rosClient, connected, error, setUrl, connect, disconnect }}
    >
      {children}
    </RosContext.Provider>
  );
};

export default RosProvider;
