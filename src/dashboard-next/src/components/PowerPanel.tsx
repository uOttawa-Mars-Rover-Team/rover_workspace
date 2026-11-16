"use client";
import Card from "./Card";
import { useTopic } from "@/hooks/useTopic";

type PowerPanelProps = {
    className?: string;
};

type PowerDataMessage = {
    voltage: number;
    currents: number[];
    filled: number;
};


const SEGMENTS = 20;
const POWER_TOPIC = "/PowerData";
const POWER_TYPE = "general_interfaces/msg/PowerData";
const ROUND_PRECISION = 2;

type JetsonData = {
    label: string;
    usage: number | null;
    temp: number | null;
};

const jetson: JetsonData[] = [
    { label: "Jetson CPU", usage: null, temp: null },
    { label: "Jetson GPU", usage: null, temp: null },
];

export default function PowerPanel({ className }: PowerPanelProps) {
    const power = useTopic<PowerDataMessage>(POWER_TOPIC, POWER_TYPE);
    const powerData = [
        {
            label: "Battery Voltage",
            value: power ? power.voltage.toFixed(ROUND_PRECISION) : "—",
            unit: "V",
        },
        {
            label: "Total Current",
            value: power ? power.currents[0].toFixed(ROUND_PRECISION) : "—",
            unit: "A",
        },
    ];

    return (
        <Card title="Power & Jetson" className={className}>
            <div className="flex flex-1 flex-wrap items-center gap-6">
                <div className="flex gap-6">
                    {powerData.map((item) => (
                        <div key={item.label} className="flex flex-col">
                            <div className="flex items-baseline gap-1">
                                <span className="font-mono text-3xl font-semibold">
                                    {item.value}
                                </span>
                                <span className="font-mono text-sm text-muted">
                                    {item.unit}
                                </span>
                            </div>
                            <span className="text-xs text-muted">{item.label}</span>
                        </div>
                    ))}
                </div>

                <div className="flex min-w-48 flex-1 flex-col gap-4">
                    {jetson.map((item) => {
                        const litSegments =
                            item.usage === null ? 0 : Math.round((item.usage / 100) * SEGMENTS);

                        return (
                            <div key={item.label}>
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted">{item.label}</span>
                                    <span className="font-mono">
                                        {item.usage === null ? "—" : `${item.usage}% · ${item.temp} °C`}
                                    </span>
                                </div>
                                <div
                                    role="meter"
                                    aria-label={`${item.label} usage`}
                                    aria-valuenow={item.usage ?? undefined}
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    className="mt-1 flex gap-0.5"
                                >
                                    {Array.from({ length: SEGMENTS }, (_, i) => (
                                        <span
                                            key={i}
                                            aria-hidden="true"
                                            className={`h-2 flex-1 rounded-sm ${
                                                i < litSegments ? "bg-accent" : "bg-line"
                                            }`}
                                        />
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </Card>
    );
}