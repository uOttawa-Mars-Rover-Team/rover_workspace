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
  const [targetPosition, setTargetPosition] = useState<Leaflet.LatLngTuple>([0.0,0.0]);

  const [roverPosition, setRoverPosition] = useState<Leaflet.LatLngTuple>([
      latitude,
      longitude,
    ]);

    const [gpsWaypointMessage, setGpsWaypointMessage] = useState<GPSMessage>({
      status: { status: -1 },
      altitude: 0,
      latitude: currentPosition.lat,
      longitude: currentPosition.lng,
    });


    const handleSubmitTargetPosition = (targetPosition: Leaflet.LatLngTuple) => {

      if (rosClient) {
        const abc = new ROSLIB.ActionClient({
          ros: rosClient,
          serverName: "FollowGpsWaypoints",
          actionName: "/follow_gps_waypoints",
        });
        
        var goal = new ROSLIB.Goal({
          actionClient: abc,
          goalMessage: { 
            number_of_loops: 0,
            goal_index: 0,
            gps_poses: [
              { 
                position: {latitude: targetPosition[0], longitude: targetPosition[1], altitude: 0 },
                orientation: {x: 0, y: 0, z: 0, w: 1}
              }
            ]
          },
        });
        
        goal.on("result", function (result) {
          console.log("Action result:", result);
          notification.success({
            message: "Mission Completed",
            description: "The rover has reached the target position.",
          });
        });

        goal.send();
      }
      

      // setTargetPosition([0.0, 0.0]);

    };

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
          <div style={{display: "flex", flexDirection: "column", marginTop: "10px" }}>
            <label style={{ fontWeight: "bold" }}>Lattitude</label>
            <Input
              value={targetPosition[0]}
              max={90}
              min={-90}
              type="number"
              onChange={(e) => {
                setTargetPosition([
                  Math.min(90, Math.max(-90, parseFloat(e.target.value))),
                  targetPosition[1]
                ]);
              }}
            />
            </div>
            <div style={{display: "flex", flexDirection: "column", marginTop: "10px" }}>
            <label style={{ fontWeight: "bold" }}>Longitude</label>
            <Input
              value={targetPosition[1]}
              max={180}
              min={-180}
              type="number"
              onChange={(e) => {
                setTargetPosition([
                  targetPosition[0],
                  Math.min(180, Math.max(-180, parseFloat(e.target.value)))
                ]);
              }}
            />
            </div>
          </Descriptions.Item>
        </Descriptions>


        <Space>
          <Button onClick={() => handleSubmitTargetPosition(targetPosition)}>
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



