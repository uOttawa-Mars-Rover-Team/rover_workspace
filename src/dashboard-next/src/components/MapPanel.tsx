type MapPanelProps = {
    className?: string;
}

// Mock data for now, will be replaced with actual data in tasks 3 and 4
const stats = [
    { label: "Distance to goal", value: "48.2 m" },
    { label: "Elapsed time", value: "02:14" },
    { label: "Recovery behavior", value: "none" },
];

export default function MapPanel({
    className
}: MapPanelProps) {
    return (
        <section className={`relative flex items-center justify-center overflow-hidden rounded-xl border border-line bg-line text-sm text-muted ${className ?? ""}`}>
            Map placeholder

            <h2 className="absolute left-2.5 top-2.5 rounded-lg border border-line bg-panel px-3 py-2 text-sm font-semibold text-ink">
                Navigation
            </h2>

            <div className="absolute right-2.5 top-2.5 flex gap-4 rounded-xl border border-line bg-panel px-3 py-2 text-ink">
                {stats.map((stat) => (
                    <div key={stat.label} className="flex flex-col">
                        <span className="text-xs text-muted">{stat.label}</span>
                        <span className="font-mono font-semibold">{stat.value}</span>
                    </div>
                ))}
            </div>

            <div className="absolute bottom-2.5 left-2.5 flex flex-col gap-1">
                <button
                    type="button"
                    aria-label="Zoom in"
                    className="cursor-pointer h-10 w-10 rounded-lg border border-line bg-panel text-ink"
                >
                    +
                </button>
                <button
                    type="button"
                    aria-label="Zoom out"
                    className="cursor-pointer h-10 w-10 rounded-lg border border-line bg-panel text-ink"
                >
                    -
                </button>
            </div>
        </section>
    );
}