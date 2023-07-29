import { BrowserRouter, Switch, Route, Redirect } from "react-router-dom";
import {
  Overview,
  ScienceMission,
  DeliveryMission,
  EquipmentServicingMission,
  AutonomousNavigationMission,
} from "../pages";

const Router: React.FC = () => (
  <BrowserRouter>
    <Switch>
      <Route path="/autonomousNavigationMission">
        <AutonomousNavigationMission />
      </Route>
      <Route path="/equipmentServicingMission">
        <EquipmentServicingMission />
      </Route>
      <Route path="/deliveryMission">
        <DeliveryMission />
      </Route>
      <Route path="/scienceMission">
        <ScienceMission />
      </Route>
      <Route path="/overview">
        <Overview />
      </Route>
      <Route path="/">
        <Redirect to="/overview" />
      </Route>
    </Switch>
  </BrowserRouter>
);

export default Router;
