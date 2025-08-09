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
import {
  EditOutlined,
  SaveOutlined,
  DeleteOutlined,
  PauseCircleOutlined,
  CameraOutlined,
  VideoCameraOutlined,
  PictureOutlined,
  PlayCircleOutlined,
  ExportOutlined,
} from "@ant-design/icons";
import React, { useContext, useEffect, useState } from "react";
import ROSLIB from "roslib";

import CopiableTag from "../copiableTag/CopiableTag";
import { DashboardContext, RosContext } from "../../contexts";
import { useNavigate } from "react-router-dom";

interface CameraFeedProps {
  arrayIndex: number;
  topicName: string;
  title: string;
  messageType: string;
  singleCamera?: false | boolean;
  cameraModifiers: string;
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
  singleCamera,
  cameraModifiers,
}) => {
  const [edit, setEdit] = useState(false);
  const [cameraState, setCameraState] = useState<CameraState>(
    CameraState.Disconnected
  );

  const { removeCameraFeed, editCameraFeed } = useContext(DashboardContext);
  const { rosClient } = useContext(RosContext);
  const [image, setImage] = useState("");

  const [cameraRefresh, setCameraRefresh] = useState(true);
  const navigate = useNavigate();

  //video feed const
  const videoParams =
    "/image_raw&default_transport=compressed&qos_profile=sensor_data";

  // Function to download current image displayed in feed. Image is saved in default browser download folder.
  const onDownload = () => {
    const d = new Date();
    const formattedDate = `${d.getFullYear()}-${
      d.getMonth() + 1
    }-${d.getDay()} ${d.getHours()}-${d.getMinutes()}-${d.getSeconds()}`;
    //fetch(image)
    //fetch("http://localhost:8080/snapshot?topic=/usb_cam/image_raw")
    fetch(
      topicName +
        "snapshot?topic=/" +
        messageType +
        videoParams +
        cameraModifiers
    )
      .then((response) => response.blob())
      .then((blob) => {
        const url = URL.createObjectURL(new Blob([blob]));
        const link = document.createElement("a");
        link.href = url;
        link.download = `${title} ${formattedDate}.png`;
        document.body.appendChild(link);
        link.click();
        URL.revokeObjectURL(url);
        link.remove();
      });
  };

  useEffect(() => {
    console.log("in useEffect");
    //setImage("http://localhost:8080/stream?topic=/usb_cam/image_raw");
    //console.log(topicName + "stream?topic=" + messageType);
    console.log(image);

    setImage(
      topicName +
        "stream?topic=/" +
        messageType +
        "" +
        videoParams +
        cameraModifiers
    );

    if (rosClient && cameraRefresh) {
      setCameraState(CameraState.Connected);

      //setCameraState(CameraState.Connecting);
      const topic = new ROSLIB.Topic({
        ros: rosClient!,
        name: topicName,
        messageType,
      });

      topic.subscribe((message) => {
        setCameraState(CameraState.Connected);
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        //setImage("data:image/jpg;base64," + message.data);
        //setImage("http://localhost:8080/stream?topic=/usb_cam/image_raw");
        //console.log(topicName + "stream?topic=" + messageType);
        // setImage(
        //   topicName +
        //     "stream?topic=/" +
        //     messageType +
        //     videoParams +
        //     cameraModifiers
        // );
        //setImage(topicName);
      });

      return () => {
        setCameraState(CameraState.Disconnected);
        topic.unsubscribe();
      };
    }
    //setImage("http://localhost:8080/stream?topic=/usb_cam/image_raw");
  }, [topicName, messageType, rosClient, cameraRefresh, cameraModifiers]);

  const itemsNest: CollapseProps["items"] = [
    // {
    //   key: "1",
    //   label: "ROS Details",
    //   children: (
    //     <Descriptions bordered size="small" layout="vertical" column={1}>
    //       <Descriptions.Item label={<b>ROS Topic Name</b>}>
    //         <CopiableTag name={topicName} />
    //       </Descriptions.Item>
    //       <Descriptions.Item label={<b>ROS Message Type</b>}>
    //         <CopiableTag name={messageType} />
    //       </Descriptions.Item>
    //     </Descriptions>
    //   ),
    // },
    {
      key: "1",
      label: "Camera Details",
      children: (
        <Descriptions bordered size="small" layout="vertical" column={1}>
          <Descriptions.Item label={<b>Camera Server URL</b>}>
            <CopiableTag name={topicName} />
          </Descriptions.Item>
          <Descriptions.Item label={<b>Camera Topic</b>}>
            <CopiableTag name={messageType} />
          </Descriptions.Item>
          <Descriptions.Item label={<b>Camera Modifiers</b>}>
            <CopiableTag name={cameraModifiers} />
          </Descriptions.Item>
        </Descriptions>
      ),
    },
  ];

  const cameraFeedItems: CollapseProps["items"] = [
    {
      key: "1",
      label: edit ? (
        <>
          <b>Editing Camera Feed</b>
          <Form
            layout="vertical"
            onFinish={({ title, topicName, messageType, cameraModifiers }) => {
              editCameraFeed(
                { title, topicName, messageType, cameraModifiers },
                arrayIndex
              );
              setEdit(false);
            }}
            initialValues={{ title, topicName, messageType, cameraModifiers }}
            style={{ marginTop: 12 }}
            onClick={(e) => e.stopPropagation()}
          >
            <Form.Item label="Camera Title" name="title">
              <Input />
            </Form.Item>
            <Form.Item label="Video Server URL" name="topicName">
              <Input />
            </Form.Item>
            <Form.Item label="Camera Topic" name="messageType">
              <Input />
            </Form.Item>
            <Form.Item label="Camera Modifiers" name="cameraModifiers">
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
        <div>
          <a
            onClick={(e) => {
              e.stopPropagation();
              console.log("PictureOutlined");
            }}
            style={{ marginRight: 12 }}
          >
            <PictureOutlined />
          </a>

          <a
            onClick={(e) => {
              e.stopPropagation();
              console.log("Camera");
              onDownload();
            }}
            style={{ marginRight: 12 }}
          >
            <CameraOutlined />
          </a>

          <a
            onClick={(e) => {
              e.stopPropagation();
              console.log("Video Camera");
            }}
            style={{ marginRight: 12 }}
          >
            <VideoCameraOutlined />
          </a>

          <a
            onClick={(e) => {
              e.stopPropagation();
              setCameraRefresh(!cameraRefresh);
            }}
            style={{ marginRight: 12 }}
          >
            {cameraRefresh ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
          </a>

          {!singleCamera && (
            <a
              onClick={(e) => {
                e.stopPropagation();
                const cameraIndex = arrayIndex;
                navigate("/camera/singleCamera", {
                  state: { key: `${cameraIndex}` },
                });
              }}
              style={{ marginRight: 12 }}
            >
              <ExportOutlined />
            </a>
          )}
          <a
            onClick={(e) => {
              e.stopPropagation();
              setEdit((prev) => !prev);
            }}
          >
            <EditOutlined /> Edit
          </a>
        </div>
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
            <Image src={image} height="100%" width="100%" />
          )}
          {cameraState === CameraState.Error && (
            <Result
              status="error"
              title="Error connecting to video feed"
              subTitle="Make sure everything is running."
            />
          )}
          <Collapse items={itemsNest} style={{ margin: 10 }} />
        </>
      ),
    },
  ];

  return (
    <>
      {singleCamera ? (
        <Col sm={24} lg={12} xl={12} xxl={12}>
          <Collapse items={cameraFeedItems} defaultActiveKey={["1"]} />
        </Col>
      ) : (
        <Col sm={24} lg={12} xl={8} xxl={6}>
          <Collapse items={cameraFeedItems} defaultActiveKey={["1"]} />
        </Col>
      )}
    </>
  );
};

export default CameraFeed;
