import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import { useContext, useEffect, useState } from "react";
import TelemetryContainer from "../telemetryContainer/TelemetryContainer";
import { Row, Col, Space } from "antd";
import ArtificialHorizon from "./ArtificialHorizon.tsx";
import AccelBars from "./AccelBars.tsx";

type ImuMessage = {
  roll: number;
  pitch: number;
  yaw: number;
  accel_x: number;
  accel_y: number;
  accel_z: number;
  accel_norm: number;
};

const SAMPLE_DATA: ImuMessage = {
  roll: 23,
  pitch: 12,
  yaw: 0,
  accel_x: 3.2,
  accel_y: 7.8,
  accel_z: 10,
  accel_norm: 3.6,
};

const roundTo3 = (value: number): number => Math.round(value * 1000) / 1000;

export default function IMUTelemetry() {
  const { rosClient } = useContext(RosContext);
  const [imuData, setImuData] = useState<ImuMessage>(SAMPLE_DATA);

  useEffect(() => {
    if (!rosClient) return;
    const topic = new ROSLIB.Topic({
      ros: rosClient,
      name: config.overview.telemetry.imuTopicName,
      messageType: "general_interfaces/msg/IMU",
    });
    topic.subscribe((msg) => {
      const raw = msg as ImuMessage;
      setImuData({
        roll: (-1)*(roundTo3(raw.roll)),
        pitch: roundTo3(raw.pitch),
        yaw: roundTo3(raw.yaw),
        accel_x: roundTo3(raw.accel_x / 9.80665),
        accel_y: roundTo3(raw.accel_y / 9.80665),
        accel_z: roundTo3(raw.accel_z / 9.80665),
        accel_norm: roundTo3(raw.accel_norm / 9.80665),
      });
    });
    return () => topic.unsubscribe();
  }, [rosClient]);

  return (
    <TelemetryContainer>
      <Row
        justify="center"
        align="middle"
        style={{ width: "100%", height: "100%" }}
        gutter={48}
      >
        <Col>
          <ArtificialHorizon roll={imuData.roll} pitch={imuData.pitch} />
        </Col>
        <Col flex="620px">
          <AccelBars
            ax={imuData.accel_x}
            ay={imuData.accel_y}
            az={imuData.accel_z}
            norm={imuData.accel_norm}
          />
        </Col>
      </Row>
    </TelemetryContainer>
  );
}