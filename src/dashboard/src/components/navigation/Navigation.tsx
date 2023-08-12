import "font-awesome/css/font-awesome.min.css";
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
  Input,
} from "antd";
import { MapContainer } from "react-leaflet";
import { Fragment, useCallback, useEffect, useState } from "react";
import DraggableMarker from "./DraggableMarker";
import { tileLayerOffline, savetiles, SaveStatus } from "leaflet.offline";

type NavigationType = {
  precision?: number;
};
type markerObjectListType = {
  [key: number]: JSX.Element;
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

  const [markers, setMarkers] = useState<markerObjectListType>({
    0: <DraggableMarker initPosition={initPosition} title="Base Station" />,
  });
  const [numMarkers, setNumMarkers] = useState(Object.keys(markers).length);
  const markerDeleteCallbackGenerator = (markerIndex: number) => {
    return () => {
      const newMarkers = markers;
      delete newMarkers[markerIndex];
      setMarkers(newMarkers);
    };
  };

  const [form] = Form.useForm<{ lat: string; lng: string; title: string }>();

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
        saveText: '<i class="fa fa-download" title="Save tiles"></i>',
        rmText: '<i class="fa fa-trash" title="Remove tiles"></i>',
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
            {Object.keys(markers).map((markerNum, index) => {
              return (
                <Fragment key={index}>{markers[Number(markerNum)]}</Fragment>
              );
            })}
          </MapContainer>
          <Row gutter={[12, 12]} justify="space-between" align="middle">
            <Col>
              <Form
                form={form}
                onFinish={(value) => {
                  const newPosition = new Leaflet.LatLng(
                    Number(value.lat),
                    Number(value.lng)
                  );
                  const newMarkers = markers;
                  newMarkers[numMarkers] = (
                    <DraggableMarker
                      initPosition={newPosition}
                      deleteCallback={markerDeleteCallbackGenerator(numMarkers)}
                      title={
                        value.title.trim()
                          ? value.title.trim()
                          : `Marker #${(numMarkers + 1).toString()}`
                      }
                    />
                  );
                  setMarkers(newMarkers);
                  setNumMarkers(numMarkers + 1);
                }}
              >
                <Space>
                  <Form.Item noStyle>
                    <Button type="primary" htmlType="submit">
                      Add marker
                    </Button>
                  </Form.Item>
                  at
                  <Form.Item
                    name="lat"
                    initialValue={initPosition.lat.toFixed(precision)}
                    noStyle
                  >
                    <InputNumber<string>
                      style={{ width: "8em" }}
                      min="-90"
                      max="90"
                      step={Math.pow(10, -1 * precision).toString()}
                      stringMode
                    />
                  </Form.Item>
                  ,
                  <Form.Item
                    name="lng"
                    initialValue={initPosition.lng.toFixed(precision)}
                    noStyle
                  >
                    <InputNumber<string>
                      style={{ width: "8em" }}
                      min="-180"
                      max="180"
                      step={Math.pow(10, -1 * precision).toString()}
                      stringMode
                    />
                  </Form.Item>
                  with title
                  <Form.Item name="title" initialValue="" noStyle>
                    <Input />
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
