import { useContext, useEffect, useState } from "react";
import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import { Descriptions, Row } from "antd";
import CollapsibleWrapper from "../collapsibleWrapper/CollapsibleWrapper";

type MotorDataMessage = {
  velocity_feedback: number;
  position_feedback: number;
  output_current: number;
  output_voltage: number;
  sticky_faults: string;
  faults_bitfield: number;
};
type PowerDataMessage = {
  voltage: number;
  currents: number[];
  filled: number;
};

/*
Access an object's property if it exists, return the default value if it doesn't.
Intended for use with object representations of ROS messages.
*/
const safeAccess = (
  obj: { [key: string]: any } | undefined,
  key: string,
  defaultVal: any = "Unknown",
  roundPrecision: number = 3
) => {
  const returnVal = obj ? obj[key] : defaultVal;
  return typeof returnVal === "number"
    ? returnVal.toFixed(roundPrecision)
    : returnVal;
};

const Telemetry: React.FC = () => {
  const numPowerDataCurrents = 16;
  const { rosClient } = useContext(RosContext);
  const [motorData, setMotorData] = useState<MotorDataMessage>();
  const [powerData, setPowerData] = useState<PowerDataMessage>();

  useEffect(() => {
    if (rosClient) {
      let motorDataTopic = new ROSLIB.Topic({
        ros: rosClient!,
        name: config.overview.telemetry.motorDataTopicName,
        messageType: "general_interfaces/msg/MotorData",
      });
      let powerDataTopic = new ROSLIB.Topic({
        ros: rosClient!,
        name: config.overview.telemetry.powerDataTopicName,
        messageType: "general_interfaces/msg/PowerData",
      });

      motorDataTopic.subscribe((msg) => {
        const message = msg as MotorDataMessage;
        setMotorData(message);
      });
      powerDataTopic.subscribe((msg) => {
        const message = msg as PowerDataMessage;
        console.log(message);
        setPowerData(message);
      });

      return () => {
        powerDataTopic.unsubscribe();
      };
    }
  }, [rosClient]);

  return (
    <>
      <Row gutter={[12, 12]}>
        {/* Motor Data */}
        <CollapsibleWrapper header="Motor Data">
          <Descriptions bordered size="small" layout="horizontal">
            <Descriptions.Item label={<b>Velocity Feedback</b>} span={4}>
              {safeAccess(motorData, "velocity_feedback")}
            </Descriptions.Item>
            <Descriptions.Item label={<b>Position Feedback</b>} span={4}>
              {safeAccess(motorData, "position_feedback")}
            </Descriptions.Item>
            <Descriptions.Item label={<b>Output Current</b>} span={4}>
              {safeAccess(motorData, "output_current")}
            </Descriptions.Item>
            <Descriptions.Item label={<b>Output Voltage</b>} span={4}>
              {safeAccess(motorData, "output_voltage")} V
            </Descriptions.Item>
            <Descriptions.Item label={<b>Sticky Faults</b>} span={4}>
              {safeAccess(motorData, "sticky_faults")}
            </Descriptions.Item>
            <Descriptions.Item label={<b>Faults Bitfield</b>} span={4}>
              {safeAccess(motorData, "faults_bitfield")}
            </Descriptions.Item>
          </Descriptions>
        </CollapsibleWrapper>
        {/* Power Data */}
        <CollapsibleWrapper header="Power Data">
          <Descriptions bordered size="small" layout="horizontal">
            <Descriptions.Item label={<b>Voltage</b>} span={24}>
              {safeAccess(powerData, "voltage")} V
            </Descriptions.Item>
            <Descriptions.Item label={<b>Currents</b>} span={24}>
              <Descriptions bordered size="small" layout="vertical">
                {[...Array(numPowerDataCurrents)].map((_, i) => {
                  return (
                    <Descriptions.Item key={i} label={<b>[{i}]</b>} span={0.75}>
                      {typeof safeAccess(powerData, "currents") === "string"
                        ? safeAccess(powerData, "currents")
                        : safeAccess(powerData, "currents")[i]}
                    </Descriptions.Item>
                  );
                })}
              </Descriptions>
            </Descriptions.Item>
            <Descriptions.Item label={<b>Filled</b>} span={24}>
              {safeAccess(powerData, "filled")}
            </Descriptions.Item>
          </Descriptions>
        </CollapsibleWrapper>
      </Row>
    </>
  );
};

export default Telemetry;
