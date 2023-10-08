import { Image, Row, Button, Col } from "antd";
import {
  CameraOutlined,
  VideoCameraAddOutlined,
  CompassOutlined,
  InfoCircleOutlined,
  WifiOutlined,
  FileAddOutlined,
} from "@ant-design/icons";
import { useContext, useState } from "react";
import { Helmet } from "react-helmet";

import {
  Layout,
  CameraFeed,
  Navigation,
  Header,
  TopicsPanel,
  ServicesPanel,
  ParamsPanel,
  NodesPanel,
  AddCameraFeedModal,
  LifeDetectionCharts,
  // TemperatureChart,
  CameraControls,
} from "../../components";
import { DashboardContext } from "../../contexts";

const Overview: React.FC = () => {
  const [addCameraModalVisible, setAddCameraModalVisible] = useState(false);
  const { cameraFeeds } = useContext(DashboardContext);

  return (
    <>
      <Helmet>
        <title>uoRover - Overview</title>
      </Helmet>
      <Layout title="Overview" menuKey="overview">
        {/* Cameras */}
        <Header
          title={`Cameras (${cameraFeeds.length})`}
          icon={<CameraOutlined />}
          style={{ paddingTop: 0 }}
          extra={
            <Button onClick={() => setAddCameraModalVisible(true)}>
              <VideoCameraAddOutlined />
              Add Camera Feed
            </Button>
          }
        />
        <Row gutter={[12, 12]}>
          <Image.PreviewGroup>
            {cameraFeeds.map(({ title, topicName, messageType }, index) => (
              <CameraFeed
                key={index}
                arrayIndex={index}
                topicName={topicName}
                title={title}
                messageType={messageType}
              />
            ))}
          </Image.PreviewGroup>
        </Row>

        {/* Camera Controls */}
        <Header title="Camera Controls" icon={<FileAddOutlined />} />
        <CameraControls
          cameraTopics={cameraFeeds.map(({ topicName }) => topicName)}
        />

        {/* Navigation */}
        <Header title="Navigation" icon={<CompassOutlined />} />
        <Navigation />

        {/* Sensors */}
        <Header title="Sensors" icon={<WifiOutlined />} />
        <LifeDetectionCharts />

        {/* ROS Debug Information */}
        <Header title="ROS Debug Information" icon={<InfoCircleOutlined />} />
        <Row gutter={[12, 12]}>
          <Col md={24} lg={12}>
            <TopicsPanel />
          </Col>
          <Col md={24} lg={12}>
            <ParamsPanel />
          </Col>
          <Col span={24}>
            <NodesPanel />
          </Col>
          <Col span={24}>
            <ServicesPanel />
          </Col>
        </Row>
      </Layout>

      {/* Modals */}
      <AddCameraFeedModal
        visible={addCameraModalVisible}
        setVisible={setAddCameraModalVisible}
      />
    </>
  );
};

export default Overview;
