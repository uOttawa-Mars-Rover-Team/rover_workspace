import React, { useState, useEffect } from "react";
import { Layout as AntLayout, Row } from "antd";
import { GitlabOutlined } from "@ant-design/icons";

import Navbar from "./navbar/Navbar";

import "./Layout.scss";

const { Content, Footer } = AntLayout;

interface LayoutProps {
  children?: React.ReactNode;
  title: React.ReactNode;
  menuKey:
    | "overview"
    | "scienceMission"
    | "deliveryMission"
    | "equipmentServicingMission"
    | "autonomousNavigationMission";
}

const Layout: React.FC<LayoutProps> = ({ children, title, menuKey }) => {
  const [year, setYear] = useState("");

  useEffect(() => {
    setYear(new Date().getFullYear().toString());
  }, []);

  return (
    <AntLayout className="root-layout">
      <Row align="middle" justify="start">
        <Navbar title={title} menuKey={menuKey} />
      </Row>
      <Row align="middle" justify="center">
        <Content
          style={{
            margin: 20,
            marginTop: 20,
            maxWidth: 2200,
          }}
        >
          {children}
        </Content>
      </Row>
      <Footer className="root-footer">
        ©{year} Open source code available on
        <a
          className="root-footer-link"
          target="_blank"
          rel="noopener noreferrer"
          href="https://gitlab.com/uorover/rover_workspace"
        >
          <GitlabOutlined />
          <span className="root-footer-link">Gitlab</span>
        </a>
      </Footer>
    </AntLayout>
  );
};

export default Layout;
