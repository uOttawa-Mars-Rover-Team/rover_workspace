import { useRef, useState } from "react";
import { Typography, Button } from "antd";

const { Text } = Typography;

const DANGER_LIMIT = 10;

const GATES = [
  "Gate 1",
  "Gate 2",
  "Gate 3",
  "Gate 4",
  "Gate 5: Drop",
  "Gate 6",
  "Gate 7",
];

function clamp(v: number, min: number, max: number) {
  return Math.max(min, Math.min(max, v));
}

function getColor(value: number) {
  const abs = Math.abs(value);
  if (abs >= DANGER_LIMIT) return "#d16154";
  if (abs >= 7) return "#ebce59";
  return "#77eea9";
}

export default function AccelBars({
  ax,
  ay,
  az,
  norm,
}: {
  ax: number;
  ay: number;
  az: number;
  norm: number;
}) {
  const [currentGate, setCurrentGate] = useState(0);
  const [gateResults, setGateResults] = useState<(boolean | null)[]>(
    Array(GATES.length).fill(null)
  );

  const limitHitRef = useRef(false);

  if (Math.abs(ax) >= 10 || Math.abs(ay) >= 10 || Math.abs(az) >= 10 || norm >= 10) {
    limitHitRef.current = true;
  }

  const bars = [
    { label: "X", value: ax },
    { label: "Y", value: ay },
    { label: "Z", value: az },
    { label: "Total", value: norm },
  ];

  const MAX = 20;
  const ticks = Array.from({ length: MAX + 1 }, (_, i) => i);

  const isDone = currentGate >= GATES.length;

  function handleNext() {
    if (isDone) return;
    const updated = [...gateResults];
    updated[currentGate] = limitHitRef.current;
    setGateResults(updated);
    setCurrentGate((g) => g + 1);
    limitHitRef.current = false;
  }

  function handleReset() {
    setCurrentGate(0);
    setGateResults(Array(GATES.length).fill(null));
    limitHitRef.current = false;
  }

  return (
    <div style={{ width: "100%", margin: 20 }}>
      {bars.map(({ label, value }) => {
        const pctRaw = (value / MAX) * 50;
        const pct = clamp(pctRaw, -50, 50);
        const left = pct < 0 ? 50 + pct : 50;
        const width = Math.max(Math.abs(pct), 1);
        const color = getColor(value);
        const isDanger = Math.abs(value) >= DANGER_LIMIT;

        return (
          <div
            key={label}
            style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 20, height: 75 }}
          >
            <Text style={{ width: 60, fontFamily: "monospace", textAlign: "left" }}>
              {label}
            </Text>

            <div
              style={{
                position: "relative",
                width: "100%",
                height: 24,
                background: "#111a2e",
                borderRadius: 2,
                border: "1px solid #223",
                overflow: "visible",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  top: -6,
                  width: 2,
                  height: 28,
                  background: "#556",
                  zIndex: 2,
                }}
              />
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: `${left}%`,
                  width: `${width}%`,
                  height: "100%",
                  background: color,
                  zIndex: 1,
                }}
              />
              {ticks.map((t) => {
                const pos = (t / MAX) * 100;
                const isMajor = t % 5 === 0;
                const isLabel = t === 10;
                return (
                  <div
                    key={t}
                    style={{
                      position: "absolute",
                      left: `${pos}%`,
                      top: "50%",
                      transform: "translateY(-50%)",
                      width: isLabel ? 4 : isMajor ? 2 : 1,
                      height: isLabel ? 44 : isMajor ? 34 : 28,
                      background: isLabel ? "#8d8d8d" : "rgb(206, 206, 206)",
                      zIndex: 10,
                    }}
                  />
                );
              })}
            </div>

            <Text
              style={{ width: 60, fontFamily: "monospace", textAlign: "right" }}
              type={isDanger ? "danger" : undefined}
            >
              {value.toFixed(2)}
            </Text>
          </div>
        );
      })}

      {/* Live limit indicator */}
      <div style={{ marginBottom: 16 }}>
        {limitHitRef.current ? (
          <Text type="danger" style={{ fontFamily: "monospace" }}>Limit Reached</Text>
        ) : (
          <Text style={{ fontFamily: "monospace" }}>No limit reached</Text>
        )}
      </div>

      {/* Gate log - left to right */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 16 }}>
        {GATES.map((gate, i) => {
          const result = gateResults[i];
          if (result === null) return null;
          return (
            <Text
              key={gate}
              type={result ? "danger" : "success"}
              style={{ fontFamily: "monospace", whiteSpace: "nowrap" }}
            >
              {gate}: {result ? "Limit reached" : "Cleared"}
            </Text>
          );
        })}
      </div>

      {/* Current gate label + button */}
      {!isDone ? (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Text style={{ fontFamily: "monospace" }}>
            Current: {GATES[currentGate]}
          </Text>
          <Button type="primary" onClick={handleNext}>
            Next Gate →
          </Button>
        </div>
      ) : (
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Text type="success" style={{ fontFamily: "monospace" }}>All gates complete</Text>
          <Button onClick={handleReset}>↺ Reset</Button>
        </div>
      )}
    </div>
  );
}