import "leaflet/dist/leaflet.css";
import { Collapse, CollapseProps, Row, Switch, Col } from "antd";
import { MapContainer, TileLayer } from "react-leaflet";
import { useState } from "react";

const Navigation: React.FC = () => {
  const initPosition = {
    lat: 45.4203222,
    lng: -75.6803941,
  };
  const initZoom = 18;
  // Define URL templates according to the Leaflet TileLayer style to get map
  // tile data from Google Maps
  const satelliteTileLayer =
    "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}";
  const terrainTileLayer = "https://mt0.google.com/vt/lyrs=p&x={x}&y={y}&z={z}";
  const [useTerrain, setUseTerrain] = useState(false);

  const mapCollapseItems: CollapseProps["items"] = [
    {
      key: "1",
      label: <b>Map</b>,
      extra: <div>Rover position: </div>,
      children: (
        <div style={{ height: 550 }}>
          <MapContainer
            center={[initPosition.lat, initPosition.lng]}
            zoom={initZoom}
            style={{
              height: "95%",
            }}
          >
            <TileLayer
              attribution="Google Maps"
              url={useTerrain ? terrainTileLayer : satelliteTileLayer}
            />
          </MapContainer>
          <Row gutter={[12, 12]} justify="end" align="middle">
            <Col>Use terrain map</Col>
            <Col>
              <Switch onChange={() => setUseTerrain(!useTerrain)} />
            </Col>
          </Row>
        </div>
      ),
    },
  ];

  return <Collapse items={mapCollapseItems} defaultActiveKey={["1"]} />;
};

export default Navigation;
