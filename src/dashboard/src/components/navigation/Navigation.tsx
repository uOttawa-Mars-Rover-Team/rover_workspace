import "leaflet/dist/leaflet.css";
import * as Leaflet from "leaflet";
import { Collapse, CollapseProps, Row, Switch, Col, Space, Button } from "antd";
import { MapContainer, Marker } from "react-leaflet";
import { useCallback, useEffect, useState } from "react";
import DraggableMarker from "./DraggableMarker";
import { tileLayerOffline, savetiles } from "leaflet.offline";

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
  const activeTileLayer = useTerrain ? terrainTileLayer : satelliteTileLayer;

  const [map, setMap] = useState<null | Leaflet.Map>(null);
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
  useEffect(() => {
    if (map) {
      const offlineTileLayer = tileLayerOffline(activeTileLayer, {
        attribution: "Google Maps",
      });
      // lets you know when the tiles are finished saving/removing
      offlineTileLayer.on("saveend", (_e) => {
        window.alert("Success!");
      });
      offlineTileLayer.on("tilesremoved", (_e) => {
        window.alert("Tiles removed");
      });
      offlineTileLayer.addTo(map);

      const controlSaveTiles = savetiles(offlineTileLayer, {
        confirm(layer: any, successCallback: any) {
          if (
            window.confirm(
              `Save ${layer._tilesforSave.length} tiles? (may take up to a few minutes)`
            )
          ) {
            successCallback();
          }
        },
        confirmRemoval(layer: any, successCallback: any) {
          if (window.confirm(`Remove ${layer.storagesize} tiles?`)) {
            successCallback();
          }
        },
        saveText:
          '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" x="5" y="5" width="30" height="30" preserveAspectRatio="xMidYMid meet" viewBox="-2 -2 20 20"><g fill="currentColor"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/></g></svg>',
        rmText:
          '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" width="30" height="30" preserveAspectRatio="xMidYMid meet" viewBox="-2 -3 20 20"><g fill="currentColor"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></g></svg>',
      });
      controlSaveTiles.addTo(map);

      return () => {
        map.removeLayer(offlineTileLayer);
        map.removeControl(controlSaveTiles);
      };
    }
  }, [map, activeTileLayer]);

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
