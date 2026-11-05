const inputClass =
    "min-h-11 rounded-lg border border-line bg-page px-3 font-mono text-sm text-ink";

const buttonClass =
    "cursor-pointer min-h-11 rounded-lg border border-line bg-page px-4 text-sm";

// Mock data for now, will be replaced with actual data in task 3
const marker = { latitude: "45.42032", longitude: "-75.68039" };
const mapInfo = { center: "45.41799, -75.68222", rover: "45.42032, -75.68039" };

export default function MapControls() {
    return (
        <section className="flex flex-col gap-3 rounded-xl border border-line bg-panel p-3">
            <div className="flex flex-wrap items-center gap-2">
                <button
                    type="button"
                    className="cursor-pointer min-h-11 rounded-lg bg-accent px-4 text-sm font-semibold text-page"
                >
                    Add marker
                </button>
                <span className="text-sm text-muted">at</span>
                <input
                    defaultValue={marker.latitude}
                    aria-label="Latitude"
                    className={`${inputClass} w-32`}
                />
                <input
                    defaultValue={marker.longitude}
                    aria-label="Longitude"
                    className={`${inputClass} w-32`}
                />
                <span className="text-sm text-muted">with title</span>
                <input
                    aria-label="Marker title"
                    className={`${inputClass} min-w-32 flex-1`}
                />
            </div>

            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
                <span className="font-mono text-xs text-muted">
                    Map Center: {mapInfo.center}
                </span>
                <span className="font-mono text-xs text-muted">
                    Rover Position: {mapInfo.rover}
                </span>
                <div className="flex items-center gap-2">
                    <span className="text-sm text-muted">Use terrain map</span>
                    <button
                        type="button"
                        role="switch"
                        aria-checked={false}
                        aria-label="Use terrain map"
                        className="relative h-6 w-11 cursor-pointer rounded-full border border-line bg-page"
                    >
                        <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-muted" />
                    </button>
                </div>
            </div>

            <div className="flex flex-wrap gap-2">
                <input
                    placeholder="Waypoint Comment"
                    aria-label="Waypoint comment"
                    className={`${inputClass} min-w-48 flex-1`}
                />
                <button type="button" className={buttonClass}>
                    Record Waypoint
                </button>
                <button type="button" className={buttonClass}>
                    Download
                </button>
            </div>
        </section>
    );
}