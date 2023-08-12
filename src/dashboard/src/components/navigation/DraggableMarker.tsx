import { Col, Row, Space } from "antd";
import * as Leaflet from "leaflet";
import { useState, useRef } from "react";
import { Marker, Popup } from "react-leaflet";

type DraggableMarkerProps = {
  initPosition: Leaflet.LatLng;
  deleteCallback?: () => void;
  title?: string;
  precision?: number;
  icon?: Leaflet.DivIcon;
};

const DraggableMarker: React.FC<DraggableMarkerProps> = ({
  initPosition,
  deleteCallback,
  title = "No title.",
  precision = 5,
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
    <Popup minWidth={40}>
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
          </Space>
        </div>
      </div>
    </Popup>
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

export default DraggableMarker;
