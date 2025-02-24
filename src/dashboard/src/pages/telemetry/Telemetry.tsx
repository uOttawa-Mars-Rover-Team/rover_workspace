import { CompassOutlined, InfoCircleOutlined } from "@ant-design/icons";
import { Helmet } from "react-helmet";

import { Layout, Navigation, Header } from "../../components";

import {
  TelemetryContainer,
  TelemetryItem,
  DriveMotorTelemetry,
  PowerTelemetry,
  IMUTelemetry,
} from "../../components";

// Waveform
import WaveForm_Green from "/waveform.path.ecg.rectangle.green.svg";

import styles from "./Telemetry.module.css";

const telemetry: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>rDash - Telemetry</title>
      </Helmet>
      <Layout title="Telemetry" menuKey="telemetry">
        <Header title="Navigation" icon={<CompassOutlined />} />
        <Navigation />
        <IMUTelemetry />
        <Header title="Telemetry Data" icon={<InfoCircleOutlined />} />
        <PowerTelemetry />
        <div className={styles.TelemetryDiv}>
          <DriveMotorTelemetry />
          <TelemetryContainer style={{ width: "40%" }}>
            <TelemetryItem
              name="Heartbeat Front Left"
              data="Alive"
              image={WaveForm_Green}
            />
            <TelemetryItem
              name="Heartbeat Front Right"
              data="Alive"
              image={WaveForm_Green}
            />
            <TelemetryItem
              name="Heartbeat Back Left"
              data="Alive"
              image={WaveForm_Green}
            />
            <TelemetryItem
              name="Heartbeat Back Right"
              data="Alive"
              image={WaveForm_Green}
            />
          </TelemetryContainer>
        </div>
      </Layout>
    </>
  );
};

export default telemetry;
