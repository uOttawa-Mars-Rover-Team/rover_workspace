import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { useState, useEffect, useContext } from "react";
import { DownloadOutlined } from "@ant-design/icons";
import { Button, Col, Form, Input, Row, Space } from "antd";
import ROSLIB from "roslib";
import { RosContext } from "../../contexts";

interface Datapoint {
  name: Date;
  value: Number;
}
type DatapointAccessorFunction = (message: string) => Datapoint;
interface TopicLineChartProps {
  messageDatapointAccessor: DatapointAccessorFunction;
  dataLabel: string;
  defaultTopicName?: string;
  stroke?: string;
}
interface CustomTooltipProps {
  active: boolean;
  payload: Array<Datapoint>;
  label: String | Date;
  dataLabel: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
  dataLabel,
}) => {
  if (active && label && payload && payload.length) {
    return (
      <div>
        <h3>{dataLabel}</h3>
        <p>
          {label.toLocaleString()}: {payload[0].value}
        </p>
      </div>
    );
  } else {
    return (
      <>
        <b>No data</b>
      </>
    );
  }
};

const TopicLineChart: React.FC<TopicLineChartProps> = ({
  messageDatapointAccessor,
  dataLabel,
  defaultTopicName = "",
  stroke = "#0b7385",
}) => {
  const [topicName, setTopicName] = useState(defaultTopicName);
  const [data, setData] = useState<Array<Datapoint>>([]);
  const { rosClient } = useContext(RosContext);
  // The ROS message type is assumed to be a string (with a JSON format). The messageDatapointAccessor
  // function will return the datapoint from the ROS message received according to the structure of the
  // JSON received (if it's not already in the format of Datapoint).
  const messageType = "std_msgs/String";
  const initialCsvHref: string =
    "data:text/csv;charset=utf-8," + encodeURIComponent("Date,Value\n");
  const [csvHref, setCsvHref] = useState<string>(initialCsvHref);

  useEffect(() => {
    if (rosClient) {
      let topic = new ROSLIB.Topic({
        ros: rosClient!,
        name: topicName,
        messageType,
      });

      topic.subscribe((message) => {
        // @ts-ignore
        const newDatapoint = messageDatapointAccessor(message.data);
        setData([...data, newDatapoint]);
        const newLine = encodeURIComponent(
          newDatapoint.name + "," + newDatapoint.value + "\n"
        );
        setCsvHref((c) => c + newLine);
      });

      return () => {
        topic.unsubscribe();
      };
    }
  }, [data, messageDatapointAccessor, topicName, messageType, rosClient]);

  return (
    <>
      <Form layout="vertical">
        <Form.Item label="ROS Topic Name">
          <Input
            value={topicName}
            onChange={(e) => {
              setTopicName(e.target.value);
            }}
          />
        </Form.Item>
      </Form>
      <Space
        direction="horizontal"
        style={{ width: "100%", justifyContent: "center" }}
      ></Space>
      <ResponsiveContainer width="100%" height={500}>
        <LineChart
          data={data}
          margin={{
            right: 30,
            bottom: 5,
          }}
        >
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey={() => {
              return data.length
                ? typeof data[0].name === "string"
                  ? data[0].name
                  : data[0].name.toLocaleDateString()
                : null;
            }}
            padding={{ left: 30, right: 30 }}
          />
          <YAxis />
          {/* 
            // @ts-ignore */}
          <Tooltip content={<CustomTooltip dataLabel={dataLabel} />} />
          <Legend />
          <Line
            type="linear"
            dataKey="value"
            name={dataLabel}
            stroke={stroke}
          />
        </LineChart>
      </ResponsiveContainer>
      <Row gutter={[12, 12]}>
        <Col>
          <Button
            type="primary"
            danger
            onClick={() => {
              setData([]);
              setCsvHref(initialCsvHref);
            }}
          >
            Reset Data
          </Button>
        </Col>
        <Col>
          <Button href={csvHref} target="_blank" download={`${dataLabel}.csv`}>
            <DownloadOutlined />
            Download .CSV
          </Button>
        </Col>
      </Row>
    </>
  );
};

export default TopicLineChart;
