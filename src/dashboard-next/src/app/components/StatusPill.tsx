type StatusPillProps = {
    label: string;
    value: string; 
    valueClassName?: string;
}

export default function StatusPill({
    label,
    value,
    valueClassName
}: StatusPillProps) {
    return (
        <div className="bg-panel border border-line rounded-lg px-3.5 py-1.5 flex flex-col">
            <span className="text-xs text-muted">{label}</span>
            <span className={`font-semibold ${valueClassName ??``}`}>{value}</span>
        </div>
    )
}