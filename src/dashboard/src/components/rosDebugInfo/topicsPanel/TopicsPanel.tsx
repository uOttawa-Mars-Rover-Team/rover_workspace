import { useState, useContext } from "react";

import { useTopics } from "../../../hooks";
import { stringColumnSorter } from "../../../utils/table";
import CopiableTag from "../../copiableTag/CopiableTag";
import CustomTable from "../CustomTable";
import { DashboardContext } from "../../../contexts";

const TopicsPanel: React.FC = () => {
  const { autoRefresh } = useContext(DashboardContext);
  const [shouldRefresh, setShouldRefresh] = useState<boolean>(
    autoRefresh.topics,
  );
  const { topics, lastRefreshed } = useTopics(shouldRefresh);

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
          dataIndex: "type",
          title: "Message Type",
          render: (type) => <CopiableTag name={type} />,
          sorter: stringColumnSorter("type"),
        },
      ]}
      scroll={{ x: 800 }}
      data={topics}
      lastRefreshed={lastRefreshed}
      title="Topics"
      shouldRefresh={shouldRefresh}
      setShouldRefresh={setShouldRefresh}
    />
  );
};

export default TopicsPanel;
