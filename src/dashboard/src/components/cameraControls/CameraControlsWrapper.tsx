import { Col, Collapse } from "antd";

type CameraControlsWrapperProps = {
  header: string;
  children: React.ReactNode;
};

const CameraControlsWrapper: React.FC<CameraControlsWrapperProps> = ({
  header,
  children,
}) => {
  const cameraControlsCollapseItems = [
    {
      key: "1",
      label: header,
      children: <>{children}</>,
    },
  ];

  return (
    <Col sm={24} lg={12} xl={8} xxl={6}>
      <Collapse items={cameraControlsCollapseItems} defaultActiveKey={["1"]} />
    </Col>
  );
};

export default CameraControlsWrapper;
