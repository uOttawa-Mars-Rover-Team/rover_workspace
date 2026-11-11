"use client";

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState,
    type ReactNode,
} from "react";
import type ROSLIB from "roslib";

type RosStatus = "disconnected" | "connecting" | "connected" | "error";

type RosContextValue = {
    url: string;
    status: RosStatus;
    connect: (url: string) => void;
    disconnect: () => void;
};

const RosContext = createContext<RosContextValue | null>(null);

export function RosProvider({ children }: { children: ReactNode }) {
    const [url, setUrl] = useState("ws://localhost:9090");
    const [status, setStatus] = useState<RosStatus>("disconnected");
    const rosRef = useRef<ROSLIB.Ros | null>(null);

    const connect = useCallback(async (newUrl: string) => {
        rosRef.current?.close();
        setUrl(newUrl);
        setStatus("connecting");

        const ROSLIB = (await import("roslib")).default;
        const ros = new ROSLIB.Ros({ url: newUrl });
        rosRef.current = ros;

        ros.on("connection", () => {
            if (rosRef.current === ros) setStatus("connected");
        });
        ros.on("error", () => {
            if (rosRef.current === ros) setStatus("error");
        });
        ros.on("close", () => {
            if (rosRef.current === ros) {
                setStatus((s) => (s === "error" ? s : "disconnected"));
            }
        });
    }, []);

    const disconnect = useCallback(() => {
        rosRef.current?.close();
        rosRef.current = null;
        setStatus("disconnected");
    }, []);

    useEffect(() => {
        return () => {
            rosRef.current?.close();
        };
    }, []);

    const value: RosContextValue = { url, status, connect, disconnect };

    return <RosContext.Provider value={value}>{children}</RosContext.Provider>;
}

export function useRos() {
    const context = useContext(RosContext);
    if (!context) {
        throw new Error("useRos must be used inside RosProvider");
    }
    return context;
}