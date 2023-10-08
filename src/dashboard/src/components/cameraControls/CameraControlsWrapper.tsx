import { Col, Collapse } from "antd";

type CameraControlsWrapperProps = {
  header: string;
  children: React.ReactNode;
};

const CameraControlsWrapper: React.FC<CameraControlsWrapperProps> = ({
  header,
  children,
}) => {
  return (
    <Col sm={24} lg={12} xl={8} xxl={6}>
      <Collapse defaultActiveKey={["1"]}>
        <Collapse.Panel header={header} key="1">
          {children}
        </Collapse.Panel>
      </Collapse>
    </Col>
  );
};

export default CameraControlsWrapper;
