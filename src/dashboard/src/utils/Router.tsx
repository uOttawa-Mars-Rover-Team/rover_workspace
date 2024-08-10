import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import {
  Overview,
  Camera,
  SingleCamera,
  Telemetry,
  ScienceMission,
  DeliveryMission,
  EquipmentServicingMission,
  AutonomousNavigationMission,
} from "../pages";

const Router: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route
        path="/autonomousNavigationMission"
        element={<AutonomousNavigationMission />}
      />
      <Route
        path="/equipmentServicingMission"
        element={<EquipmentServicingMission />}
      />
      <Route path="/deliveryMission" element={<DeliveryMission />} />
      <Route path="/scienceMission" element={<ScienceMission />} />
      <Route path="/overview" element={<Overview />} />
      <Route path="/camera" element={<Camera />} />
      <Route path="/camera/singleCamera" element={<SingleCamera/>}/>
      <Route path="/telemetry" element={<Telemetry />} />
      <Route path="/" element={<Navigate to="/overview" replace />} />
    </Routes>
  </BrowserRouter>
);

export default Router;
