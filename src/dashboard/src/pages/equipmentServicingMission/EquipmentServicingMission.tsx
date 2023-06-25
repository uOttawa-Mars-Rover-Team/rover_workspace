import { Helmet } from "react-helmet";

import { Layout } from "../../components";

const EquipmentServicingMission: React.FC = () => (
  <>
    <Helmet>
      <title>uoRover - Equipment Servicing Mission</title>
    </Helmet>
    <Layout
      title="Equipment Servicing Mission"
      menuKey="equipmentServicingMission"
    />
  </>
);

export default EquipmentServicingMission;
