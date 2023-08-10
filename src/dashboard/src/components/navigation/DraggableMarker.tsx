import * as Leaflet from "leaflet";
import { useState, useRef } from "react";
import { Marker, Popup } from "react-leaflet";

type DraggableMarkerProps = {
  initPosition: Leaflet.LatLng;
  title?: string;
  precision?: number;
};

const DraggableMarker: React.FC<DraggableMarkerProps> = ({
  initPosition,
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
        <div style={{ background: draggable ? "#ccf5ff" : "white" }}>
          <h2>{title}</h2>
          <div
            style={{
              textAlign: "center",
            }}
          >
            <p>{`${position.lat.toFixed(precision)}, ${position.lng.toFixed(
              precision
            )}`}</p>
            <p onClick={() => setDraggable(!draggable)}>
              {draggable ? "Not fixed" : "Fixed"}
            </p>
          </div>
        </div>
      </Popup>
    </Marker>
  );
};

export default DraggableMarker;
