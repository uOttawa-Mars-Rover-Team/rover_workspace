type propsCameraPanel = {
    title: string;
    status: "live" | "no-signal"; 
    className?: string;
}

export default function CameraPanel({
    title,
    status,
    className
}: propsCameraPanel) {
    return (
        <section className={`bg-panel border border-line rounded-xl overflow-hidden flex flex-col ${className ?? ""}`}>
            <div className="flex items-center gap-2 border-b border-line px-3 py-2">
                <span className="text-sm font-semibold">{title}</span>
                <span
                    aria-hidden="true"
                    className={`h-2 w-2 rounded-full ${status === "live" ? "bg-ok" : "bg-danger"}`}
                />
            </div>
            <div className="flex flex-1 items-center justify-center bg-line text-sm text-muted">
                {status === "live" ? "Feed placeholder" : "No signal"}
            </div>
        </section>
    )
}
        