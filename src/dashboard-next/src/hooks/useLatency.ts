import { useEffect, useState } from "react";
import { useRos } from "@/providers/RosProvider";

export function useLatency(intervalMs = 2000) {
    const { ros } = useRos();
    const [latency, setLatency] = useState<number | null>(null);

    useEffect(() => {
        if (!ros) return;

        let cancelled = false;
        let timer: ReturnType<typeof setInterval> | undefined;

        import("roslib").then((mod) => {
            if (cancelled) return;
            const ROSLIB = mod.default;

            const service = new ROSLIB.Service({
                ros,
                name: "/rosapi/get_time",
                serviceType: "rosapi_msgs/srv/GetTime", 
            });

            const ping = () => {
                const start = performance.now();
                service.callService(
                    new ROSLIB.ServiceRequest({}),
                    () => {
                        if (!cancelled) {
                            setLatency(Math.round(performance.now() - start));
                        }
                    },
                    () => {
                        if (!cancelled) setLatency(null);
                    },
                );
            };

            ping();
            timer = setInterval(ping, intervalMs);
        });

        return () => {
            cancelled = true;
            clearInterval(timer);
        };
    }, [ros, intervalMs]);

    return ros ? latency : null;
}