import {
  ControlOutlined,
  HomeOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  CloudDownloadOutlined
} from "@ant-design/icons";
import { Button, Col, Row, Space, Card, Input } from "antd";
import { Helmet } from "react-helmet";

import { Header, Layout } from "../../components";
import coring_icon from "../../assets/icons/drill-tip-svgrepo-com.svg";
import weather_icon from "../../assets/icons/weather-symbol-4-svgrepo-com.svg"

const dummyWeatherData = [
  { label: 'Wind', value: '16 Km/h' },
  { label: 'UV index', value: '4' },
  { label: 'IR', value: '3' },
  { label: 'Pressure', value: '1022 mb' },
  { label: 'Temperature', value: '18 °C' },
  { label: 'Humidity', value: '43%' },
]

const ScienceMission: React.FC = () => (
  <>
    <Helmet>
      <title>uoRover - Science Mission</title>
    </Helmet>
    <Layout title="Science Mission" menuKey="scienceMission">

      {/* Soil Collection Controls block */}
      <Header title="Soil Collection Controls" icon={<ControlOutlined />} />

      {/* Creates a row with 32 pixels of horizontal spacing and 16 pixels of vertical spacing between the columns,
          the vertical spacing is used for small screens where  */}
      <Row gutter={[32, 16]}>
        {/* Each column takes up 8 spans out of the 24 available spans in the grid system */}
        {/* Make it responsive to different screen sizes, each card component will be arranged vertically due to the screen width is not enough */}
        <Col xs={24} sm={12} md={8} lg={8}>
          <Card title="Soil Collection Linear Actuator" style={{ height: 260 }}>
            <Space direction="vertical" size="middle">

              <Button
                type="primary"
                icon={<img src={coring_icon} alt="Coring Icon" style={{ width: 24, height: 24 }} />}
                style={{
                  width: '100px', padding: '8px 8px', height: 'auto', display: 'flex', alignItems: 'center'
                }}>
                Coring
              </Button>

            </Space>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8} lg={8}>
          <Card title="Vacuum Tube" style={{ height: 260 }}>
            <Space direction="vertical" size="middle">
              <Button
                type="primary"
                icon={<HomeOutlined style={{ width: 24, height: 24 }} />}
                style={{
                  width: '100px', padding: '8px 8px', height: 'auto', display: 'flex', alignItems: 'center'
                }}>
                Home
              </Button>

              <Button
                type="primary"
                icon={<ArrowUpOutlined style={{ width: 24, height: 24 }} />}
                style={{
                  width: '100px', padding: '8px 8px', height: 'auto', display: 'flex', alignItems: 'center'
                }}>
                Up
              </Button>

              <Button
                type="primary"
                icon={<ArrowDownOutlined style={{ width: 24, height: 24 }} />}
                style={{
                  width: '100px', padding: '8px 8px', height: 'auto', display: 'flex', alignItems: 'center'
                }}>
                Down
              </Button>
            </Space>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={8} lg={8}>
          <Card title="Core Soil Sensors Data" style={{ height: 260 }}>
            <Space direction="vertical" size="middle">
              <Button
                type="primary"
                icon={<CloudDownloadOutlined style={{ width: 24, height: 24 }} />}
                style={{
                  width: '100px', padding: '8px 8px', height: 'auto', display: 'flex', alignItems: 'center'
                }}>
                Collect
              </Button>
              <Input placeholder="TODO: Published Data" disabled />
            </Space>
          </Card>
        </Col>
      </Row>


      {/* Weather block */}
      <Header
        title="Weather"
        icon={<img src={weather_icon} alt="Weather Icon" />} >
      </Header>
      <Card>
        <Row gutter={[32, 32]}>
          {dummyWeatherData.map((item, index) => (
            <Col xs={12} sm={12} md={8} lg={4} key={index} style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 'bold', fontSize: '18px' }}>
                {item.value}
              </div>

              <div>
                {item.label}
              </div>
            </Col>
          ))}
        </Row>
      </Card>
    </Layout>
  </>
);

export default ScienceMission;
