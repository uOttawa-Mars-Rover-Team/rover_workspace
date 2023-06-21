import { Collapse, Button, Tooltip, Form, Input } from "antd";
import { AimOutlined } from "@ant-design/icons";

import L, { Map } from "leaflet";
import { MapContainer } from "react-leaflet";
import React, { useState, useEffect, useRef } from "react";
import "leaflet.offline";

// tiles are stored in the browser storage. They remain there unless you clear the browser's cache
// to see the database (firefox), right click on the screen -> inspect -> storage -> indexed DB ->
// localhost -> leaflet.offline -> tileStore
// make sure there are no third party cache clearers on your browser that will accidentally clear the DB

//offline leaflet does not have types
//@ts-nocheck
const Navigation: React.FC = () => {
  const [map, setMap] = useState<Map | undefined>();

  // map properties
  const center = {
    lat: 45.4203222,
    lng: -75.6803941,
  };
  const zoom = 18;

  // // icon for the moving rover
  var rover = L.divIcon({
    html: '<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" role="img" width="16" height="16" preserveAspectRatio="xMidYMid meet" viewBox="0 0 24 24"><circle cx="12" cy="12" r="11" fill="#000"/></svg>',
    className: "",
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });

  // state holding the position of the rover
  const [pos, setPos] = useState<L.Marker>(
    new L.Marker(center, { icon: rover })
  );
  const prevPos = usePrevious(pos);

  // default marker position, change to the default location of the map as well
  const [marker, setMarker] = useState<L.Marker>(
    new L.Marker(center, { draggable: true })
  );
  const prevMarker = usePrevious(marker);

  const [line, setLine] = useState<L.Polyline>(
    new L.Polyline([marker.getLatLng(), pos.getLatLng()], {
      color: "red",
    })
  );

  function usePrevious(value: L.Marker) {
    const markerRef = useRef<L.Marker>(new L.Marker(center));

    useEffect(() => {
      markerRef.current = value; //assign the value of ref to the argument
    }, [value]); //this code will run when the value of 'value' changes
    return markerRef.current; //in the end, return the current ref value.
  }

  // @ts-ignore
  const tileLayerOffline = L.tileLayer.offline(
    "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", // satellite map
    // "http://mt0.google.com/vt/lyrs=p&hl=en&x={x}&y={y}&z={z}", // terrain map
    { minZoom: 13, maxNativeZoom: 22, maxZoom: 22 }
  );

  // lets you know when the tiles are finished saving/removing
  tileLayerOffline.on("saveend", (e: Event) => {
    window.alert("Success!");
  });

  tileLayerOffline.on("tilesremoved", (e: Event) => {
    window.alert("Tiles removed");
  });

  // @ts-ignore
  // handles saving, removing of tiles
  // saves the tiles in indexedDB which stores them until the database is cleared
  const controlSaveTiles = L.control.savetiles(tileLayerOffline, {
    zoomlevels: [18, 19, 20, 21, 22], // optional zoomlevels to save, default current zoomlevel
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

  // displays the map
  useEffect(() => {
    if (map) {
      map.setView(center, zoom);

      tileLayerOffline.addTo(map);
      controlSaveTiles.addTo(map!);
      L.control.scale().addTo(map);

      map.addLayer(pos);
      pos.setZIndexOffset(100);
      map.addLayer(marker);
      map.addLayer(line);
      // map.on('click', onMapClick);
    }
  }, [map]);

  // randomly generates the next position of the rover
  // add gps
  useEffect(() => {
    if (map) {
      let id = setTimeout(() => {
        let newCoords = {
          lat: pos.getLatLng().lat,
          lng: pos.getLatLng().lng,
        };
        setPos(new L.Marker(newCoords, { icon: rover }));
        pos.setZIndexOffset(100);
      }, 100);

      return () => clearTimeout(id);
    }
  }, [map]);

  // update the line when the position/marker changes
  useEffect(() => {
    if (map) {
      map.removeLayer(prevPos);
      map.addLayer(pos);
      line.setLatLngs([marker.getLatLng(), pos.getLatLng()]);
    }
  }, [pos]);

  useEffect(() => {
    if (map) {
      map.removeLayer(prevMarker);
      map.addLayer(marker);
      line.setLatLngs([marker.getLatLng(), pos.getLatLng()]);
    }
  }, [marker]);

  // // when a new marker is placed, the old one gets deleted
  // function onMapClick (e:any) {
  //   let newMarker = new L.Marker(e.latlng);
  //   setMarker(newMarker);
  // }

  // pans the map to the centre (for the center button)
  function toggleCenter() {
    if (map) {
      map.setView(pos.getLatLng());
    }
  }

  // changes the marker position based on the textboxes
  function onChangeLat(e: React.FormEvent<HTMLInputElement>): void {
    let newMarker = new L.Marker(
      L.latLng(Number(e.currentTarget.value), marker.getLatLng().lng)
    );
    setMarker(newMarker);
  }

  function onChangeLng(e: React.FormEvent<HTMLInputElement>): void {
    let newMarker = new L.Marker(
      L.latLng(marker.getLatLng().lat, Number(e.currentTarget.value))
    );
    setMarker(newMarker);
  }

  return (
    <Collapse defaultActiveKey={["1"]}>
      <Collapse.Panel
        header={<b>Map</b>}
        key="1"
        extra={
          <Tooltip title="Current location">
            Rover position: {pos.getLatLng().lat}, {pos.getLatLng().lng}
          </Tooltip>
        }
      >
        <div style={{ height: 550 }}>
          <MapContainer
            whenCreated={setMap}
            style={{ height: "95%", width: "100%", zIndex: 0 }}
          >
            <div
              style={{ zIndex: 1000, position: "absolute", right: 10, top: 10 }}
            >
              <Button
                type="primary"
                onClick={toggleCenter}
                icon={<AimOutlined />}
              ></Button>
            </div>
          </MapContainer>
          <Form style={{ position: "absolute", right: 30 }}>
            Marker Position: &nbsp;
            <Input
              type="textarea"
              size="small"
              maxLength={25}
              value={marker.getLatLng().lat}
              onChange={onChangeLat}
              style={{ width: 200 }}
            />{" "}
            , &nbsp;
            <Input
              type="textarea"
              size="small"
              maxLength={25}
              value={marker.getLatLng().lng}
              onChange={onChangeLng}
              style={{ width: 200 }}
            />
          </Form>
        </div>
      </Collapse.Panel>
    </Collapse>
  );
};

export default Navigation;
