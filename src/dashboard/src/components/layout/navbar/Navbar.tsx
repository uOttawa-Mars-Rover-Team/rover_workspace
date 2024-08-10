import {
  Col,
  Menu,
  Popover,
  Row,
  Layout,
  Typography,
  Button,
  Input,
  Tooltip,
} from "antd";
import {
  ApiOutlined,
  DownloadOutlined,
  PoweroffOutlined,
  MenuOutlined,
  HomeOutlined,
  ExperimentOutlined,
  RobotOutlined,
  FieldTimeOutlined,
  NodeIndexOutlined,
  VideoCameraOutlined,
  RadarChartOutlined,
} from "@ant-design/icons";
import { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import LogoImage from "../../../assets/images/logo.png";
import { RosContext, DashboardContext } from "../../../contexts";

const { Header } = Layout;
const { Title } = Typography;

interface NavbarProps {
  title: React.ReactNode;
  menuKey: string;
}

const Navbar: React.FC<NavbarProps> = ({ menuKey, title }) => {
  const { connect, disconnect, connected, url, setUrl } =
    useContext(RosContext);
  const { dashboardConfig } = useContext(DashboardContext);

  const navigate = useNavigate();

  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const updateWidth = () => setWindowWidth(window.innerWidth);

  useEffect(() => {
    window.addEventListener("resize", updateWidth);
    return () => window.removeEventListener("resize", updateWidth);
  }, []);

  return (
    <Header
      style={{
        position: "fixed",
        zIndex: 10000,
        bottom: 10,
        left: 10,
        borderRadius: 6,
        paddingLeft: 12,
        paddingRight: 12,
        marginRight: 10,
        background: "linear-gradient(20deg, #974b1c 5%, #EF8934 50%)",
      }}
    >
      <img
        src={LogoImage}
        alt={"uoRover logo"}
        height={120}
        className="root-header-logo"
      />
      <Row
        justify="space-between"
        align="middle"
        style={{ height: "100%", marginLeft: 100 }}
        gutter={[12, 12]}
      >
        <Col>
          <Title level={2} style={{ margin: 0, opacity: 1 }}>
            {title}
          </Title>
        </Col>
        <Col style={{ marginRight: 12 }}>
          <Popover
            overlayClassName="root-header-menu"
            content={
              <Menu
                style={{ borderRadius: 6, borderWidth: 0 }}
                onClick={({ key }) => {
                  navigate(`/${key}`);
                }}
                selectedKeys={[menuKey]}
              >
                <Menu.Item key="overview">
                  <HomeOutlined />
                  <span>Overview</span>
                </Menu.Item>
                <Menu.Item key="telemetry">
                <RadarChartOutlined />
                  <span>Telemetry</span>
                </Menu.Item>
                <Menu.Item key="camera">
                <VideoCameraOutlined />
                  <span>Camera</span>
                </Menu.Item>
                <Menu.Item key="scienceMission">
                  <ExperimentOutlined />
                  <span>Science Mission</span>
                </Menu.Item>
                <Menu.Item key="deliveryMission">
                  <FieldTimeOutlined />
                  <span>Delivery Mission</span>
                </Menu.Item>
                <Menu.Item key="equipmentServicingMission">
                  <RobotOutlined />
                  <span>Equipment Servicing Mission</span>
                </Menu.Item>
                <Menu.Item key="autonomousNavigationMission">
                  <NodeIndexOutlined />
                  <span>Autonomous Navigation Mission</span>
                </Menu.Item>
              </Menu>
            }
            overlayStyle={{ padding: 0 }}
            trigger="click"
          >
            <Button icon={<MenuOutlined />} />
          </Popover>
        </Col>
        <Col>
          {!connected && (
            <Input
              placeholder="Set ROS URL"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
            />
          )}
        </Col>
        <Col style={{ marginRight: 12 }}>
          {connected ? (
            <Tooltip title="Disconnect from ROS">
              <Button onClick={disconnect}>
                <PoweroffOutlined />
                {windowWidth >= 570 && "Disconnect from ROS"}
              </Button>
            </Tooltip>
          ) : (
            <Tooltip title="Connect to ROS">
              <Button onClick={connect}>
                <ApiOutlined />
                {windowWidth >= 750 && "Connect to ROS"}
              </Button>
            </Tooltip>
          )}
        </Col>
        {windowWidth >= 820 && (
          <Col>
            <Tooltip title="Download dashboard layout">
              <Button
                href={`data:application/json;charset=utf-8,${dashboardConfig()}`}
                target="_blank"
                download="dashboardConfig.json"
              >
                <DownloadOutlined />
                {windowWidth >= 1000 && "Download dashboard layout"}
              </Button>
            </Tooltip>
          </Col>
        )}
      </Row>
    </Header>
  );
};

export default Navbar;
