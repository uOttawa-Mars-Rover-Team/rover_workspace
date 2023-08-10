import "leaflet/dist/leaflet.css";
import * as Leaflet from "leaflet";
import { Collapse, CollapseProps, Row, Switch, Col, Space, Button } from "antd";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import { useCallback, useEffect, useState } from "react";
import DraggableMarker from "./DraggableMarker";

const Navigation: React.FC = () => {
  const precision = 5;
  const initPosition = new Leaflet.LatLng(45.4203222, -75.6803941);
  const initZoom = 18;
  // Define URL templates according to the Leaflet TileLayer style to get map
  // tile data from Google Maps
  const satelliteTileLayer =
    "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}";
  const terrainTileLayer = "https://mt0.google.com/vt/lyrs=p&x={x}&y={y}&z={z}";
  const [useTerrain, setUseTerrain] = useState(false);

  const [map, setMap] = useState<null | Leaflet.Map>();
  const [mapPosition, setMapPosition] = useState(initPosition);
  const onMove = useCallback(() => {
    if (map) {
      setMapPosition(map.getCenter());
    }
  }, [map]);
  useEffect(() => {
    if (map) {
      map.on("move", onMove);
      return () => {
        map.off("move", onMove);
      };
    }
  }, [map]);

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
            ref={setMap}
          >
            <TileLayer
              attribution="Google Maps"
              url={useTerrain ? terrainTileLayer : satelliteTileLayer}
            />
            <Marker position={initPosition}></Marker>
            <DraggableMarker initPosition={initPosition} />
          </MapContainer>
          <Row gutter={[12, 12]} justify="space-between" align="middle">
            <Col>
              <Button>Add marker</Button>
            </Col>
            <Col>
              Map Center:{" "}
              {`${mapPosition.lat.toFixed(
                precision
              )}, ${mapPosition.lng.toFixed(precision)}`}
            </Col>
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
