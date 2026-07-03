import { useContext } from "react";
import { Form, Modal, Input } from "antd";

import { DashboardContext } from "../../contexts";

interface AddCameraFeedModalProps {
  visible: boolean;
  setVisible: React.Dispatch<React.SetStateAction<boolean>>;
}

const AddCameraFeedModal: React.FC<AddCameraFeedModalProps> = ({
  visible,
  setVisible,
}) => {
  const { addCameraFeed } = useContext(DashboardContext);
  const [form] = Form.useForm();

  const dismissModal = () => setVisible(false);

  const formOnFinish = ({
    title,
    topicName,
    messageType,
    cameraModifiers,
  }: {
    title: string;
    topicName: string;
    messageType: string;
    cameraModifiers: string;
  }) => {
    addCameraFeed({ title, topicName, messageType, cameraModifiers });
    dismissModal();
    form.resetFields();
  };

  return (
    <Modal
      open={visible}
      onCancel={dismissModal}
      title="Add Camera Feed"
      closable={false}
      onOk={form.submit}
    >
      <Form form={form} layout="vertical" onFinish={formOnFinish}>
        <Form.Item
          label="Camera Title"
          name="title"
          rules={[{ required: true, message: "Need to provide camera title" }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          label="Camera Server URL"
          name="topicName"
          rules={[
            { required: true, message: "Need to provide camera server URL" },
          ]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          label="Camera Topic"
          name="messageType"
          rules={[{ required: true, message: "Need to provide camera topic" }]}
        >
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default AddCameraFeedModal;
