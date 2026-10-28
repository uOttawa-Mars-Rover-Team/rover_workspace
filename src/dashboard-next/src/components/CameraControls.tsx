import Card from "./Card";

type CameraControlsProps = {
    className?: string;
}

const controls = [
    { label: "Picture Node"},
    { label: "Panorama Node"},
    { label: "Video Node"},
];

export default function CameraControls({
    className
}: CameraControlsProps) {
    return (
        <Card title="Camera Controls" className={className}>
            <div className="flex flex-col gap-2">
                {controls.map((control) => (
                    <button type="button" key={control.label} className="cursor-pointer text-sm min-h-10 rounded-lg border border-line bg-page px-3 text-left">
                        {control.label}
                    </button>
                ))}
            </div>
        </Card>
    )
}   