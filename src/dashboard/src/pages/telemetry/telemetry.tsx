import {
  CompassOutlined,
  InfoCircleOutlined
} from "@ant-design/icons";
import { Helmet } from "react-helmet";

import {
  Layout,
  Navigation,
  Header
} from "../../components";

import TelemetryContainer from "../../components/telemetryContainer/TelemetryContainer";
import TelemetryBox from "../../components/TelemetryBox/TelemetryBox";
import DriveMotorTelemetry from "../../components/driveMotorTelemetry/DriveMotorTelemetry";
import ImuTelemetry from "../../components/imuTelemetry/ImuTelemetry";
import PowerTelemetry from "../../components/powerTelemetry/PowerTelemetry";

//waveform
import WaveForm_Green from '/waveform.path.ecg.rectangle.green.svg'


import styles from './telemetry.module.css'

const telemetry: React.FC = () => {

  return (
    <>
      <Helmet>
        <title>rDash - Telemetry</title>
      </Helmet>
      <Layout title="Telemetry" menuKey="telemetry">
        <Header title="Navigation" icon={<CompassOutlined />} />
        <Navigation/>
        {/*
        <TelemetryContainer>
          <TelemetryBox name="Cardinality" data="NE" image={Heading}></TelemetryBox>
          <TelemetryBox name="Roll" data="2°" image={Roll}></TelemetryBox>
          <TelemetryBox name="Pitch" data="10°" image={Pitch}></TelemetryBox>
          <TelemetryBox name="Yaw" data="45°" image={Yaw}></TelemetryBox>
        </TelemetryContainer>
        */
        }
        <ImuTelemetry/>

        <Header title="Telemetry Data" icon={<InfoCircleOutlined />} />
        {/*
          <TelemetryContainer>
          <TelemetryBox name="Battery Voltage" data="19.2V" image={Battery_100_Green}></TelemetryBox>
          <TelemetryBox name="Total Current" data="26.7A" image={Bolt_yellow}></TelemetryBox>
          <TelemetryBox name="Rover Speed" data="4 m/s" image={Gauge_White}></TelemetryBox>
          </TelemetryContainer>
          */
        }
        <PowerTelemetry/>

        <div className={styles.TelemetryDiv}>
          {/*
          <TelemetryContainer style={{width: '40%'}}>
          <TelemetryBox name="RPM Front Left" data="25.0 RPM" image={GearShape_Green}></TelemetryBox>
          <TelemetryBox name="RPM Front Right" data="25.2 RPM" image={GearShape_Yellow}></TelemetryBox>
          <TelemetryBox name="RPM Back Left" data="24.9 RPM" image={GearShape_Green}></TelemetryBox>
          <TelemetryBox name="RPM Back Right" data="25.1 RPM" image={GearShape_Red}></TelemetryBox>
          </TelemetryContainer>
          */
          }

          <DriveMotorTelemetry/>

          


          <TelemetryContainer style={{width: '40%'}}>
            <TelemetryBox name="Heartbeat Front Left" data="Alive" image={WaveForm_Green}></TelemetryBox>
            <TelemetryBox name="Heartbeat Front Right" data="Alive" image={WaveForm_Green}></TelemetryBox>
            <TelemetryBox name="Heartbeat Back Left" data="Alive" image={WaveForm_Green}></TelemetryBox>
            <TelemetryBox name="Heartbeat Back Right" data="Alive" image={WaveForm_Green}></TelemetryBox>
          </TelemetryContainer>
        </div>
      </Layout>
    </>
  );
};

export default telemetry;
