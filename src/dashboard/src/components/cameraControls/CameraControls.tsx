import { Button, Descriptions, Input, Row, Select } from "antd";
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

  const [pictureTopic, setPictureTopic] = useState(defaultTopic);
  const [pictureWritePath, setPictureWritePath] = useState(initPath);

  useEffect(() => {
    if (ROSClient) {
      setRosClient(ROSClient);
    }
  }, [ROSClient]);

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

  const [panoramaPath, setPanoramaPath] = useState(initPath);

  const [videoTopic, setVideoTopic] = useState(defaultTopic);
  const [videoWritePath, setVideoWritePath] = useState(initPath);

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
        <Row style={{ padding: 10 }}>
          <Button
            type="primary"
            onClick={() => {
              if (validatePath(pictureWritePath)) {
                const data = {
                  imageTopic: pictureTopic,
                  path: pictureWritePath,
                };
                publishMessage(
                  config.overview.cameraControls.picture.topicName,
                  "std_msgs/String",
                  {
                    data: JSON.stringify(data),
                  }
                );
              }
            }}
          >
            Save
          </Button>
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
                publishMessage(
                  config.overview.cameraControls.panorama.topicName,
                  "std_msgs/String",
                  {
                    data: JSON.stringify(data),
                  }
                );
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
