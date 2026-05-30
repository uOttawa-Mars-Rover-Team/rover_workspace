import { Typography } from "antd";

const { Text } = Typography;

const DANGER_LIMIT = 10;

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
  const bars = [
    { label: "X", value: ax },
    { label: "Y", value: ay },
    { label: "Z", value: az },
    { label: "Total", value: norm },
  ];

  const MAX = 20;

  /// ticks every 1g
const ticks = Array.from({ length: MAX + 1 }, (_, i) => i);
  return (
    <div style={{ width: "100%", margin:20}}>
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
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              marginBottom: 20,
              height: 75
            }}
          >

            {/* label */}
            <Text style={{ width: 60, fontFamily: "monospace", textAlign: "left"}}>
              {label}
            </Text>

            {/* bar container */}
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
              {/* center line */}
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

              {/* bar */}
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

              {/* ticks */}
              {ticks.map((t) => {
                const pos = (t / MAX) * 100;

                const isMajor = t % 5 === 0; // 5g, 10g, 15g, 20g
                const isLabel = t === 10;     // emphasized mid danger point

                return (
                  <div
                    key={t}
                    style={{
                      position: "absolute",
                      left: `${pos}%`,
                      top: "50%",
                      transform: "translateY(-50%)",
                      width:
                        isLabel
                            ? 4
                            : isMajor
                            ? 2
                            : 1,
                      height:
                        isLabel
                            ? 44
                            : isMajor
                            ? 34
                            : 28,
                      background:
                        isLabel
                          ? "#8d8d8d"
                          : isMajor
                          ? "rgb(206, 206, 206)"
                          : "rgb(206, 206, 206)",
                      zIndex: 10,
                      
                    }}
                  />
                );
              })}
            </div>

            {/* value */}
            <Text
              style={{
                width: 60,
                fontFamily: "monospace",
                textAlign: "right",
              }}
              type={isDanger ? "danger" : undefined}
            >
              {value.toFixed(2)}
            </Text>
          </div>
        );
      })}
    </div>
  );
}