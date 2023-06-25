import { Tag, Typography } from "antd";

const { Paragraph } = Typography;

interface TopicProps {
  name: string;
}

const CopiableTag: React.FC<TopicProps> = ({ name }) => (
  <Tag>
    <Paragraph copyable style={{ margin: 0 }}>
      {typeof name === "boolean" ? JSON.stringify(name) : name}
    </Paragraph>
  </Tag>
);

export default CopiableTag;
