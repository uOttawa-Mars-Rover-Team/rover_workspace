import Card from "./Card";

type PowerPanelProps = {
    className?: string;
}

//Mock Data for now, will be replaced with actual data in task 2
const rows = [
            { label: "Battery voltage", value: "24.8 V" },
            { label: "Total current", value: "12.4 A" },
            { label: "Jetson CPU", value: "38%" },
            { label: "Jetson GPU", value: "21%" },
            { label: "CPU temp", value: "54 °C" },
            { label: "GPU temp", value: "49 °C" },
];


export default function PowerPanel({
    className
}: PowerPanelProps) {
    return (
        <Card title="Power & Jetson" className={className}>
        {rows.map((row) => (
            <div key={row.label} className="flex items-center justify-between border-t border-line py-2">
                <span className="text-sm text-muted">{row.label}</span>
                <span className="font-mono font-semibold">{row.value}</span>
            </div>
        ))}
        </Card>
    )}              