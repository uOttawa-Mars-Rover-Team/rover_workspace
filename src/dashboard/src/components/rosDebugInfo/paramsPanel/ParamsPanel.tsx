import { useContext, useState } from "react";
import {
  Button,
  Input,
  notification,
  Collapse,
  Form,
  Col,
  Row,
  Popover,
  Tag,
  CollapseProps,
} from "antd";
import { DeleteOutlined, EditOutlined, SaveOutlined } from "@ant-design/icons";

import { useParams } from "../../../hooks";
import CopiableTag from "../../copiableTag/CopiableTag";
import CustomTable from "../CustomTable";
import { RosContext, DashboardContext } from "../../../contexts";
import { deleteParam, setParam } from "../../../utils/ros";
import { stringColumnSorter } from "../../../utils/table";

const notificationMessageHelper = (message: string, name: string) => (
  <Row align="middle" gutter={12}>
    <Col>{message}</Col>
    <Tag>{name}</Tag>
  </Row>
);

const ParamsPanel: React.FC = () => {
  const { autoRefresh } = useContext(DashboardContext);
  const [shouldRefresh, setShouldRefresh] = useState<boolean>(
    autoRefresh.params
  );
  const { params, lastRefreshed } = useParams(shouldRefresh);
  const { rosClient } = useContext(RosContext);

  const deleteOnClick = async (name: string) => {
    try {
      await deleteParam(rosClient!, name);
      notification.success({
        message: notificationMessageHelper("Successfully deleted param", name),
      });
    } catch (e) {
      notification.error({
        message: notificationMessageHelper("Error deleting param", name),
      });
    }
  };

  const addParamOnFinish = async ({ name, value }: any) => {
    try {
      await setParam(rosClient!, name, value);
      notification.success({
        message: notificationMessageHelper("Successfully created param", name),
      });
    } catch (e) {
      notification.error({
        message: notificationMessageHelper("Error creating param", name),
      });
    }
  };

  const editParamOnFinish = async (value: string, name: string) => {
    try {
      await setParam(rosClient!, name, value);
      notification.success({
        message: notificationMessageHelper("Successfully modified param", name),
      });
    } catch (e) {
      notification.error({
        message: notificationMessageHelper("Error modifying param", name),
      });
    }
  };

  const collapseItems: CollapseProps["items"] = [
    {
      key: "1",
      label: <b>Add Param</b>,
      children: (
        <Form
          layout="vertical"
          style={{ padding: 12 }}
          onFinish={addParamOnFinish}
        >
          <Row gutter={[12, 12]}>
            <Col span={12}>
              <Form.Item
                label="Name"
                name="name"
                rules={[
                  { required: true, message: "Need to provide param name" },
                ]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Value"
                name="value"
                rules={[
                  {
                    required: true,
                    message: "Need to provide param value",
                  },
                ]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          <Row justify="end">
            <Button htmlType="submit" type="primary">
              <SaveOutlined /> Save
            </Button>
          </Row>
        </Form>
      ),
    },
  ];

  return (
    <CustomTable
      columns={[
        {
          dataIndex: "name",
          title: "Name",
          render: (type) => <CopiableTag name={type} />,
          sorter: stringColumnSorter("name"),
        },
        {
          dataIndex: "value",
          title: "Param Value",
          render: (value) => <CopiableTag name={value} />,
          sorter: stringColumnSorter("value"),
        },
        {
          title: "Edit",
          fixed: "right",
          width: 50,
          render: (_, param) => (
            <Popover
              content={
                <Form
                  layout="vertical"
                  initialValues={{ value: param.value }}
                  onFinish={({ value }) => editParamOnFinish(value, param.name)}
                >
                  <Form.Item label="Value" name="value">
                    <Input />
                  </Form.Item>
                  <Row justify="end">
                    <Button htmlType="submit" type="primary">
                      <SaveOutlined /> Save
                    </Button>
                  </Row>
                </Form>
              }
              title={
                <>
                  Edit param value for
                  <Tag style={{ marginLeft: 3 }}>{param.name}</Tag>
                </>
              }
              trigger="click"
            >
              <Button
                icon={<EditOutlined />}
                shape="circle"
                onClick={() => {}}
                size="small"
              />
            </Popover>
          ),
        },
        {
          title: "Delete",
          fixed: "right",
          width: 70,
          render: (_, param) => (
            <Button
              icon={<DeleteOutlined />}
              shape="circle"
              danger
              onClick={() => deleteOnClick(param.name)}
              size="small"
            />
          ),
        },
      ]}
      scroll={{ x: 800 }}
      data={params}
      lastRefreshed={lastRefreshed}
      title="Params"
      shouldRefresh={shouldRefresh}
      setShouldRefresh={setShouldRefresh}
    >
      <div style={{ padding: 12, paddingTop: params.length === 0 ? 12 : 0 }}>
        <Collapse items={collapseItems} bordered={true} />
      </div>
    </CustomTable>
  );
};

export default ParamsPanel;
