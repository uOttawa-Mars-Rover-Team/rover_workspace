import { Helmet } from "react-helmet";
import { Header, Layout, Navigation } from "../../components";
import "leaflet/dist/leaflet.css";
import * as Leaflet from "leaflet";
import {
  Button,
  Col,
  Descriptions,
  Image,
  Input,
  notification,
  Row,
  Select,
  Space,
  Switch,
  Typography,
} from "antd";
import { useContext, useEffect, useState } from "react";
import ros from "../../contexts/ros";
import GpsWaypointRecorder from "../../components/gpsWaypointRecorder/GpsWaypointRecorder";
import { GPSMessage } from "../../components/navigation/Navigation";
import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";

export const defaultPrecision = 5;

const AutonomousNavigationMission: React.FC = () => {
  const { rosClient } = useContext(RosContext);
  const { latitude, longitude } =
    config.overview.navigation.baseStationInitPosition;
  const currentPosition = new Leaflet.LatLng(latitude, longitude);
  const newPosition = new Leaflet.LatLng(latitude, longitude);
  const [targetPosition, setTargetPosition] = useState<Leaflet.LatLngTuple>([
      newPosition.lat,
      newPosition.lng,
    ]);

  const [roverPosition, setRoverPosition] = useState<Leaflet.LatLngTuple>([
      currentPosition.lat,
      currentPosition.lng,
    ]);

    const [gpsWaypointMessage, setGpsWaypointMessage] = useState<GPSMessage>({
      status: { status: -1 },
      altitude: 0,
      latitude: currentPosition.lat,
      longitude: currentPosition.lng,
    });

  useEffect(() => {
    if (rosClient) {
      const topicName = config.overview.navigation.gpsTopicName;
      const topic = new ROSLIB.Topic({
        ros: rosClient,
        name: topicName,
        messageType: "sensor_msgs/NavSatFix",
      });
      topic.subscribe((msg) => {
        const message = msg as GPSMessage;
        if (message.status.status >= 0 && message.status.status <= 2) {
          setRoverPosition([message.latitude!, message.longitude!]);
          setGpsWaypointMessage(message);
        }
      });

      return () => {
        topic.unsubscribe();
      };
    }
  }, [rosClient]);

  useEffect(() => {
    if (targetPosition) {
      // var fibonacciClient = new ROSLIB.Action({
      //   ros: ros,
      //   name: "/fibonacci",
      //   actionType: "idk",
      // });
      
      // Send an action goal
      // var goal = { GPS_targetPosition: [/* target GPS targetPosition */] };

      // var goal_id = fibonacciClient.sendGoal(
      //   goal,
      //   function (result) {
      //     //Result confirming if the robot reached the target targetPosition or not
      //   },
      //   function (feedback) {
      //     //Feedback from server current GPS targetPosition
      //   }, //[current GPS targetPosition of the robot]);
      // );
    }
  }, [targetPosition]);

  return(
  <>
    <Helmet>
      <title>rDash - Autonomous Navigation Mission</title>
    </Helmet>

    <Layout title="Autonomous Navigation Mission" menuKey="autonomousNavigationMission">
        <Header
          title="Autonomous Navigation System"
          icon=""
        />
        <div style={{ marginBottom: "70px" , marginLeft: "70px" , marginRight: "70px"}}>
          <Navigation/>
        </div>
        
        <Descriptions>
          <Descriptions.Item label={<b>Current GPS Position</b>} span={24}>
            <Col>
              Rover Position:{" "}
              <Typography.Text copyable>
                {`${roverPosition[0].toFixed(
                  defaultPrecision
                )}, ${roverPosition[1].toFixed(defaultPrecision)}`}
              </Typography.Text>
            </Col>
          </Descriptions.Item>

          <Descriptions.Item label={<b>Target GPS Position</b>} span={24}>
            <Input
              value={targetPosition?.newPosition?.lat || ""}
              placeholder="Enter a GPS lattitude value (eg: 34.0522° N)"
              type="number"
              onChange={(e) => {
                setTargetPosition({
                  newPosition: {
                    lat: e.target.value
                  }
                });
              }}
            />
            <Input
              value={targetPosition?.newPosition?.lng || ""}
              placeholder="Enter an GPS longitude value (eg: 118.2437° W)"
              type="number"
              onChange={(e) => {
                setTargetPosition({
                  newPosition: {
                    lng: e.target.value
                  }
                });
              }}
            />
          </Descriptions.Item>
        </Descriptions>


        <Space>
          <Button onClick={() => setTargetPosition({ newPosition: { lat: 0, lng: 0 } })}>
            Submit targetPosition
          </Button>
        </Space>
        
        <div style={{ marginTop: "30px", marginBottom: "30px" }}>

          <GpsWaypointRecorder message={gpsWaypointMessage} />
          
        </div>
      </Layout>
  </>
  )
};

export default AutonomousNavigationMission;



