import { Helmet } from "react-helmet";

import { Layout, Header, Navigation } from "../../components";
import { CompassOutlined } from "@ant-design/icons";

const AutonomousNavigationMission: React.FC = () => (
  <>
    <Helmet>
      <title>uoRover - Autonomous Navigation Mission</title>
    </Helmet>
    <Layout
      title="Autonomous Navigation Mission"
      menuKey="autonomousNavigationMission"
    >
      <Header title="Navigation" icon={<CompassOutlined />} />
      <Navigation />
    </Layout>
  </>
);

export default AutonomousNavigationMission;
