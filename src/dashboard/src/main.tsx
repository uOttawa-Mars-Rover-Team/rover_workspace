import React from "react";
import ReactDOM from "react-dom/client";

import "./index.scss";
import { Provider, Router } from "./utils";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Provider>
      <Router />
    </Provider>
  </React.StrictMode>
);
