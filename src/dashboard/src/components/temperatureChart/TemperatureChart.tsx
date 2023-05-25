import { Form, Input } from "antd";
import TopicLineChart from "../topicLineChart/TopicLineChart";
import { useState } from "react";

interface messageString {
  name: number;
  value: Number;
}
interface Datapoint {
  name: Date;
  value: Number;
}

const TemperatureChart: React.FC = () => {
  const [topicName, setTopicName] = useState("");
  const messageDatapointAccessor = (message: string) => {
    const parsedMessage: messageString = JSON.parse(message);
    // Convert the UNIX timestamp in the ROS message to a Javascript date
    const datapointDate: Date = new Date(parsedMessage.name * 1000);
    const datapoint: Datapoint = {
      name: datapointDate,
      value: parsedMessage.value,
    };
    return datapoint;
  };

  return (
    <>
      <h2>Temperature Sensor</h2>
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
      <TopicLineChart
        topicName={topicName}
        messageDatapointAccessor={messageDatapointAccessor}
        dataName="Temperature"
      />
    </>
  );
};

export default TemperatureChart;
