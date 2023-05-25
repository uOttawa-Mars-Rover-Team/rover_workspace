import { Helmet } from "react-helmet";

import { Layout } from "../../components";

const AutonomousNavigationMission: React.FC = () => (
  <>
    <Helmet>
      <title>uoRover - Autonomous Navigation Mission</title>
    </Helmet>
    <Layout
      title="Autonomous Navigation Mission"
      menuKey="autonomousNavigationMission"
    />
  </>
);

export default AutonomousNavigationMission;
