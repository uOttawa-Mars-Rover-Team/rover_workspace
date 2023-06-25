import { useContext, useEffect, useState } from "react";
import isEqual from "react-fast-compare";
import dayjs from "dayjs";

import { RosContext } from "../contexts";
import * as config from "../dashboardConfig.json";
import { getNode } from "../utils/ros";

export interface Node {
  name: string;
  publishing: string[];
  subscribing: string[];
  services: string[];
}

/**
 * React Hook wrapper on ROSLIB Node
 * 
 * @param shouldRefresh Specify if nodes should periodically get refreshed
 * @returns ROS nodes and time of last refresh
 */
export const useNodes = (shouldRefresh: boolean) => {
  const { rosClient } = useContext(RosContext);
  const [rosNodes, setRosNodes] = useState<Node[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState("");

  useEffect(() => {
    let id = setInterval(() => {
      rosClient?.getNodes(async (nodes) => {
        const newRosNodesPromises = nodes.map((node) =>
          getNode(rosClient, node)
        );
        let newRosNodes = await Promise.all(newRosNodesPromises);

        if (!isEqual(rosNodes, newRosNodes)) {
          setRosNodes(newRosNodes);
        }

        console.log(newRosNodes);

        setLastRefreshed(dayjs().format("MMM D, YYYY h:mm:ss A"));
      });
    }, config.overview.autoRefreshFrequency);

    if (!shouldRefresh) {
      clearInterval(id);
    }

    return () => clearInterval(id);
  }, [shouldRefresh, rosClient, rosNodes]);

  return { nodes: rosNodes, lastRefreshed };
};
