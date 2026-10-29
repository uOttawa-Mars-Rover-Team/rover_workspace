import Card from "./Card";

type AutonomyPanelProps = {
    className?: string;
}

// Mock data for now, will be replaced with actual data in task 4
const goal = { latitude: "45.42210", longitude: "-75.68302" };

export default function AutonomyPanel({
    className
}: AutonomyPanelProps) {
    return (
        <Card title="Autonomy Mission" className={className}>
            <div className="flex flex-wrap items-end gap-3">
                <label className="flex min-w-40 flex-1 flex-col gap-1">
                    <span className="text-xs text-muted">Target Latitude (WGS 84)</span>
                    <input
                        defaultValue={goal.latitude}
                        className="min-h-11 rounded-lg border border-line bg-page px-3 font-mono text-sm text-ink"
                    />
                </label>
                <label className="flex min-w-40 flex-1 flex-col gap-1">
                    <span className="text-xs text-muted">Target Longitude (WGS 84)</span>
                    <input
                        defaultValue={goal.longitude}
                        className="min-h-11 rounded-lg border border-line bg-page px-3 font-mono text-sm text-ink"
                    />
                </label>
                <button
                    type="button"
                    className="cursor-pointer min-h-11 rounded-lg bg-accent px-5 font-semibold text-page"
                >
                    Dispatch Goal
                </button>
                <button
                    type="button"
                    className="cursor-pointer min-h-11 rounded-lg border border-line bg-page px-5 text-sm"
                >
                    Pause / Resume
                </button>
            </div>
        </Card>
    );
}