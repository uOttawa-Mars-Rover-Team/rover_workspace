import React from "react";
import ReactDOM from "react-dom";

import "./index.scss";
import { Provider, Router } from "./utils";

ReactDOM.render(
  <React.StrictMode>
    <Provider>
      <Router />
    </Provider>
  </React.StrictMode>,
  document.getElementById("root")
);
