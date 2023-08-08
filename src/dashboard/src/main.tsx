import React from "react";
import ReactDOM from "react-dom/client";
import { ConfigProvider, theme } from "antd";
import "./index.scss";
import { Provider, Router } from "./utils";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider
      theme={{
        algorithm: [theme.darkAlgorithm],
        token: {
          colorPrimary: "#ef8934",
          colorInfo: "#ef8934",
          borderRadius: 6,
        },
      }}
    >
      <Provider>
        <Router />
      </Provider>
    </ConfigProvider>
  </React.StrictMode>
);
