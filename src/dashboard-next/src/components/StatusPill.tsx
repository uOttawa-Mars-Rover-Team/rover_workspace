type StatusPillProps = {
    label: string;
    value: string; 
    valueClassName?: string;
    dot?: boolean;
}

export default function StatusPill({
    label,
    value,
    valueClassName,
    dot
}: StatusPillProps) {
    return (
        <div className="bg-panel border border-line rounded-lg px-3.5 py-1.5 flex flex-col">
            <span className="text-xs text-muted">{label}</span>
            <span className={`flex items-center gap-2 font-semibold ${valueClassName ??""}`}>
                {dot && <span aria-hidden="true" className="h-2 w-2 rounded-full bg-current" />}
                {value}
            </span>
        </div>
    )
}