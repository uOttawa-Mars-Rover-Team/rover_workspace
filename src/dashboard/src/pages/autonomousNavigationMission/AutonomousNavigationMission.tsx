import { Helmet } from "react-helmet";
import { Header, Layout } from "../../components";
import { Image, Row, Button } from "antd";
import { useContext, useEffect, useState } from "react";
import {
  CameraOutlined,
  VideoCameraAddOutlined,
  FileAddOutlined,
} from "@ant-design/icons";
import ros from "../../contexts/ros";

const AutonomousNavigationMission: React.FC = () => {
  const [coordinates, setCoordinates] = useState(false);

  useEffect(() => {
    if (coordinates) {
      var fibonacciClient = new ROSLIB.Action({
        ros: ros,
        name: "/fibonacci",
        actionType: "idk",
      });

      // Send an action goal
      var goal = { GPS_coordinates: [/* target GPS coordinates */] };

      var goal_id = fibonacciClient.sendGoal(
        goal,
        function (result) {
          //Result confirming if the robot reached the target coordinates or not
        },
        function (feedback) {
          //Feedback from server current GPS coordinates
        }, //[current GPS coordinates of the robot]);
    }

  return(
  <>
    <Helmet>
      <title>rDash - Autonomous Navigation Mission</title>
    </Helmet>

    <Layout title="Autonomous Navigation Mission" menuKey="autonomousNavigationMission">
        <Header
          title="Autonomous Navigation System"
          icon=""
          extra={
            <Button onClick={() => setCoordinates((true))}>
              Submit Coordinates
            </Button>
          }
        />

        <Header title="LoL" icon={<FileAddOutlined />} />
        <div style={{ marginBottom: "30px" }}>
          
        </div>
      </Layout>
  </>
  )
};

export default AutonomousNavigationMission;

