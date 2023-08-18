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
import {
  CreatePanoramaRequest,
  SaveImageRequest,
  CreatePanoramaResponse,
  SaveImageResponse,
} from "./interfaces";

type CameraControlsProps = {
  cameraTopics: string[];
};
type VideoNodeRequest = CreatePanoramaRequest | SaveImageRequest;
type VideoNodeResponse = CreatePanoramaResponse | SaveImageResponse;

const CameraControls: React.FC<CameraControlsProps> = ({ cameraTopics }) => {
  // ROS Client
  const ROSClient = useContext(RosContext).rosClient;
  const [rosClient, setRosClient] = useState(ROSClient);
  useEffect(() => {
    if (ROSClient) {
      setRosClient(ROSClient);
    }
  }, [ROSClient]);

  const cameraTopicOptions = cameraTopics.map((cameraTopic) => ({
    value: cameraTopic,
    label: cameraTopic,
  }));
  const defaultSaveImageRequestState: SaveImageRequest = {
    image_topic: "",
    path: "",
    create_path: false,
  };

  // Picture node
  const [pictureControlConfig, setPictureControlConfig] =
    useState<SaveImageRequest>(defaultSaveImageRequestState);
  // Panorama node
  const [panoramaPath, setPanoramaPath] = useState("");
  // Video node
  const [videoControlConfig, setVideoControlConfig] =
    useState<SaveImageRequest>(defaultSaveImageRequestState);

  // Common functions
  const validatePath = (path: string) => {
    if (path.trim() === "" || !path.includes("/")) {
      notification.error({
        message: "Error: path is invalid!",
      });
      return false;
    }
    return true;
  };
  const useService = (
    serviceName: string,
    serviceType: string,
    serviceContent: VideoNodeRequest
  ) => {
    if (!rosClient) {
      notification.error({
        message: "Error: unable to use ROS client!",
      });
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
      (response: VideoNodeResponse) => {
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

  return (
    <Row gutter={[12, 12]} justify="center">
      {/* Picture Node Controls */}
      <CameraControlsWrapper header="Picture Node">
        <Descriptions bordered size="small" layout="vertical">
          <Descriptions.Item label={<b>ROS Topic Name</b>} span={24}>
            <Select
              value={pictureControlConfig.image_topic}
              options={cameraTopicOptions}
              showSearch
              style={{ width: "100%" }}
              onChange={(newValue: string) => {
                setPictureControlConfig({
                  ...pictureControlConfig,
                  image_topic: newValue,
                });
              }}
            />
          </Descriptions.Item>
          <Descriptions.Item label={<b>File Write Path</b>} span={24}>
            <Input
              value={pictureControlConfig.path}
              placeholder="Enter an absolute path to save an image to"
              onChange={(e) => {
                setPictureControlConfig({
                  ...pictureControlConfig,
                  path: e.target.value,
                });
              }}
            />
          </Descriptions.Item>
        </Descriptions>
        <Row style={{ padding: 10 }} justify="space-between" align="middle">
          <Col>
            <Button
              type="primary"
              onClick={() => {
                if (validatePath(pictureControlConfig.path)) {
                  useService(
                    config.overview.cameraControls.picture.serviceName,
                    "general_interfaces/srv/SaveImage",
                    pictureControlConfig
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
                checked={pictureControlConfig.create_path}
                onChange={() => {
                  setPictureControlConfig({
                    ...pictureControlConfig,
                    create_path: !pictureControlConfig.create_path,
                  });
                }}
              />
            </Space>
          </Col>
        </Row>
      </CameraControlsWrapper>

      {/* Panorama Node Controls */}
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
              }
            }}
          >
            Stitch
          </Button>
        </Row>
      </CameraControlsWrapper>

      {/* Video Node Controls */}
      <CameraControlsWrapper header="Video Node">
        <Descriptions bordered size="small" layout="vertical">
          <Descriptions.Item label={<b>ROS Topic Name</b>} span={24}>
            <Select
              value={videoControlConfig.image_topic}
              options={cameraTopicOptions}
              showSearch
              style={{ width: "100%" }}
              onChange={(newValue: string) => {
                setVideoControlConfig({
                  ...videoControlConfig,
                  image_topic: newValue,
                });
              }}
            />
          </Descriptions.Item>
          <Descriptions.Item label={<b>File Write Path</b>} span={24}>
            <Input
              value={videoControlConfig.path}
              placeholder="Enter an absolute path"
              onChange={(e) => {
                setVideoControlConfig({
                  ...videoControlConfig,
                  path: e.target.value,
                });
              }}
            />
          </Descriptions.Item>
        </Descriptions>
        <Row style={{ padding: 10 }} justify="space-between">
          <Space>
            <Button
              danger
              onClick={() => {
                const data = {
                  ...videoControlConfig,
                  path: "*",
                };
                useService(
                  config.overview.cameraControls.video.serviceName.stop,
                  "general_interfaces/srv/SaveImage",
                  data
                );
              }}
            >
              Stop all
            </Button>
            <Button
              danger
              onClick={() => {
                if (validatePath(videoControlConfig.path)) {
                  useService(
                    config.overview.cameraControls.video.serviceName.stop,
                    "general_interfaces/srv/SaveImage",
                    videoControlConfig
                  );
                }
              }}
            >
              Stop
            </Button>
          </Space>
          <Space>
            <Space>
              <b>Create path</b>
              <Switch
                checked={videoControlConfig.create_path}
                onChange={() => {
                  setVideoControlConfig({
                    ...videoControlConfig,
                    create_path: !videoControlConfig.create_path,
                  });
                }}
              />
            </Space>
            <Button
              type="primary"
              onClick={() => {
                if (validatePath(videoControlConfig.path)) {
                  useService(
                    config.overview.cameraControls.video.serviceName.start,
                    "general_interfaces/srv/SaveImage",
                    videoControlConfig
                  );
                }
              }}
            >
              Start
            </Button>
          </Space>
        </Row>
      </CameraControlsWrapper>
    </Row>
  );
};

export default CameraControls;
