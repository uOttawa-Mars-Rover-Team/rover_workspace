import { PageHeader } from "antd";

interface HeaderProps {
  title: React.ReactNode;
  icon: React.ReactNode;
  style?: React.CSSProperties;
  extra?: React.ReactNode;
}

const Header: React.FC<HeaderProps> = ({ title, icon, extra, style }) => (
  <PageHeader
    title={title}
    avatar={{
      icon,
      size: "large",
      style: {
        background: "transparent",
      },
    }}
    extra={extra}
    style={{ ...style, paddingLeft: 0, paddingRight: 0 }}
  />
);

export default Header;
