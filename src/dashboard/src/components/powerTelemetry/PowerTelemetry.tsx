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
import Bolt_yellow from '/bolt.fill.yellow.svg'

import Battery_100_Green from '/battery.100percent.green.svg'

import Gauge_White from '/gauge.open.with.lines.needle.33percent.white.svg'

type PowerDataMessage = {
    voltage: number;
    currents: number[];
    filled: number;
  };

export default function PowerTelemetry() {
  const { rosClient } = useContext(RosContext);
  const [powerData, setPowerData] = useState<PowerDataMessage>();
  const roundPrecision = 2


  useEffect(() => {
    if (rosClient) {
        const powerDataTopic = new ROSLIB.Topic({
        ros: rosClient!,
        name: config.overview.telemetry.powerDataTopicName,
        messageType: "general_interfaces/msg/PowerData",
      });
      
      powerDataTopic.subscribe((msg) => {
        const message = msg as PowerDataMessage;
        setPowerData(message);
      });
      
      return () => {
        powerDataTopic.unsubscribe();
      };
    }
  }, [rosClient]);
  
  return <TelemetryContainer>
    <TelemetryBox name="Battery Voltage" data={powerData?.voltage.toFixed(roundPrecision) + "V"} image={Battery_100_Green}></TelemetryBox>
    <TelemetryBox name="Total Current" data={powerData?.currents[0].toFixed(roundPrecision) + "A"} image={Bolt_yellow}></TelemetryBox>
    <TelemetryBox name="Rover Speed" data="4 m/s" image={Gauge_White}></TelemetryBox>
</TelemetryContainer>
}
