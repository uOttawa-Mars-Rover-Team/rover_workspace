import { Helmet } from "react-helmet";

import { Layout } from "../../components";

const AutonomousNavigationMission: React.FC = () => (
  <>
    <Helmet>
      <title>rDash - Autonomous Navigation Mission</title>
    </Helmet>
    <Layout
      title="Autonomous Navigation Mission"
      menuKey="autonomousNavigationMission"
    />
  </>
);

export default AutonomousNavigationMission;
