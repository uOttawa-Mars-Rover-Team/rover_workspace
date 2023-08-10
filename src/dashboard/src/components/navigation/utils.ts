import * as Leaflet from "leaflet";

export const round = (num: number, places: number = 0) => {
  const multiplier = Math.pow(10, places);
  return Math.round((num + Number.EPSILON) * multiplier) / multiplier;
};

export const displayPosition = (
  position: Leaflet.LatLngExpression,
  precision: number = 5
) => {
  let lat = -1;
  let lng = -1;
  if (Array.isArray(position)) {
    lat = position[0];
    lng = position[1];
  } else {
    lat = position.lat;
    lng = position.lng;
  }
  return `${round(lat, precision)}, ${round(lng, precision)}`;
};
