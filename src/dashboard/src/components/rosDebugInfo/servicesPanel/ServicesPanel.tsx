import { Empty, Row } from "antd";
import { useState, useContext } from "react";

import { useServices } from "../../../hooks";
import CopiableTag from "../../copiableTag/CopiableTag";
import CustomCollapse from "../CustomCollapse";
import { DashboardContext } from "../../../contexts";

const ServicesPanel: React.FC = () => {
  const { autoRefresh } = useContext(DashboardContext);
  const [shouldRefresh, setShouldRefresh] = useState<boolean>(
    autoRefresh.services
  );
  const { services, lastRefreshed } = useServices(shouldRefresh);

  return (
    <CustomCollapse
      size={services.length}
      lastRefreshed={lastRefreshed}
      title="Services"
      shouldRefresh={shouldRefresh}
      setShouldRefresh={setShouldRefresh}
    >
      <Row
        gutter={[0, 6]}
        style={{ padding: 12 }}
        justify={services.length === 0 ? "center" : "start"}
      >
        {services.map((i) => (
          <CopiableTag name={i} />
        ))}
        {services.length === 0 && (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}
      </Row>
    </CustomCollapse>
  );
};

export default ServicesPanel;
