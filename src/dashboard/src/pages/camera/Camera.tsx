import { Image, Row, Button } from "antd";
import {
  CameraOutlined,
  VideoCameraAddOutlined,
  FileAddOutlined,
} from "@ant-design/icons";
import { useContext, useState } from "react";
import { Helmet } from "react-helmet";

import {
  Layout,
  CameraFeed,
  Header,
  AddCameraFeedModal,
  CameraControls,
} from "../../components";
import { DashboardContext } from "../../contexts";

const Camera: React.FC = () => {
  const [addCameraModalVisible, setAddCameraModalVisible] = useState(false);
  const { cameraFeeds } = useContext(DashboardContext);

  return (
    <>
      <Helmet>
        <title>rDash - Camera</title>
      </Helmet>
      <Layout title="Camera" menuKey="camera">
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

        <Header title="Camera Controls" icon={<FileAddOutlined />} />
        <div style={{ marginBottom: "30px" }}>
          <CameraControls
            cameraTopics={cameraFeeds.map(({ topicName }) => topicName)}
          />
        </div>
      </Layout>

      <AddCameraFeedModal
        visible={addCameraModalVisible}
        setVisible={setAddCameraModalVisible}
      />
    </>
  );
};

export default Camera;
