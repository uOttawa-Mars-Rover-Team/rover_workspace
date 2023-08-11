import { Row, Col } from "antd";
import TopicLineChart from "../topicLineChart/TopicLineChart";
import config from "../../dashboardConfig.json";

interface Datapoint {
  name: Date;
  value: Number;
}

const TemperatureChart: React.FC = () => {
  const messageDatapointAccessorGenerator = (valueIndex: number) => {
    return (message: string) => {
      const values = message.split(";");
      const datapointDate = new Date();
      const datapoint: Datapoint = {
        name: datapointDate,
        value: parseFloat(values[valueIndex]),
      };
      return datapoint;
    };
  };

  return (
    <>
      <Row gutter={[24, 24]}>
        {config.overview.charts.map((value, index) => (
          <Col sm={24} xl={12} xxl={8}>
            <h2>{value.name}</h2>
            <TopicLineChart
              messageDatapointAccessor={messageDatapointAccessorGenerator(
                index
              )}
              dataLabel={value.dataLabel}
              defaultTopicName={value.topicName}
            />
          </Col>
        ))}
      </Row>
    </>
  );
};

export default TemperatureChart;
