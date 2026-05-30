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
  accel_x: number;
  accel_y: number;
  accel_z: number;
  accel_norm: number;
};

const SAMPLE_DATA: ImuMessage = {
  roll: 23,
  pitch: 12,
  accel_x: 3.2,
  accel_y: 7.8,
  accel_z: 10,
  accel_norm: 3.6,
};

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

    topic.subscribe((msg) => setImuData(msg as ImuMessage));
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