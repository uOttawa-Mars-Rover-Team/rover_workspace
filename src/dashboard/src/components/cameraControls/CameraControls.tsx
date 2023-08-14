import {
  Button,
  Col,
  Descriptions,
  Input,
  Row,
  Select,
  Space,
  Switch,
  notification,
} from "antd";
import CameraControlsWrapper from "./CameraControlsWrapper";
import { useContext, useEffect, useState } from "react";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import * as config from "../../dashboardConfig.json";

type CameraControlsProps = {
  cameraTopics: string[];
};

const CameraControls: React.FC<CameraControlsProps> = ({ cameraTopics }) => {
  const ROSClient = useContext(RosContext).rosClient;
  const [rosClient, setRosClient] = useState(ROSClient);

  const cameraTopicOptions = cameraTopics.map((cameraTopic) => ({
    value: cameraTopic,
    label: cameraTopic,
  }));
  const defaultTopic = "";
  const initPath = "";

  // Picture node
  const [pictureTopic, setPictureTopic] = useState(defaultTopic);
  const [pictureWritePath, setPictureWritePath] = useState(initPath);
  const [pictureCreatePath, setPictureCreatePath] = useState(false);
  // Panorama node
  const [panoramaPath, setPanoramaPath] = useState(initPath);
  // Video node
  const [videoTopic, setVideoTopic] = useState(defaultTopic);
  const [videoWritePath, setVideoWritePath] = useState(initPath);

  useEffect(() => {
    if (ROSClient) {
      setRosClient(ROSClient);
    }
  }, [ROSClient]);

  const useService = (
    serviceName: string,
    serviceType: string,
    serviceContent: object
  ) => {
    if (!rosClient) {
      return;
    }
    const service = new ROSLIB.Service({
      ros: rosClient,
      name: serviceName,
      serviceType: serviceType,
    });
    const request = new ROSLIB.ServiceRequest(serviceContent);
    service.callService(
      request,
      (response: object) => {
        const notificationData = {
          message: `Service request to ${serviceName} ${
            response.status ? "succeeded" : "failed"
          }.`,
          description: response.message,
        };
        response.status
          ? notification.success(notificationData)
          : notification.error(notificationData);
      },
      (error) => {
        notification.error({
          message: `ROS Error (${serviceName}).`,
          description: error,
        });
      }
    );
  };

  const publishMessage = (
    topicName: string,
    messageType: string,
    messageContent: object
  ) => {
    if (!rosClient) {
      return;
    }
    const topic = new ROSLIB.Topic({
      ros: rosClient,
      name: topicName,
      messageType: messageType,
    });
    const message = new ROSLIB.Message(messageContent);
    topic.publish(message);
  };

  const validatePath = (path: string) => {
    if (path.trim() === "" || !path.includes("/")) {
      return false;
    }
    return true;
  };

  const startLabel = "START";
  const stopLabel = "STOP";
  const [videoActionState, setVideoActionState] = useState<
    typeof startLabel | typeof stopLabel
  >(startLabel);

  return (
    <Row gutter={[12, 12]} justify="center">
      {/* Picture Node */}
      <CameraControlsWrapper header="Picture Node">
        <Descriptions bordered size="small" layout="vertical">
          <Descriptions.Item label={<b>ROS Topic Name</b>} span={24}>
            <Select
              value={pictureTopic}
              options={cameraTopicOptions}
              showSearch
              style={{ width: "100%" }}
              onChange={(newValue: string) => {
                setPictureTopic(newValue);
              }}
            />
          </Descriptions.Item>
          <Descriptions.Item label={<b>File Write Path</b>} span={24}>
            <Input
              value={pictureWritePath}
              placeholder="Enter an absolute path"
              onChange={(e) => {
                setPictureWritePath(e.target.value);
              }}
            />
          </Descriptions.Item>
        </Descriptions>
        <Row style={{ padding: 10 }} justify="space-between" align="middle">
          <Col>
            <Button
              type="primary"
              onClick={() => {
                if (validatePath(pictureWritePath)) {
                  const data = {
                    image_topic: pictureTopic,
                    path: pictureWritePath,
                    create_path: pictureCreatePath,
                  };
                  useService(
                    config.overview.cameraControls.picture.serviceName,
                    "general_interfaces/srv/SaveImage",
                    data
                  );
                }
              }}
            >
              Save
            </Button>
          </Col>
          <Col>
            <Space>
              <b>Create path</b>
              <Switch
                checked={pictureCreatePath}
                onChange={() => setPictureCreatePath(!pictureCreatePath)}
              />
            </Space>
          </Col>
        </Row>
      </CameraControlsWrapper>

      {/* Panorama Node */}
      <CameraControlsWrapper header="Panorama Node">
        <Descriptions bordered size="small" layout="vertical">
          <Descriptions.Item label={<b>Panorama Location</b>} span={24}>
            <Input
              value={panoramaPath}
              placeholder="Enter an absolute path to stitch panorama images from"
              onChange={(e) => {
                setPanoramaPath(e.target.value);
              }}
            />
          </Descriptions.Item>
        </Descriptions>
        <Row style={{ padding: 10 }}>
          <Button
            type="primary"
            onClick={() => {
              if (validatePath(panoramaPath)) {
                const data = {
                  path: panoramaPath,
                };
                useService(
                  config.overview.cameraControls.panorama.serviceName,
                  "general_interfaces/srv/CreatePanorama",
                  data
                );
                console.log("WOWO");
              }
            }}
          >
            Stitch
          </Button>
        </Row>
      </CameraControlsWrapper>

      {/* Video Node */}
      <CameraControlsWrapper header="Video Node">
        <Descriptions bordered size="small" layout="vertical">
          <Descriptions.Item label={<b>Action</b>} span={24}>
            <Select
              value={videoActionState}
              options={[
                { value: startLabel, label: startLabel },
                { value: stopLabel, label: stopLabel },
              ]}
              style={{ width: "100%" }}
              onChange={(newValue) => {
                setVideoActionState(newValue);
              }}
            />
          </Descriptions.Item>
          <Descriptions.Item label={<b>ROS Topic Name</b>} span={24}>
            <Select
              value={videoTopic}
              options={cameraTopicOptions}
              showSearch
              style={{ width: "100%" }}
              onChange={(newValue: string) => {
                setVideoTopic(newValue);
              }}
            />
          </Descriptions.Item>
          <Descriptions.Item label={<b>File Write Path</b>} span={24}>
            <Input
              disabled={videoActionState === "STOP"}
              value={videoWritePath}
              placeholder="Enter an absolute path"
              onChange={(e) => {
                setVideoWritePath(e.target.value);
              }}
            />
          </Descriptions.Item>
        </Descriptions>
        <Row style={{ padding: 10 }} justify="space-between">
          <Button
            disabled={videoActionState === "START"}
            danger
            onClick={() => {
              if (validatePath(videoWritePath)) {
                const data = {
                  action: "STOP",
                  imageTopic: videoTopic,
                };
                publishMessage(
                  config.overview.cameraControls.video.topicName,
                  "std_msgs/String",
                  {
                    data: JSON.stringify(data),
                  }
                );
              }
            }}
          >
            Stop
          </Button>
          <Button
            disabled={videoActionState === "STOP"}
            type="primary"
            onClick={() => {
              if (validatePath(videoWritePath)) {
                const data = {
                  action: "START",
                  path: videoWritePath,
                  imageTopic: videoTopic,
                };
                publishMessage(
                  config.overview.cameraControls.video.topicName,
                  "std_msgs/String",
                  {
                    data: JSON.stringify(data),
                  }
                );
              }
            }}
          >
            Start
          </Button>
        </Row>
      </CameraControlsWrapper>
    </Row>
  );
};

export default CameraControls;
