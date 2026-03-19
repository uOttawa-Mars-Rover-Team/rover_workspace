import { Helmet } from "react-helmet";
import { Header, Layout } from "../../components";
import { Image, Row, Button } from "antd";
import { useContext, useState } from "react";
import {
  CameraOutlined,
  VideoCameraAddOutlined,
  FileAddOutlined,
} from "@ant-design/icons";

const AutonomousNavigationMission: React.FC = () => {
  const [coordinates, setCoordinates] = useState(false);

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
