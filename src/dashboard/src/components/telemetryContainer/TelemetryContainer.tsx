import "@fortawesome/fontawesome-free/css/all.min.css";
import "leaflet/dist/leaflet.css";

import styles from './TelemetryContainer.module.css'
import { CSSProperties } from "react";

interface ContainerProps {
    children: React.ReactNode;
    style? : CSSProperties
}



export default function TelemetryContainer({style, children} : ContainerProps) {
    return <div className={styles.ContentWrap} style={style}>
            {children}
        </div>
}
