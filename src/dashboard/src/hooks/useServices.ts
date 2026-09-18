import { useContext, useEffect, useState } from "react";
import isEqual from "react-fast-compare";
import dayjs from "dayjs";

import { RosContext } from "../contexts";
import * as config from "../dashboardConfig.json";

/**
 * React Hook wrapper on ROSLIB Services
 *
 * @param shouldRefresh Specify if services should periodically get refreshed
 * @returns ROS services and time of last refresh
 */
export const useServices = (shouldRefresh: boolean) => {
  const { rosClient } = useContext(RosContext);
  const [rosServices, setRosServices] = useState<string[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState("");

  useEffect(() => {
    const id = setInterval(() => {
      rosClient?.getServices((newRosServices) => {
        if (!isEqual(rosServices, newRosServices)) {
          setRosServices(newRosServices);
        }

        setLastRefreshed(dayjs().format("MMM D, YYYY h:mm:ss A"));
      });
    }, config.overview.autoRefreshFrequency);

    if (!shouldRefresh) {
      clearInterval(id);
    }

    return () => clearInterval(id);
  }, [shouldRefresh, rosClient, rosServices]);

  return { services: rosServices, lastRefreshed };
};
