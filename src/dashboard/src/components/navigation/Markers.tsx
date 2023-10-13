import { Col, Row, Space } from "antd";
import * as Leaflet from "leaflet";
import { useState, useRef, useEffect } from "react";
import { Marker, Popup, MarkerProps, PopupProps } from "react-leaflet";
import { defaultPrecision } from "./Navigation";

// Remove the position property/type and manually set it, because by default
// position may be an array of latitude and longitude or have properties "lat"
// and "lng". It may be easier to just omit array usage and always expect "lat"
// and "lng" properties to make accessing the values easier
type ModMarkerProps = Omit<MarkerProps, "position">;

type MarkerPopupProps = PopupProps & {
  position: Leaflet.LatLng;
  children?: React.ReactNode;
  title?: string;
  precision?: number;
};

type DynamicMarkerProps = ModMarkerProps & {
  position: Leaflet.LatLng;
  precision?: number;
};

type DraggableMarkerProps = ModMarkerProps & {
  initPosition: Leaflet.LatLng;
  deleteCallback?: () => void;
  precision?: number;
};

export const MarkerPopup: React.FC<MarkerPopupProps> = ({
  position,
  children,
  title = "No title.",
  precision = defaultPrecision,
  minWidth = 40,
}) => {
  return (
    <Popup minWidth={minWidth}>
      <div>
        <h2>{title}</h2>
        <div
          style={{
            textAlign: "center",
          }}
        >
          <Space direction="vertical">
            <div>{`${position.lat.toFixed(precision)}, ${position.lng.toFixed(
              precision
            )}`}</div>
            <div>{children}</div>
          </Space>
        </div>
      </div>
    </Popup>
  );
};

export const DynamicMarker: React.FC<DynamicMarkerProps> = ({
  position,
  title,
  icon,
}) => {
  useEffect(() => {
    console.log("wowo!");
  }, [position]);

  // Omit the icon prop altogether if it isn't a valid Leaflet.DivIcon. It seems
  // as though passing in an undefined value throws errors that cause the page
  // to not load (even though Typescript indicates it's a valid prop value)
  return icon ? (
    <Marker position={position} icon={icon}>
      <MarkerPopup title={title} position={position}></MarkerPopup>
    </Marker>
  ) : (
    <Marker position={position}>
      <MarkerPopup title={title} position={position}></MarkerPopup>
    </Marker>
  );
};

export const DraggableMarker: React.FC<DraggableMarkerProps> = ({
  initPosition,
  deleteCallback,
  title = "No title.",
  precision = defaultPrecision,
  icon = undefined,
}) => {
  const [draggable, setDraggable] = useState(false);
  const [position, setPosition] = useState(initPosition);
  const markerRef = useRef<null | Leaflet.Marker>(null);
  const eventHandlers = {
    // Define a "dragend" event handler, as defined by react-leaflet, to handle
    // drag events
    dragend: () => {
      if (markerRef !== null && markerRef.current !== null) {
        setPosition(markerRef.current.getLatLng());
      }
    },
  };

  const markerChildren = (
    <MarkerPopup position={position} title={title} precision={precision}>
      <Row justify="space-between">
        <Col>
          <b
            onClick={() => setDraggable(!draggable)}
            style={{ color: draggable ? "blue" : "black" }}
          >
            {draggable ? "Not fixed" : "Fixed"}
          </b>
        </Col>
        {deleteCallback && (
          <Col>
            <b style={{ color: "red" }} onClick={deleteCallback}>
              Delete
            </b>
          </Col>
        )}
      </Row>
    </MarkerPopup>
  );

  // Omit the icon prop altogether if it isn't a valid Leaflet.DivIcon. It seems
  // as though passing in an undefined value throws errors that cause the page
  // to not load (even though Typescript indicates it's a valid prop value)
  return icon ? (
    <Marker
      draggable={draggable}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
      icon={icon}
    >
      {markerChildren}
    </Marker>
  ) : (
    <Marker
      draggable={draggable}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    >
      {markerChildren}
    </Marker>
  );
};
