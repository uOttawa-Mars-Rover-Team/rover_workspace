import { Space, Typography } from "antd";

const { Text } = Typography;

const CARDINALS: Record<number, string> = {
  0: "N", 22: "NNE", 45: "NE", 67: "ENE",
  90: "E", 112: "ESE", 135: "SE", 157: "SSE",
  180: "S", 202: "SSW", 225: "SW", 247: "WSW",
  270: "W", 292: "WNW", 315: "NW", 337: "NNW",
};

const CARDINAL_KEYS = [0, 22, 45, 67, 90, 112, 135, 157, 180, 202, 225, 247, 270, 292, 315, 337];

function getCardinalLabel(deg: number) {
  const idx = Math.round(deg / 22.5) % 16;
  return CARDINALS[CARDINAL_KEYS[idx]];
}

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

export default function Compass({ yaw }: { yaw: number }) {
  const SIZE = 250;
  const CX = 125;
  const CY = 125;
  const R = 121;

  const heading = ((yaw % 360) + 360) % 360;

  const ticks = Object.entries(CARDINALS).map(([degStr, label]) => {
    const deg = Number(degStr);
    const isMajor = deg % 90 === 0;
    const isMid = deg % 45 === 0 && !isMajor;
    const tickLen = isMajor ? 14 : isMid ? 10 : 7;
    const a = toRad(deg - heading - 90);
    const innerR = R - tickLen;
    return {
      deg, label, isMajor, isMid,
      x1: CX + innerR * Math.cos(a),
      y1: CY + innerR * Math.sin(a),
      x2: CX + (R - 2) * Math.cos(a),
      y2: CY + (R - 2) * Math.sin(a),
      lx: CX + (R - tickLen - 10) * Math.cos(a),
      ly: CY + (R - tickLen - 10) * Math.sin(a),
    };
  });

  return (
    <div style={{ textAlign: "center", display: "flex", flexDirection: "column", alignItems: "center", margin: 40 }}>
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        style={{
          borderRadius: "50%",
          overflow: "hidden",
          border: "3px solid rgb(223,223,233)",
        }}
      >
        <defs>
          <clipPath id="compassClip">
            <circle cx={CX} cy={CY} r={R} />
          </clipPath>
        </defs>

        <circle cx={CX} cy={CY} r={R} fill="#1a1e2a" clipPath="url(#compassClip)" />

        {ticks.map((t) => (
          <g key={t.deg}>
            <line
              x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
              stroke={t.isMajor ? "rgba(255,255,255,0.9)" : "rgba(255,255,255,0.5)"}
              strokeWidth={t.isMajor ? 1.5 : 1}
              clipPath="url(#compassClip)"
            />
            <text
              x={t.lx} y={t.ly}
              textAnchor="middle"
              dominantBaseline="central"
              fontSize={t.isMajor ? 18 : 9}
              fontWeight={t.isMajor ? "800" : "400"}
              fontFamily="sans-serif"
              fill={t.label === "N" ? "#e24b4a" : t.isMajor ? "rgba(255,255,255,0.95)" : "rgba(255,255,255,0.6)"}
              clipPath="url(#compassClip)"
            >
              {t.label}
            </text>
          </g>
        ))}

        {/* Lubber line */}
        <line x1={CX} y1={CY - R + 2} x2={CX} y2={CY - R + 10}
          stroke="#f1c31c" strokeWidth={2.5} strokeLinecap="round" />

        {/* Centre dot */}
        <circle cx={CX} cy={CY} r={2} fill="#f1c31c" />

        <circle cx={CX} cy={CY} r={R} fill="none" stroke="rgb(223,223,233)" strokeWidth={1} />
      </svg>

      <Space style={{ marginTop: 6 }}>
        <Text style={{ fontSize: 14 }}>
          Compass Facing: {getCardinalLabel(heading)} <b> ({String(Math.round(heading)).padStart(3, "0")}°)</b>
        </Text>
      </Space>
    </div>
  );
}