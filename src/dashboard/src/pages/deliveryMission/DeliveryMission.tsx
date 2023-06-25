import { Helmet } from "react-helmet";

import { Layout } from "../../components";

const DeliveryMission: React.FC = () => (
  <>
    <Helmet>
      <title>uoRover - Delivery Mission</title>
    </Helmet>
    <Layout title="Delivery Mission" menuKey="deliveryMission" />
  </>
);

export default DeliveryMission;
