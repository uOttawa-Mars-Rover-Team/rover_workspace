import { Space, Typography } from "antd";

const { Text } = Typography;

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function toRad(deg: number) {
  return (deg * Math.PI) / 180;
}

export default function ArtificialHorizon({
  roll,
  pitch,
}: {
  roll: number;
  pitch: number;
}) {
  const SIZE = 300;
  const CX = 150;
  const CY = 150;
  const R = 146;

  const pitchOffset = clamp(pitch * 1.5, -R * 0.8, R * 0.8);
  const cosR = Math.cos(toRad(roll));
  const sinR = Math.sin(toRad(roll));
  const len = R * 1.5;

  const x1 = CX - len * cosR;
  const y1 = CY + pitchOffset + len * sinR;
  const x2 = CX + len * cosR;
  const y2 = CY + pitchOffset - len * sinR;

  const pitchTicks = [-50, -40, -30, -20, -10, 10, 20, 30, 40, 50].map((deg) => {
    const yOff = pitchOffset - deg * 1.5;
    const hw = deg % 20 === 0 ? 30 : 18;

    return {
      tx1: CX - hw * cosR - yOff * sinR,
      ty1: CY + hw * sinR - yOff * cosR,
      tx2: CX + hw * cosR - yOff * sinR,
      ty2: CY - hw * sinR - yOff * cosR,
      deg,
    };
  });

  const rollTicks = [-90, -80, -70, -60, -50, -40, -30, -20, -10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90 ].map((deg) => {
    const a = toRad(deg - 90);
    const inner = R - 8;
    const outer = R - (deg % 30 === 0 ? 2 : 5);

    return {
      x1: CX + inner * Math.cos(a),
      y1: CY + inner * Math.sin(a),
      x2: CX + outer * Math.cos(a),
      y2: CY + outer * Math.sin(a),
      major: deg % 30 === 0,
    };
  });

  const pA = toRad(-roll - 90);

  return (
    <div style={{ textAlign: "center", alignItems: "center", display: "flex",flexDirection: "column",margin: 40}}>
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        style={{
          borderRadius: "50%",
          overflow: "hidden",
          border: "3px solid rgb(223, 223, 223)",
        }}
      >
        <defs>
          <clipPath id="hClip">
            <circle cx={CX} cy={CY} r={R} />
          </clipPath>
        </defs>

        <path
          d={`M${x1} ${y1}L${x2} ${y2}L${CX + R * 2} ${CY - R * 2}L${CX - R * 2} ${CY - R * 2}Z`}
          fill="#3e7bca"
          clipPath="url(#hClip)"
        />

        <path
          d={`M${x1} ${y1}L${x2} ${y2}L${CX + R * 2} ${CY + R * 2}L${CX - R * 2} ${CY + R * 2}Z`}
          fill="#a18151"
          clipPath="url(#hClip)"
        />

        <line
          x1={x1}
          y1={y1}
          x2={x2}
          y2={y2}
          stroke="#e9e9e9"
          strokeWidth={2}
          clipPath="url(#hClip)"
        />

        {pitchTicks.map((t) => (
          <line
            key={t.deg}
            x1={t.tx1}
            y1={t.ty1}
            x2={t.tx2}
            y2={t.ty2}
            stroke="rgba(255,255,255,0.7)"
            strokeWidth={1.5}
            clipPath="url(#hClip)"
          />
        ))}

        {rollTicks.map((t, i) => (
          <line
            key={i}
            x1={t.x1}
            y1={t.y1}
            x2={t.x2}
            y2={t.y2}
            stroke="rgba(255,255,255,0.8)"
            strokeWidth={t.major ? 2 : 1}
            clipPath="url(#hClip)"
          />
        ))}

        <polygon
          fill="#f1c31c"
          points={[
            `${CX + (R - 2) * Math.cos(pA)},${CY + (R - 2) * Math.sin(pA)}`,
            `${CX + (R - 14) * Math.cos(toRad(-roll - 85))},${
              CY + (R - 14) * Math.sin(toRad(-roll - 85))
            }`,
            `${CX + (R - 14) * Math.cos(toRad(-roll - 95))},${
              CY + (R - 14) * Math.sin(toRad(-roll - 95))
            }`,
          ].join(" ")}
        />

        <circle cx={CX} cy={CY} r={R} fill="none" stroke="rgb(223, 223, 233)" />
      </svg>

      <Space style={{ marginTop: 8 }}>
        <Text >
          Roll <b>{roll.toFixed(1)}°</b>
        </Text>
        <Text>
          Pitch <b>{pitch.toFixed(1)}°</b>
        </Text>
      </Space>
    </div>
  );
}