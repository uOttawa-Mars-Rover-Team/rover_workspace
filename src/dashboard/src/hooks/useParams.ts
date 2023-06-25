import { useContext, useEffect, useState } from "react";
import isEqual from "react-fast-compare";
import dayjs from "dayjs";

import { RosContext } from "../contexts";
import * as config from "../dashboardConfig.json";
import { getParam } from "../utils/ros";

export interface Param {
  name: string;
  value: string;
}

/**
 * React Hook wrapper on ROSLIB Params
 * 
 * @param shouldRefresh Specify if params should periodically get refreshed
 * @returns ROS params and time of last refresh
 */
export const useParams = (shouldRefresh: boolean) => {
  const { rosClient } = useContext(RosContext);
  const [rosParams, setRosParams] = useState<Param[]>([]);
  const [lastRefreshed, setLastRefreshed] = useState("");

  useEffect(() => {
    let id = setInterval(() => {
      rosClient?.getParams(async (params) => {
        let newRosParamsPromises = params.map((param) =>
          getParam(rosClient, param)
        );
        let newRosParams = await Promise.all(newRosParamsPromises);

        if (!isEqual(rosParams, newRosParams)) {
          setRosParams(newRosParams);
        }

        setLastRefreshed(dayjs().format("MMM D, YYYY h:mm:ss A"));
      });
    }, config.overview.autoRefreshFrequency);

    if (!shouldRefresh) {
      clearInterval(id);
    }

    return () => clearInterval(id);
  }, [rosClient, rosParams, shouldRefresh]);

  return { params: rosParams, lastRefreshed };
};
