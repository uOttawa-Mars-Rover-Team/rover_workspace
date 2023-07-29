import { Table } from "antd";
import { ColumnsType } from "antd/lib/table";

import CustomCollapse from "./CustomCollapse";

interface CustomTableProps {
  children?: React.ReactNode;
  lastRefreshed: string;
  title: string;
  data: any[];
  columns: ColumnsType<any>;
  shouldRefresh: boolean;
  setShouldRefresh: React.Dispatch<React.SetStateAction<boolean>>;
  scroll?: any;
}

const CustomTable: React.FC<CustomTableProps> = ({
  lastRefreshed,
  title,
  data,
  columns,
  shouldRefresh,
  setShouldRefresh,
  children,
  scroll,
}) => (
  <CustomCollapse
    lastRefreshed={lastRefreshed}
    title={title}
    size={data.length}
    shouldRefresh={shouldRefresh}
    setShouldRefresh={setShouldRefresh}
  >
    <Table
      pagination={{ showSizeChanger: true, style: { marginRight: 12 } }}
      size="small"
      dataSource={data}
      columns={columns}
      scroll={scroll}
    />
    {children}
  </CustomCollapse>
);

export default CustomTable;
