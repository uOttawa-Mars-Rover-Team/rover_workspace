import {
  CarOutlined,
  ControlOutlined,
  FilterOutlined,
} from "@ant-design/icons";
import { Button, Col, Row } from "antd";
import { Helmet } from "react-helmet";

import { Header, Layout } from "../../components";

const operations = {
  controls: [
    { label: "Hose Up", command: "hose-up" },
    { label: "Hose Down", command: "hose-down" },
    { label: "Hose Stop", command: "hose-stop" },
    { label: "Open Flap", command: "funnel-open" },
    { label: "Close Flap", command: "funnel-close" },
    { label: "Start Vibration Motor", command: "vibrate" },
    { label: "Stop Vibration Motor", command: "vibrate-stop" },
    { label: "Vacuum", command: "vacuum" },
  ],
  movement: [
    { label: "Return Home", command: "home" },
    { label: "Step Forward", command: "+" },
    { label: "Step Backward", command: "-" },
  ],
  beakers: [
    { label: "Beaker 1", command: "beaker1" },
    { label: "Beaker 2", command: "beaker2" },
    { label: "Beaker 3", command: "beaker3" },
    { label: "Beaker 4", command: "beaker4" },
    { label: "Beaker 5", command: "beaker5" },
    { label: "Beaker 6", command: "beaker6" },
    { label: "Beaker 7", command: "beaker7" },
    { label: "Beaker 8", command: "beaker8" },
    { label: "Beaker 9", command: "beaker9" },
    { label: "Beaker 10", command: "beaker10" },
  ],
};

const ScienceMission: React.FC = () => (
  <>
    <Helmet>
      <title>rDash - Science Mission</title>
    </Helmet>
    <Layout title="Science Mission" menuKey="scienceMission">
      <Header title="Beakers" icon={<FilterOutlined />} />
      <Row gutter={[12, 12]}>
        {operations.beakers.map(({ label }) => (
          <Col>
            <Button>{label}</Button>
          </Col>
        ))}
      </Row>

      <Header title="Movement" icon={<CarOutlined />} />
      <Row gutter={[12, 12]}>
        {operations.movement.map(({ label }) => (
          <Col>
            <Button>{label}</Button>
          </Col>
        ))}
      </Row>

      <Header title="Controls" icon={<ControlOutlined />} />
      <Row gutter={[12, 12]}>
        {operations.controls.map(({ label }) => (
          <Col>
            <Button>{label}</Button>
          </Col>
        ))}
      </Row>
    </Layout>
  </>
);

export default ScienceMission;
