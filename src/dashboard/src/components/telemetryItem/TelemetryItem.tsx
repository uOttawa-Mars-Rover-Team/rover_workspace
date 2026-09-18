import "@fortawesome/fontawesome-free/css/all.min.css";
import "leaflet/dist/leaflet.css";
import styles from "./TelemetryItem.module.css";

import React from "react";

interface TelemetryItemProps {
  name: string;
  data: string;
  image: string;
  children?: React.ReactNode;
}

export default function TelemetryItem({
  name,
  data,
  image,
  children,
}: TelemetryItemProps) {
  return (
    <div className={styles.Box}>
      {children}
      <p className={styles.name}>{name}</p>
      <img src={image} alt="image of lightning bolt" className={styles.icon} />
      <p className={styles.data}>{data}</p>
    </div>
  );
}
