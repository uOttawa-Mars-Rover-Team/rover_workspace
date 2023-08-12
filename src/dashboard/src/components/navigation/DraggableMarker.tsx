import { Col, Row, Space } from "antd";
import * as Leaflet from "leaflet";
import { useState, useRef } from "react";
import { Marker, Popup } from "react-leaflet";

type DraggableMarkerProps = {
  initPosition: Leaflet.LatLng;
  deleteCallback?: () => void;
  title?: string;
  precision?: number;
};

const DraggableMarker: React.FC<DraggableMarkerProps> = ({
  initPosition,
  deleteCallback,
  title = "No title.",
  precision = 5,
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

  return (
    <Marker
      draggable={draggable}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    >
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
    </Marker>
  );
};

export default DraggableMarker;
