import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import { useContext, useEffect, useState } from "react";

//components
import TelemetryContainer from "../../components/telemetryContainer/TelemetryContainer";
import TelemetryBox from "../../components/TelemetryBox/TelemetryBox";

//icons
//roll pitch yaw
import Pitch from '/digitalcrown.arrow.clockwise.fill.svg'
import Yaw from '/digitalcrown.horizontal.arrow.counterclockwise.fill.svg'
import Roll from '/arrow.triangle.2.circlepath.svg'

type ImuMesssage = {
    roll : number;
    pitch : number;
    yaw : number;
}

export default function ImuTelemetry() {
    const { rosClient } = useContext(RosContext);
    const [imuData, setImuData] = useState<ImuMesssage>();
    const roundPrecision = 2
  
  
    useEffect(() => {
      if (rosClient) {
        const imuDataTopic = new ROSLIB.Topic({
          ros: rosClient!,
          name: config.overview.telemetry.imuTopicName,
          messageType: "general_interfaces/msg/IMU",
        });
        
        imuDataTopic.subscribe((msg) => {
          const message = msg as ImuMesssage;
          setImuData(message);
        });
        
        return () => {
          imuDataTopic.unsubscribe();
        };
      }
    }, [rosClient]);
    
    return <TelemetryContainer style={{marginTop: 20}}>
        <TelemetryBox name="Roll" data={imuData?.roll.toFixed(roundPrecision) + "°"} image={Roll}></TelemetryBox>
        <TelemetryBox name="Pitch" data={imuData?.pitch.toFixed(roundPrecision) + "°"} image={Pitch}></TelemetryBox>
        <TelemetryBox name="Yaw" data={imuData?.yaw.toFixed(roundPrecision) + "°"} image={Yaw}></TelemetryBox>
  </TelemetryContainer>
  }


