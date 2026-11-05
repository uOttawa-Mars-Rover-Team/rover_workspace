import Card from "./Card";

type PowerPanelProps = {
    className?: string;
};

const SEGMENTS = 20;

// Mock data for now, will be replaced with actual data in task 2
const power = [
    { label: "Battery Voltage", value: "24.6", unit: "V" },
    { label: "Current", value: "8.4", unit: "A" },
];

const jetson = [
    { label: "Jetson CPU", usage: 46, temp: 58 },
    { label: "Jetson GPU", usage: 31, temp: 54 },
];

export default function PowerPanel({ className }: PowerPanelProps) {
    return (
        <Card title="Power & Jetson" className={className}>
            <div className="flex flex-1 flex-wrap items-center gap-6">
                <div className="flex gap-6">
                    {power.map((item) => (
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
                        const filled = Math.round((item.usage / 100) * SEGMENTS);

                        return (
                            <div key={item.label}>
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted">{item.label}</span>
                                    <span className="font-mono">
                                        {item.usage}% · {item.temp} °C
                                    </span>
                                </div>
                                <div
                                    role="meter"
                                    aria-label={`${item.label} usage`}
                                    aria-valuenow={item.usage}
                                    aria-valuemin={0}
                                    aria-valuemax={100}
                                    className="mt-1 flex gap-0.5"
                                >
                                    {Array.from({ length: SEGMENTS }, (_, i) => (
                                        <span
                                            key={i}
                                            aria-hidden="true"
                                            className={`h-2 flex-1 rounded-sm ${
                                                i < filled ? "bg-accent" : "bg-line"
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