import { useState, useContext } from "react";
import { Row } from "antd";

import { useNodes } from "../../../hooks";
import CopiableTag from "../../copiableTag/CopiableTag";
import CustomTable from "../CustomTable";
import { stringColumnSorter } from "../../../utils/table";
import { DashboardContext } from "../../../contexts";

const NodesPanel: React.FC = () => {
  const { autoRefresh } = useContext(DashboardContext);
  const [shouldRefresh, setShouldRefresh] = useState<boolean>(
    autoRefresh.nodes
  );
  const { nodes, lastRefreshed } = useNodes(shouldRefresh);

  return (
    <CustomTable
      columns={[
        {
          dataIndex: "name",
          title: "Name",
          render: (type) => <CopiableTag name={type} />,
          sorter: stringColumnSorter("name"),
        },
        {
          dataIndex: "subscribing",
          title: "Subscribed Topics",
          render: (topics) => (
            <Row gutter={[0, 6]}>
              {topics.map((i: string) => (
                <CopiableTag name={i} />
              ))}
            </Row>
          ),
        },
        {
          dataIndex: "publishing",
          title: "Published Topics",
          render: (topics) => (
            <Row gutter={[0, 6]}>
              {topics.map((i: string) => (
                <CopiableTag name={i} />
              ))}
            </Row>
          ),
        },
        {
          dataIndex: "services",
          title: "Services",
          render: (services) => (
            <Row gutter={[0, 6]}>
              {services.map((i: string) => (
                <CopiableTag name={i} />
              ))}
            </Row>
          ),
        },
      ]}
      data={nodes}
      lastRefreshed={lastRefreshed}
      title="Nodes"
      shouldRefresh={shouldRefresh}
      setShouldRefresh={setShouldRefresh}
    />
  );
};

export default NodesPanel;
