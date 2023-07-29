import {
  Descriptions,
  Image,
  Col,
  Input,
  Button,
  Form,
  Collapse,
  Row,
  Badge,
  Tooltip,
  Skeleton,
  Spin,
  Result,
  CollapseProps,
} from "antd";
import { EditOutlined, SaveOutlined, DeleteOutlined } from "@ant-design/icons";
import React, { useContext, useEffect, useState } from "react";
import ROSLIB from "roslib";

import CopiableTag from "../copiableTag/CopiableTag";
import { DashboardContext, RosContext } from "../../contexts";

interface CameraFeedProps {
  arrayIndex: number;
  topicName: string;
  title: string;
  messageType: string;
}

enum CameraState {
  Error = "error",
  Disconnected = "default",
  Connected = "success",
  Connecting = "processing",
}

const cameraStateMessage: { [key in CameraState]: string } = {
  error: "Error",
  default: "Disconnected",
  success: "Connected",
  processing: "Connecting",
};

const CameraFeed: React.FC<CameraFeedProps> = ({
  arrayIndex,
  topicName,
  title,
  messageType,
}) => {
  const [edit, setEdit] = useState(false);
  const [cameraState, setCameraState] = useState<CameraState>(
    CameraState.Disconnected
  );

  const { removeCameraFeed, editCameraFeed } = useContext(DashboardContext);
  const { rosClient } = useContext(RosContext);
  const [image, setImage] = useState("");

  useEffect(() => {
    if (rosClient) {
      if (messageType === "sensor_msgs/Image") {
        setCameraState(CameraState.Connecting);
        setImage(`http://0.0.0.0:8080/stream?topic=${topicName}`);
        setCameraState(CameraState.Connected);

        return () => {
          setCameraState(CameraState.Disconnected);
        };
      } else {
        setCameraState(CameraState.Connecting);
        let topic = new ROSLIB.Topic({
          ros: rosClient!,
          name: topicName,
          messageType,
        });

        topic.subscribe((message) => {
          setCameraState(CameraState.Connected);
          // @ts-ignore
          setImage("data:image/jpg;base64," + message.data);
        });

        return () => {
          setCameraState(CameraState.Disconnected);
          topic.unsubscribe();
        };
      }
    }
  }, [topicName, messageType, rosClient]);

  const cameraFeedItems: CollapseProps["items"] = [
    {
      key: "1",
      label: edit ? (
        <>
          <b>Editing Camera Feed</b>
          <Form
            layout="vertical"
            onFinish={({ title, topicName, messageType }) => {
              editCameraFeed({ title, topicName, messageType }, arrayIndex);
              setEdit(false);
            }}
            initialValues={{ title, topicName, messageType }}
            style={{ marginTop: 12 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Form.Item label="Camera Title" name="title">
              <Input />
            </Form.Item>
            <Form.Item label="ROS Topic Name" name="topicName">
              <Input />
            </Form.Item>
            <Form.Item label="ROS Message Type" name="messageType">
              <Input />
            </Form.Item>

            <Row justify="space-between">
              <Col>
                <Button onClick={() => removeCameraFeed(arrayIndex)} danger>
                  <DeleteOutlined />
                  Remove
                </Button>
              </Col>
              <Row>
                <Col>
                  <Button onClick={() => setEdit(false)}>Cancel</Button>
                </Col>
                <Form.Item style={{ marginBottom: 6, marginLeft: 12 }}>
                  <Button type="primary" htmlType="submit">
                    <SaveOutlined />
                    Save
                  </Button>
                </Form.Item>
              </Row>
            </Row>
          </Form>
        </>
      ) : (
        <>
          <b>{title}</b>
          <Tooltip title={cameraStateMessage[cameraState]}>
            <Badge status={cameraState} style={{ marginLeft: 12 }} />
          </Tooltip>
        </>
      ),
      extra: !edit && (
        // eslint-disable-next-line jsx-a11y/anchor-is-valid
        <a
          onClick={(e) => {
            e.stopPropagation();
            setEdit((prev) => !prev);
          }}
        >
          <EditOutlined /> Edit
        </a>
      ),
      style: { margin: 0, padding: 0 },
      children: (
        <>
          {(cameraState === CameraState.Connecting ||
            (cameraState === CameraState.Connected && !image)) && (
            <Row
              style={{ height: 300, width: "100%" }}
              justify="center"
              align="middle"
            >
              <Spin size="large" tip="Awaiting message response from ROS..." />
            </Row>
          )}
          {cameraState === CameraState.Disconnected && (
            <Skeleton.Image style={{ height: 300, width: "100%" }} />
          )}
          {cameraState === CameraState.Connected && image && (
            <Image src={image} />
          )}
          {cameraState === CameraState.Error && (
            <Result
              status="error"
              title="Error connecting to video feed"
              subTitle="Make sure everything is running."
            />
          )}
          <Descriptions bordered size="small" layout="vertical" column={1}>
            <Descriptions.Item label={<b>ROS Topic Name</b>}>
              <CopiableTag name={topicName} />
            </Descriptions.Item>
            <Descriptions.Item label={<b>ROS Message Type</b>}>
              <CopiableTag name={messageType} />
            </Descriptions.Item>
          </Descriptions>
        </>
      ),
    },
  ];

  return (
    <Col sm={24} lg={12} xl={8} xxl={6}>
      <Collapse items={cameraFeedItems} defaultActiveKey={["1"]} />
    </Col>
  );
};

export default CameraFeed;
