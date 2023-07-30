/* eslint-disable jsx-a11y/anchor-is-valid */
import { Col, Collapse, Row, Tooltip, CollapseProps } from "antd";
import { PlayCircleOutlined, PauseCircleOutlined } from "@ant-design/icons";

interface CustomCollapseProps {
  children: React.ReactNode;
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
}) => {
  const customCollapseItems: CollapseProps["items"] = [
    {
      key: "1",
      label: (
        <>
          <b>{title}</b> ({size})
        </>
      ),
      extra: (
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
      ),
      children: children,
    },
  ];

  return <Collapse items={customCollapseItems} defaultActiveKey={["1"]} />;
};

export default CustomCollapse;
