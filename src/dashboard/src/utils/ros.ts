import ROSLIB, { Ros } from "roslib";
import { Node } from "../hooks/useNodes";
import { Param } from "../hooks/useParams";

/**
 * Delete ROS param wrapper (making it async friendly, instead of using callbacks)
 * 
 * @param ros Ros client
 * @param name Name of param
 * @returns Promise wrapping the callback
 */
export const deleteParam = (ros: Ros, name: string): Promise<any> =>
  new Promise((resolve, reject) => {
    try {
      new ROSLIB.Param({
        ros,
        name,
      }).delete((a) => resolve(a));
    } catch (e) {
      reject(e);
    }
  });

/**
 * Set ROS param wrapper (making it async friendly, instead of using callbacks)
 * 
 * @param ros Ros client
 * @param name Name of param
 * @param value Value of param
 * @returns Promise wrapping the callback
 */
export const setParam = (ros: Ros, name: string, value: string): Promise<any> =>
  new Promise((resolve, reject) => {
    try {
      new ROSLIB.Param({
        ros,
        name,
      }).set(value, (a) => resolve(a));
    } catch (e) {
      reject(e);
    }
  });

/**
 * Get ROS param wrapper (making it async friendly, instead of using callbacks)
 * 
 * @param ros Ros client
 * @param name Name of param
 * @returns Promise returning the param (name and value)
 */
export const getParam = (ros: Ros, name: string): Promise<Param> =>
  new Promise((resolve, reject) => {
    try {
      new ROSLIB.Param({
        ros,
        name,
      }).get((value) => resolve({ name, value }));
    } catch (e) {
      reject(e);
    }
  });

/**
 * Get ROS node wrapper (making it async friendly, instead of using callbacks)
 * 
 * @param ros Ros client
 * @param name Name of node
 * @returns Promise returning the node (publishing and subscribing topics and services)
 */
export const getNode = (ros: Ros, name: string): Promise<Node> =>
  new Promise((resolve, reject) => {
    try {
      // @ts-ignore
      ros.getNodeDetails(name, ({ publishing, subscribing, services }) =>
        resolve({ publishing, subscribing, services, name })
      );
    } catch (e) {
      reject(e);
    }
  });
