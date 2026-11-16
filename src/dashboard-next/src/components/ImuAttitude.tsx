"use client";

import Card from "./Card";
import { useTopic } from "@/hooks/useTopic";


type ImuMessage = {
    roll: number;
    pitch: number;
    yaw: number;
}

type ImuAttitudeProps = {
    className?: string;
};

const IMU_TOPIC = "/IMU";
const IMU_TYPE = "general_interfaces/msg/IMU";
const ROUND_PRECISION = 2;

export default function ImuAttitude({ className }: ImuAttitudeProps) {
    const imu = useTopic<ImuMessage>(IMU_TOPIC, IMU_TYPE);
    const imuAttitude = [
        { label: "Roll", value: imu ? `${imu.roll.toFixed(ROUND_PRECISION)}°` : "—" },
        { label: "Pitch", value: imu ? `${imu.pitch.toFixed(ROUND_PRECISION)}°` : "—" },
        { label: "Yaw", value: imu ? `${imu.yaw.toFixed(ROUND_PRECISION)}°` : "—" },
    ];
    
    return (
        <Card title="IMU Attitude" className={className}>
            <div className="flex-1 content-center grid grid-cols-3 gap-2">
                {imuAttitude.map((row) => (
                    <div
                        key={row.label}
                        className="flex flex-col items-center justify-center border border-line py-6 bg-page rounded-lg"
                    >
                        <span className="text-xs text-muted">{row.label}</span>
                        <span className="font-mono text-xl font-semibold">{row.value}</span>
                    </div>
                ))}
            </div>
        </Card>
    );
}