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
import { Button, Space } from "antd";
import ROSLIB from "roslib";
import { RosContext } from "../../contexts";

interface Datapoint {
  name: Date;
  value: Number;
}
type DatapointAccessorFunction = (message: string) => Datapoint;
interface TopicLineChartProps {
  topicName: string;
  messageDatapointAccessor: DatapointAccessorFunction;
  dataName: string;
  stroke?: string;
}
interface CustomTooltipProps {
  active: boolean;
  payload: Array<Datapoint>;
  label: String | Date;
  dataName: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
  dataName,
}) => {
  if (active && label && payload && payload.length) {
    return (
      <div>
        <h3>{dataName}</h3>
        <p>
          {label.toLocaleString()}: {payload[0].value.toString()}
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
  topicName,
  messageDatapointAccessor,
  dataName,
  stroke = "#0b7385",
}) => {
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
      <Space
        direction="horizontal"
        style={{ width: "100%", justifyContent: "center" }}
      >
        <h2>{!data.length && "No Data"}</h2>
      </Space>
      <ResponsiveContainer width="100%" height={500}>
        <LineChart
          width={500}
          height={300}
          data={data}
          margin={{
            right: 30,
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
          <Tooltip content={<CustomTooltip dataName={dataName} />} />
          <Legend />
          <Line type="linear" dataKey="value" name={dataName} stroke={stroke} />
        </LineChart>
      </ResponsiveContainer>
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
      <Button href={csvHref} target="_blank" download={`${dataName}.csv`}>
        <DownloadOutlined />
        Download .CSV
      </Button>
    </>
  );
};

export default TopicLineChart;
