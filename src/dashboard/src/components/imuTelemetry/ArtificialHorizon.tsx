import { Space, Typography } from "antd";
import { useRef, useReducer } from "react";

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
  yellowLimit = 20,
  redLimit = 35,
}: {
  roll: number;
  pitch: number;
  yellowLimit?: number;
  redLimit?: number;
}) {
  const SIZE = 300;
  const CX = 150;
  const CY = 150;
  const R = 146;

  const tareRef = useRef({ roll: 0, pitch: 0 });
  const [, forceUpdate] = useReducer((x) => x + 1, 0);

  const effectiveRoll = roll - tareRef.current.roll;
  const effectivePitch = pitch - tareRef.current.pitch;
  const absRoll = Math.abs(effectiveRoll);
  const absPitch = Math.abs(effectivePitch);

  function handleTare() {
    tareRef.current = { roll, pitch };
    forceUpdate();
  }

  function clearTare() {
    tareRef.current = { roll: 0, pitch: 0 };
    forceUpdate();
  }

  const pitchOffset = clamp(effectivePitch * 1.5, -R * 0.8, R * 0.8);
  const cosR = Math.cos(toRad(effectiveRoll));
  const sinR = Math.sin(toRad(effectiveRoll));
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

  const rollTicks = [
    -90, -80, -70, -60, -50, -40, -30, -20, -10, 0,
     10,  20,  30,  40,  50,  60,  70,  80,  90,
  ].map((deg) => {
    const a = toRad(deg - 90);
    const inner = R - 8;
    const outer = R - (deg % 30 === 0 ? 2 : 5);
    return {
      x1: CX + inner * Math.cos(a),
      y1: CY + inner * Math.sin(a),
      x2: CX + outer * Math.cos(a),
      y2: CY + outer * Math.sin(a),
      major: deg % 30 === 0,
      deg,
    };
  });

  const pA = toRad(-effectiveRoll - 90);

  function limitArc(limitDeg: number, r: number): string {
    const s = toRad(-limitDeg - 90);
    const e = toRad(limitDeg - 90);
    const sx = CX + r * Math.cos(s), sy = CY + r * Math.sin(s);
    const ex = CX + r * Math.cos(e), ey = CY + r * Math.sin(e);
    const large = limitDeg * 2 > 180 ? 1 : 0;
    return `M${sx},${sy} A${r},${r} 0 ${large} 1 ${ex},${ey}`;
  }

  function pitchTickColor(deg: number): string {
    const absDeg = Math.abs(deg);
    if (absDeg >= redLimit)    return "rgba(226,75,74,0.85)";
    if (absDeg >= yellowLimit) return "rgba(239,159,39,0.85)";
    return "rgba(255,255,255,0.7)";
  }

  function rollTickColor(deg: number): string {
    const absDeg = Math.abs(deg);
    if (absDeg >= redLimit)    return "rgba(226,75,74,0.9)";
    if (absDeg >= yellowLimit) return "rgba(239,159,39,0.9)";
    return "rgba(255,255,255,0.8)";
  }

  const isRollRed     = absRoll  >= redLimit;
  const isRollYellow  = !isRollRed  && absRoll  >= yellowLimit;
  const isPitchRed    = absPitch >= redLimit;
  const isPitchYellow = !isPitchRed && absPitch >= yellowLimit;

  const ringColor =
    (isRollRed    || isPitchRed)    ? "#e24b4a" :
    (isRollYellow || isPitchYellow) ? "#ef9f27" :
                                       "rgb(223,223,233)";

  const rollTextColor =
    isRollRed    ? "#e24b4a" :
    isRollYellow ? "#ef9f27" :
                   undefined;

  const pitchTextColor =
    isPitchRed    ? "#e24b4a" :
    isPitchYellow ? "#ef9f27" :
                    undefined;

  return (
    <div style={{ textAlign: "center", alignItems: "center", display: "flex", flexDirection: "column", margin: 40 }}>
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        style={{
          borderRadius: "50%",
          overflow: "hidden",
          border: `3px solid ${ringColor}`,
          transition: "border-color 0.25s",
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
        <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#e9e9e9" strokeWidth={2} clipPath="url(#hClip)" />

        {pitchTicks.map((t) => (
          <line
            key={t.deg}
            x1={t.tx1} y1={t.ty1} x2={t.tx2} y2={t.ty2}
            stroke={pitchTickColor(t.deg)}
            strokeWidth={1.5}
            clipPath="url(#hClip)"
          />
        ))}

        {rollTicks.map((t, i) => (
          <line
            key={i}
            x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
            stroke={rollTickColor(t.deg)}
            strokeWidth={t.major ? 2 : 1}
            clipPath="url(#hClip)"
          />
        ))}

        {yellowLimit < 90 && (
          <path
            d={limitArc(yellowLimit, R - 2)}
            fill="none"
            stroke="rgba(239,159,39,0.6)"
            strokeWidth={7}
            strokeLinecap="round"
            clipPath="url(#hClip)"
          />
        )}
        {redLimit < 90 && (
          <path
            d={limitArc(redLimit, R - 2)}
            fill="none"
            stroke="rgba(226,75,74,0.65)"
            strokeWidth={7}
            strokeLinecap="round"
            clipPath="url(#hClip)"
          />
        )}

        {(isRollYellow || isPitchYellow) && (
          <circle cx={CX} cy={CY} r={R} fill="rgba(239,159,39,0.08)" clipPath="url(#hClip)" />
        )}
        {(isRollRed || isPitchRed) && (
          <circle cx={CX} cy={CY} r={R} fill="rgba(226,75,74,0.13)" clipPath="url(#hClip)" />
        )}

        <polygon
          fill="#f1c31c"
          points={[
            `${CX + (R - 2) * Math.cos(pA)},${CY + (R - 2) * Math.sin(pA)}`,
            `${CX + (R - 14) * Math.cos(toRad(-effectiveRoll - 85))},${CY + (R - 14) * Math.sin(toRad(-effectiveRoll - 85))}`,
            `${CX + (R - 14) * Math.cos(toRad(-effectiveRoll - 95))},${CY + (R - 14) * Math.sin(toRad(-effectiveRoll - 95))}`,
          ].join(" ")}
        />

        <circle cx={CX} cy={CY} r={R} fill="none" stroke={ringColor} strokeWidth={1.5} style={{ transition: "stroke 0.25s" }} />
      </svg>

      <Space style={{ marginTop: 8 }}>
        <Text style={{ color: rollTextColor, transition: "color 0.25s" }}>
          Roll <b>{effectiveRoll.toFixed(1)}°</b>
        </Text>
        <Text style={{ color: pitchTextColor, transition: "color 0.25s" }}>
          Pitch <b>{effectivePitch.toFixed(1)}°</b>
        </Text>
        {(tareRef.current.roll !== 0 || tareRef.current.pitch !== 0) && (
          <Text type="secondary" style={{ fontSize: 11 }}>
            tare {tareRef.current.roll.toFixed(1)}°, {tareRef.current.pitch.toFixed(1)}°
          </Text>
        )}
      </Space>

      <Space style={{ marginTop: 8 }}>
        <button onClick={handleTare}>Tare (zero here)</button>
        <button onClick={clearTare}>Clear tare</button>
      </Space>
    </div>
  );
}