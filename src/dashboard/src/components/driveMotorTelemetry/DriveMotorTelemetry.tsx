import "@fortawesome/fontawesome-free/css/all.min.css";
import "leaflet/dist/leaflet.css";
import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import { useContext, useEffect, useState } from "react";

//components
import TelemetryContainer from "../../components/telemetryContainer/TelemetryContainer";
import TelemetryBox from "../../components/TelemetryBox/TelemetryBox";

//icons
//gearshape
import GearShape_Green from '/gearshape.circle.fill.green.svg'

type MotorDataMessage = {
  velocity_feedback: number;
  positon_feedback: number;
  output_current: number;
  output_voltage: number;
  sticky_faults: string;
  faults_bitfield: number;
};

export default function DriveMotorTelemetry() {
  const { rosClient } = useContext(RosContext);
  //const [motorData, setMotorData] = useState<MotorDataMessage>();
  const [motorDataLeft, setMotorDataLeft] = useState<MotorDataMessage>();
  const [motorDataRight, setMotorDataRight] = useState<MotorDataMessage>();
  const roundPrecision = 2


  useEffect(() => {
    if (rosClient) {
        const motorDataTopic = new ROSLIB.Topic({
        ros: rosClient!,
        name: config.overview.telemetry.motorDataTopicName,
        messageType: "general_interfaces/msg/MotorData",
      });
      
      motorDataTopic.subscribe((msg) => {
        const message = msg as MotorDataMessage;
        if(message.sticky_faults === "Left Side") {
          setMotorDataLeft(message)
        } else {
          setMotorDataRight(message)
        }
        //setMotorData(message);
      });
      
      return () => {
        motorDataTopic.unsubscribe();
      };
    }
  }, [rosClient]);
  
  return <TelemetryContainer style={{width: '40%'}}>
    <TelemetryBox name="RPM Front Left" data={motorDataLeft?.velocity_feedback.toFixed(roundPrecision) +" RPM"} image={GearShape_Green}></TelemetryBox>
    <TelemetryBox name="RPM Front Right" data={motorDataRight?.velocity_feedback.toFixed(roundPrecision) +" RPM"} image={GearShape_Green}></TelemetryBox>
    <TelemetryBox name="RPM Back Left" data={motorDataLeft?.velocity_feedback.toFixed(roundPrecision) +" RPM"} image={GearShape_Green}></TelemetryBox>
    <TelemetryBox name="RPM Back Right" data={motorDataRight?.velocity_feedback.toFixed(roundPrecision) +" RPM"} image={GearShape_Green}></TelemetryBox>
  </TelemetryContainer>
}
