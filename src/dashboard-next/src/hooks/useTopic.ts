import { useEffect, useState } from "react";
import type ROSLIB from "roslib";
import { useRos } from "@/providers/RosProvider";

export function useTopic<T>(name: string, messageType: string) {
    const { ros } = useRos();
    const [message, setMessage] = useState<T | null>(null);

    useEffect(() => {
        if (!ros) return;

        let topic: ROSLIB.Topic | null = null;
        let cancelled = false;

        import("roslib").then((mod) => {
            if (cancelled) return;
            const ROSLIB = mod.default;
            topic = new ROSLIB.Topic({ ros, name, messageType });
            topic.subscribe((msg) => setMessage(msg as unknown as T));
        });

        return () => {
            cancelled = true;
            topic?.unsubscribe();
        };
    }, [ros, name, messageType]);

    return message;
}