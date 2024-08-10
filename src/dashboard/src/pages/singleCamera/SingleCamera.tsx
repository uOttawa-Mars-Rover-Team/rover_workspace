import { Image, Row} from "antd";
import {
  CameraOutlined,
} from "@ant-design/icons";
import { useContext} from "react";
import { Helmet } from "react-helmet";

import {
  Layout,
  CameraFeed,
  Header,
} from "../../components";
import { DashboardContext } from "../../contexts";
import { useLocation } from 'react-router-dom';

const SingleCamera: React.FC = () => {
  const { cameraFeeds } = useContext(DashboardContext);
  const location = useLocation();
  const cameraIndex = location.state.key;

  const selectedCamera = cameraFeeds[cameraIndex];

  return (
    <>
      <Helmet>
        <title>rDash - {selectedCamera.title}</title>
      </Helmet>
      <Layout title={selectedCamera.title} menuKey="camera">
        <Header
          title={selectedCamera.title}
          icon={<CameraOutlined />}
          style={{ paddingTop: 0 }}
        />
        <Row gutter={[12, 12]} justify="center" align="middle">
          <Image.PreviewGroup>
            {
                <CameraFeed
                key={cameraIndex}
                arrayIndex={cameraIndex}
                topicName={selectedCamera.topicName}
                title={selectedCamera.title}
                messageType={selectedCamera.messageType}
                singleCamera= {true}
                />
            }
          </Image.PreviewGroup>
        </Row>
      </Layout>
    </>
  );
};

export default SingleCamera;
