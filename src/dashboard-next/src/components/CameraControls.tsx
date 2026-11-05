import Card from "./Card";

type CameraControlsProps = {
    className?: string;
}

// Mock Data for now, will be replaced with actual data in task 2
const controls = [
    { label: "Picture Node" },
    { label: "Panorama Node" },
    { label: "Video Node" },
];

export default function CameraControls({
    className
}: CameraControlsProps) {
    return (
        <Card title="Camera Controls" className={className}>
            <div className="flex flex-col gap-2">
                {controls.map((control) => (
                    <button
                        type="button"
                        key={control.label}
                        className="cursor-pointer flex min-h-10 items-center gap-3 rounded-lg border border-line bg-page px-3 text-sm"
                    >
                        <svg
                            viewBox="0 0 24 24"
                            className="h-4 w-4 text-muted"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            aria-hidden="true"
                        >
                            <path d="M9 6l6 6-6 6" />
                        </svg>
                        {control.label}
                    </button>
                ))}
            </div>
        </Card>
    )
}   