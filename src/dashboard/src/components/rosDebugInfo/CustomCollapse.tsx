/* eslint-disable jsx-a11y/anchor-is-valid */
import { Col, Collapse, Row, Tooltip } from "antd";
import { PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";

interface CustomCollapseProps {
  lastRefreshed: string;
  title: string;
  size: number;
  shouldRefresh: boolean;
  setShouldRefresh: React.Dispatch<React.SetStateAction<boolean>>;
}

const CustomCollapse: React.FC<CustomCollapseProps> = ({
  children,
  shouldRefresh,
  setShouldRefresh,
  lastRefreshed,
  title,
  size,
}) => (
  <Collapse defaultActiveKey={["1"]}>
    <Collapse.Panel
      header={
        <>
          <b>{title}</b> ({size})
        </>
      }
      key="1"
      extra={
        <Row align="middle" gutter={12}>
          <Col>
            <Tooltip title="Last Updated">{lastRefreshed}</Tooltip>
          </Col>
          <Col>
            <Tooltip
              title={
                shouldRefresh ? "Disable auto-refresh" : "Enable auto-refresh"
              }
            >
              <span onClick={(e) => e.stopPropagation()}>
                <a onClick={() => setShouldRefresh((prev) => !prev)}>
                  {shouldRefresh ? (
                    <PauseCircleOutlined />
                  ) : (
                    <PlayCircleOutlined />
                  )}
                </a>
              </span>
            </Tooltip>
          </Col>
        </Row>
      }
    >
      {children}
    </Collapse.Panel>
  </Collapse>
);

export default CustomCollapse;
