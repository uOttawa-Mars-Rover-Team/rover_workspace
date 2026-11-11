"use client";

import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState,
    useSyncExternalStore,
    type ReactNode,
} from "react";
import type ROSLIB from "roslib";

type RosStatus =
    | "disconnected"
    | "connecting"
    | "connected"
    | "reconnecting"
    | "error";

type RosContextValue = {
    url: string;
    status: RosStatus;
    ros: ROSLIB.Ros | null;
    connect: (url: string) => void;
    disconnect: () => void;
};

const STORAGE_KEY = "ros-url";
const DEFAULT_URL = "ws://localhost:9090";
const BASE_DELAY_MS = 1000;
const MAX_DELAY_MS = 10000;

const RosContext = createContext<RosContextValue | null>(null);

const subscribe = () => () => {};

function readSavedUrl() {
    try {
        return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
        console.error("Error loading saved ROS URL", e);
        return null;
    }
}

export function RosProvider({ children }: { children: ReactNode }) {
    const [connectedUrl, setConnectedUrl] = useState<string | null>(null);
    const savedUrl = useSyncExternalStore(subscribe, readSavedUrl, () => null);
    const url = connectedUrl ?? savedUrl ?? DEFAULT_URL;
    const [status, setStatus] = useState<RosStatus>("disconnected");
    const [activeRos, setActiveRos] = useState<ROSLIB.Ros | null>(null);

    const rosRef = useRef<ROSLIB.Ros | null>(null);
    const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const attemptRef = useRef(0);
    const wantConnectedRef = useRef(false);
    const everConnectedRef = useRef(false);

    const clearRetry = useCallback(() => {
        if (retryTimerRef.current) {
            clearTimeout(retryTimerRef.current);
            retryTimerRef.current = null;
        }
    }, []);

    const openConnection = useCallback(async function open(targetUrl: string) {
        const ROSLIB = (await import("roslib")).default;
        if (!wantConnectedRef.current) return;

        const ros = new ROSLIB.Ros({ url: targetUrl });
        rosRef.current = ros;

        ros.on("connection", () => {
            if (rosRef.current !== ros) return;
            attemptRef.current = 0;
            everConnectedRef.current = true;
            setActiveRos(ros);
            setStatus("connected");
        });

        ros.on("error", () => {
            if (rosRef.current !== ros) return;
            if (!everConnectedRef.current) setStatus("error");
        });

        ros.on("close", () => {
            if (rosRef.current !== ros) return;
            setActiveRos(null);

            if (!wantConnectedRef.current || !everConnectedRef.current) {
                setStatus((s) => (s === "error" ? s : "disconnected"));
                return;
            }

            const delay = Math.min(
                BASE_DELAY_MS * 2 ** attemptRef.current,
                MAX_DELAY_MS,
            );
            attemptRef.current += 1;
            setStatus("reconnecting");
            retryTimerRef.current = setTimeout(() => open(targetUrl), delay);
        });
    }, []);

    const connect = useCallback(
        (newUrl: string) => {
            clearRetry();
            const old = rosRef.current;
            rosRef.current = null;
            old?.close();
            setActiveRos(null);

            wantConnectedRef.current = true;
            everConnectedRef.current = false;
            attemptRef.current = 0;

            setConnectedUrl(newUrl);
            try {
                localStorage.setItem(STORAGE_KEY, newUrl);
            } catch (e) {
                console.error("Error saving ROS URL", e);
            }
            setStatus("connecting");
            openConnection(newUrl);
        },
        [clearRetry, openConnection],
    );

    const disconnect = useCallback(() => {
        wantConnectedRef.current = false;
        clearRetry();
        const old = rosRef.current;
        rosRef.current = null;
        old?.close();
        setActiveRos(null);
        setStatus("disconnected");
    }, [clearRetry]);

    useEffect(() => {
        return () => {
            wantConnectedRef.current = false;
            clearRetry();
            rosRef.current?.close();
        };
    }, [clearRetry]);

    const value: RosContextValue = {
        url,
        status,
        ros: activeRos,
        connect,
        disconnect,
    };

    return <RosContext.Provider value={value}>{children}</RosContext.Provider>;
}

export function useRos() {
    const context = useContext(RosContext);
    if (!context) {
        throw new Error("useRos must be used inside RosProvider");
    }
    return context;
}