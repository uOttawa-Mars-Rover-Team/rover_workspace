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

  const formOnFinish = ({ title, topicName, messageType }: any) => {
    addCameraFeed({ title, topicName, messageType });
    dismissModal();
    form.resetFields();
  };

  return (
    <Modal
      visible={visible}
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
          label="ROS Topic Name"
          name="topicName"
          rules={[{ required: true, message: "Need to provide topic name" }]}
        >
          <Input />
        </Form.Item>
        <Form.Item
          label="ROS Message Type"
          name="messageType"
          rules={[{ required: true, message: "Need to provide message type" }]}
        >
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default AddCameraFeedModal;
