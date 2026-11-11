"use client";

import StatusPill from "./StatusPill";
import Image from "next/image";
import { useRos } from "@/providers/RosProvider";
import { useState } from "react";

const statusLabel = {
    disconnected: "Disconnected",
    connecting: "Connecting…",
    connected: "Connected",
    error: "Error",
};

const statusColor = {
    disconnected: "text-muted",
    connecting: "text-muted",
    connected: "text-ok",
    error: "text-danger-soft",
};

export default function Header() {
    const { status, url, connect } = useRos();
    const [address, setAddress] = useState(url);

    return (
        <header className="bg-bar border-b border-line flex items-center gap-4 px-4 py-2 flex-wrap">
            <Image src="/logo192.png" alt="uORover logo" width={40} height={40} />
            <div className="flex flex-col">
                <span className="text-xs text-muted">uORover</span>
                <span className="text-lg font-bold">Dashboard</span>
            </div>
            <div className="flex gap-2">
                <StatusPill
                    label="Bridge"
                    value={statusLabel[status]}
                    valueClassName={statusColor[status]}
                    dot
                />
                <StatusPill label="Latency" value="42 ms" valueClassName="font-mono" />
                <StatusPill label="Packet health" value="98%" valueClassName="font-mono text-ok" />
            </div>
            <div className="flex items-center gap-2">
                <input
                    type="text"
                    aria-label="ROS bridge address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    className="min-h-11 w-56 rounded-lg border border-line bg-page px-3 font-mono text-sm text-ink"
                />
                <button
                    type="button"
                    onClick={() => connect(address)}
                    className="cursor-pointer min-h-11 rounded-lg border border-line px-3.5 text-sm text-ink"
                >
                    Connect to ROS
                </button>
            </div>
            <div className="flex-1" />
            <nav className="flex gap-1 rounded-xl border border-line bg-panel p-1">
                <button type="button" className="cursor-pointer bg-accent text-page font-semibold rounded-lg px-5 py-3">
                    Overview
                </button>
                <button type="button" className="cursor-pointer text-muted rounded-lg px-5 py-3">
                    Sensors
                </button>
                <button type="button" className="cursor-pointer text-muted rounded-lg px-5 py-3">
                    ROS Debug
                </button>
            </nav>
            <button type="button" className="cursor-pointer bg-danger text-white font-bold rounded-lg px-5 py-3">
                Abort Mission
            </button>
        </header>
    )
}