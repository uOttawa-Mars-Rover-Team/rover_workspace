import Card from "./Card";

type ImuAttitudeProps = {
    className?: string;
}

//Mock Data for now, will be replaced with actual data in task 2
const imuAttitude = [
    { label: "Roll", value: "0.0°" },
    { label: "Pitch", value: "0.0°" },
    { label: "Yaw", value: "0.0°" },
];

export default function ImuAttitude({
    className
}: ImuAttitudeProps) {
    return (
        <Card title="IMU Attitude" className={className}>
            <div className="flex-1 content-center grid grid-cols-3 gap-2">
                {imuAttitude.map((row) => (
                    <div key={row.label} className="flex flex-col items-center justify-center border border-line py-6 bg-page rounded-lg">
                        <span className="text-xs text-muted">{row.label}</span>
                        <span className="font-mono text-xl font-semibold">{row.value}</span>
                    </div>
                ))}
            </div>
            
        </Card>
    )
}   