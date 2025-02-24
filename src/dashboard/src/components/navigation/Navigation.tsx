import "@fortawesome/fontawesome-free/css/all.min.css";
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
import { MapContainer, Marker } from "react-leaflet";
import { Fragment, useCallback, useContext, useEffect, useState } from "react";
import { DraggableMarker, MarkerPopup } from "./Markers";
import { tileLayerOffline, savetiles, SaveStatus } from "leaflet.offline";
import * as config from "../../dashboardConfig.json";
import { RosContext } from "../../contexts";
import ROSLIB from "roslib";
import GpsWaypointRecorder from "../gpsWaypointRecorder/GpsWaypointRecorder";

type NavigationType = {
  precision?: number;
};
type markerObjectListType = {
  [key: number]: JSX.Element;
};
export type GPSMessage = {
  fix: number;
  satellites: number;
  latitude: number;
  longitude: number;
};

export const defaultPrecision = 5;

const Navigation: React.FC<NavigationType> = ({
  precision = defaultPrecision,
}) => {
  // Basic constants
  const { latitude, longitude } =
    config.overview.navigation.baseStationInitPosition;
  const initPosition = new Leaflet.LatLng(latitude, longitude);
  const initZoom = 18;

  // Define URL templates according to the Leaflet TileLayer style to get map
  // tile data from Google Maps
  const satelliteTileLayer =
    "https://mt0.google.com/vt/lyrs=s&x={x}&y={y}&z={z}";
  const terrainTileLayer = "https://mt0.google.com/vt/lyrs=p&x={x}&y={y}&z={z}";
  const [useTerrain, setUseTerrain] = useState(false);
  const [gpsWaypointMessage, setGpsWaypointMessage] = useState<GPSMessage>({
    fix: 0,
    satellites: 0,
    latitude: initPosition.lat,
    longitude: initPosition.lng,
  });
  const activeTileLayer = useTerrain ? terrainTileLayer : satelliteTileLayer;

  // Use a the leaflet map component's ref to allow it to be manipulated
  const [map, setMap] = useState<null | Leaflet.Map>(null);
  // Keep track of coordinates for the center of the map, which will be
  // displayed to the user
  const [mapPosition, setMapPosition] = useState(initPosition);
  const onMoveCallback = useCallback(() => {
    if (map) {
      setMapPosition(map.getCenter());
    }
  }, [map]);
  useEffect(() => {
    if (map) {
      map.on("move", onMoveCallback);
      return () => {
        map.off("move", onMoveCallback);
      };
    }
  }, [map, onMoveCallback]);

  const roverIcon = new Leaflet.DivIcon({
    html: '<i style="color:orange;font-size:2.5em;position:absolute;top:-0.3em;right:-0.4em;" class="fa-solid fa-rocket"></i>',
  });
  // Track the position of the rover, using ROS topic subscription to update
  // it's position
  const [roverPosition, setRoverPosition] = useState<Leaflet.LatLngTuple>([
    initPosition.lat,
    initPosition.lng,
  ]);
  const { rosClient } = useContext(RosContext);
  useEffect(() => {
    if (rosClient) {
      const topicName = config.overview.navigation.gpsTopicName;
      const topic = new ROSLIB.Topic({
        ros: rosClient,
        name: topicName,
        messageType: "general_interfaces/msg/GPS",
      });
      topic.subscribe((msg) => {
        const message = msg as GPSMessage;
        setGpsWaypointMessage(message);
        if (message.fix == 1) {
          setRoverPosition([message.latitude!, message.longitude!]);
        }
      });

      return () => {
        topic.unsubscribe();
      };
    }
  }, [rosClient]);

  // Keep track of the draggable markers on the map (which can be added by the
  // user), including the base station marker. An object is used instead of an
  // array to allow for the keys to be used to access markers for
  // cleanup/deletion. The object's keys increment and aren't reused.
  const [markers, setMarkers] = useState<markerObjectListType>({
    0: (
      <DraggableMarker
        initPosition={initPosition}
        title="Base Station"
        icon={
          new Leaflet.DivIcon({
            html: '<i style="color:purple;font-size:2.5em;position:absolute;top:-0.3em;right:-0.4em;" class="fa-solid fa-house"></i>',
          })
        }
      />
    ),
  });
  const [numMarkers, setNumMarkers] = useState(Object.keys(markers).length);
  // Helper function to allow a marker to remove itself from the map if specified by the user
  const markerDeleteCallbackGenerator = (markerIndex: number) => {
    return () => {
      const newMarkers = markers;
      delete newMarkers[markerIndex];
      setMarkers(newMarkers);
    };
  };

  const [form] = Form.useForm<{ lat: string; lng: string; title: string }>();

  // Allow for map tiles to be downloaded, allowing for the map to be accessed
  // offline
  useEffect(() => {
    if (map) {
      const offlineTileLayer = tileLayerOffline(activeTileLayer, {
        attribution: "Google Maps",
      });
      // Add success callback functions for tiles that have been saved and
      // removed. These let you know when the tiles are finished saving/removing
      offlineTileLayer.on("saveend", (_) => {
        window.alert("Success!");
      });
      offlineTileLayer.on("tilesremoved", (_) => {
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
        saveText: '<i class="fa-solid fa-download" title="Save tiles"></i>',
        rmText: '<i class="fa-solid fa-trash" title="Remove tiles"></i>',
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
      children: (
        <div style={{ height: "46em" }}>
          {/* Leaflet map */}
          <MapContainer
            center={initPosition}
            zoom={initZoom}
            style={{
              height: "95%",
            }}
            ref={setMap}
          >
            {/* Rover marker */}
            <Marker position={roverPosition} title="Rover" icon={roverIcon}>
              <MarkerPopup
                title="Rover"
                position={
                  new Leaflet.LatLng(roverPosition[0], roverPosition[1])
                }
              />
            </Marker>
            {/* Draggable markers */}
            {Object.keys(markers).map((markerNum, index) => {
              return (
                <Fragment key={index}>{markers[Number(markerNum)]}</Fragment>
              );
            })}
          </MapContainer>
          {/* Bottom info. bar */}
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
              <Typography.Text copyable>{`${mapPosition.lat.toFixed(
                precision
              )}, ${mapPosition.lng.toFixed(precision)}`}</Typography.Text>
            </Col>
            <Col>
              Rover Position:{" "}
              <Typography.Text copyable>
                {`${roverPosition[0].toFixed(
                  defaultPrecision
                )}, ${roverPosition[1].toFixed(defaultPrecision)}`}
              </Typography.Text>
            </Col>
            <Col>
              <Space align="center">
                <div>Use terrain map</div>
                <Switch onChange={() => setUseTerrain(!useTerrain)} />
              </Space>
            </Col>
            <Col>
              <GpsWaypointRecorder message={gpsWaypointMessage} />
            </Col>
          </Row>
        </div>
      ),
    },
  ];

  return <Collapse items={mapCollapseItems} defaultActiveKey={["1"]} />;
};

export default Navigation;
