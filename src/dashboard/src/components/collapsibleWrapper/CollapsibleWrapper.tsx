import { Col, Collapse } from "antd";

type CollapsibleWrapperProps = {
  header: string;
  children: React.ReactNode;
};

const CollapsibleWrapper: React.FC<CollapsibleWrapperProps> = ({
  header,
  children,
}) => {
  const collapsibleWrapperCollapseItems = [
    {
      key: "1",
      label: header,
      children: <>{children}</>,
    },
  ];

  return (
    <Col sm={24} lg={12} xl={8} xxl={6}>
      <Collapse
        items={collapsibleWrapperCollapseItems}
        defaultActiveKey={["1"]}
      />
    </Col>
  );
};

export default CollapsibleWrapper;
