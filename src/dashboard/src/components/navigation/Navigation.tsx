import "leaflet/dist/leaflet.css";
import * as Leaflet from "leaflet";
import {
  Collapse,
  CollapseProps,
  Row,
  Switch,
  Col,
  Space,
  Button,
  Typography,
  InputNumber,
  Form,
} from "antd";
import { MapContainer } from "react-leaflet";
import { useCallback, useEffect, useState } from "react";
import DraggableMarker from "./DraggableMarker";
import { tileLayerOffline, savetiles, SaveStatus } from "leaflet.offline";

type NavigationType = {
  precision?: number;
};

const Navigation: React.FC<NavigationType> = ({ precision = 5 }) => {
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
  const mapCoords = `${mapPosition.lat.toFixed(
    precision
  )}, ${mapPosition.lng.toFixed(precision)}`;

  const [form] = Form.useForm<{ lat: string; lng: string }>();
  // Use a useEffect to set the form's initial lat and lng values. Setting with
  // the defaultValue prop seems to return undefined for values unless they have
  // been updated by the user at least once
  useEffect(() => {
    form.setFieldsValue({
      lat: initPosition.lat.toFixed(precision),
      lng: initPosition.lng.toFixed(precision),
    });
  }, []);

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
      // Add success callback functions for tiles that have been saved and
      // removed. These let you know when the tiles are finished saving/removing
      offlineTileLayer.on("saveend", (_e) => {
        window.alert("Success!");
      });
      offlineTileLayer.on("tilesremoved", (_e) => {
        window.alert("Tiles removed");
      });
      offlineTileLayer.addTo(map);

      const controlSaveTiles = savetiles(offlineTileLayer, {
        saveWhatYouSee: true,
        confirm(controlStatus: SaveStatus, successCallback: () => void) {
          if (
            window.confirm(
              `Save ${controlStatus.lengthToBeSaved} tiles? (This may take a few minutes).`
            )
          ) {
            successCallback();
          }
        },
        confirmRemoval(controlStatus: SaveStatus, successCallback: () => void) {
          if (controlStatus.storagesize) {
            if (window.confirm(`Remove ${controlStatus.storagesize} tiles?`)) {
              successCallback();
            }
          } else {
            window.alert("No tiles to save.");
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
        <div style={{ height: "46em" }}>
          <MapContainer
            center={initPosition}
            zoom={initZoom}
            style={{
              height: "95%",
            }}
            ref={setMap}
          >
            <DraggableMarker initPosition={initPosition} title="Base Station" />
          </MapContainer>
          <Row gutter={[12, 12]} justify="space-between" align="middle">
            <Col>
              <Form
                form={form}
                onFinish={(value) => {
                  console.log(value.lat);
                  console.log(value.lng);
                  console.log("submit!");
                }}
              >
                <Space>
                  <Form.Item noStyle>
                    <Button htmlType="submit">Add marker</Button>
                  </Form.Item>
                  at
                  <Form.Item name="lat" noStyle>
                    <InputNumber<string>
                      style={{ width: "8em" }}
                      min="-90"
                      max="90"
                      step={Math.pow(10, -1 * precision).toString()}
                      stringMode
                    />
                  </Form.Item>
                  ,
                  <Form.Item name="lng" noStyle>
                    <InputNumber<string>
                      style={{ width: "8em" }}
                      name="lng"
                      min="-180"
                      max="180"
                      step={Math.pow(10, -1 * precision).toString()}
                      stringMode
                    />
                  </Form.Item>
                </Space>
              </Form>
            </Col>
            <Col>
              Map Center:{" "}
              <Typography.Text copyable>{mapCoords}</Typography.Text>
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
