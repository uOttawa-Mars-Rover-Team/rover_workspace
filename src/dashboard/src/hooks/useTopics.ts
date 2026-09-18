import { useContext, useEffect, useState } from "react";
import isEqual from "react-fast-compare";
import dayjs from "dayjs";

import { RosContext } from "../contexts";
import * as config from "../dashboardConfig.json";

interface Topic {
  name: string;
  type: string;
}

/**
 * React Hook wrapper on ROSLIB Topics
 *
 * @param shouldRefresh Specify if topics should periodically get refreshed
 * @returns ROS topics and time of last refresh
 */
export const useTopics = (shouldRefresh: boolean) => {
  const { rosClient } = useContext(RosContext);
  const [rosTopics, setRosTopics] = useState<Topic[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState("");

  useEffect(() => {
    const id = setInterval(() => {
      rosClient?.getTopics(({ topics, types }) => {
        const newRosTopics = topics.map((topic, index) => ({
          name: topic,
          type: types[index],
        }));

        if (!isEqual(rosTopics, newRosTopics)) {
          setRosTopics(newRosTopics);
        }

        setLastRefreshed(dayjs().format("MMM D, YYYY h:mm:ss A"));
      });
    }, config.overview.autoRefreshFrequency);

    if (!shouldRefresh) {
      clearInterval(id);
    }

    return () => clearInterval(id);
  }, [shouldRefresh, rosClient, rosTopics]);

  return { topics: rosTopics, lastRefreshed };
};
