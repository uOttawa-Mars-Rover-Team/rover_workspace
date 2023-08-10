import "leaflet/dist/leaflet.css";
import { Collapse, CollapseProps, Row, Switch, Col, Space, Button } from "antd";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import { useState } from "react";
import DraggableMarker from "./DraggableMarker";

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
        <div style={{ height: 600 }}>
          <MapContainer
            center={initPosition}
            zoom={initZoom}
            style={{
              height: "95%",
            }}
          >
            <TileLayer
              attribution="Google Maps"
              url={useTerrain ? terrainTileLayer : satelliteTileLayer}
            />
            <Marker position={[initPosition.lat, initPosition.lng]}></Marker>
            <DraggableMarker initPosition={initPosition} />
          </MapContainer>
          <Row gutter={[12, 12]} justify="space-between" align="middle">
            <Col>
              <Button>Add marker</Button>
            </Col>
            <Col>Position: </Col>
            <Col>
              <Space align="center">
                <div>Use terrain map</div>
                <Switch onChange={() => setUseTerrain(!useTerrain)} />
              </Space>
            </Col>
          </Row>
        </div>
      ),
    },
  ];

  return <Collapse items={mapCollapseItems} defaultActiveKey={["1"]} />;
};

export default Navigation;
