import os
import re
import signal
import subprocess
import time
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

BY_ID_DIR = Path("/dev/v4l/by-id")

try:
    import rclpy
    from rclpy.node import Node
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    ROS_AVAILABLE = True
except Exception:
    ROS_AVAILABLE = False
    rclpy = None
    Node = None
    SingleThreadedExecutor = None
    Image = None
    qos_profile_sensor_data = None


def get_connected_cameras() -> List[str]:
    if not BY_ID_DIR.exists():
        print(f"{BY_ID_DIR} does not exist")
        return []
    # pick one node per physical camera
    return sorted(p.name for p in BY_ID_DIR.glob("*-video-index0"))


def sanitize_name_for_ros(name: str) -> str:
    # Keep alnum and underscores; replace others with underscores
    s = re.sub(r"[^A-Za-z0-9_]", "_", name)
    # Ensure it starts with a letter
    if not re.match(r"^[A-Za-z]", s):
        s = f"cam_{s}"
    return s


def launch_camera(symlink_name: str) -> subprocess.Popen:
    camera_name = sanitize_name_for_ros(symlink_name)
    cmd = [
        "ros2",
        "launch",
        "camera_nodes",
        "ffmpeg.launch.py",
        f"video_device:=/dev/v4l/by-id/{symlink_name}",
        f"camera_name:={camera_name}",
    ]
    print(f"Launching: {cmd}")

    return subprocess.Popen(
        cmd, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def stop_process_tree(proc: subprocess.Popen, sig=signal.SIGINT, timeout=5):
    try:

        os.killpg(proc.pid, sig)
    except ProcessLookupError:
        return
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGTERM)
            proc.wait(timeout=timeout)
        except Exception:
            proc.kill()


class RosImageMonitor:
    def __init__(self, camera_names: List[str], topic_suffixes: Optional[List[str]] = None):
        self.camera_names = camera_names
        # Try common suffixes; adjust if your pipeline uses different topics
        self.topic_suffixes = topic_suffixes or ["image_raw", "image"]
        self._lock = threading.Lock()
        self._last_frame: Dict[str, float] = {}
        self._resolutions: Dict[str, Tuple[int, int]] = {}
        self.enabled = ROS_AVAILABLE

        self._node = None
        self._executor = None
        self._thread = None

    def start(self):
        if not self.enabled:
            print("ROS 2 (rclpy) not available; health checks will only report process status.")
            return
        rclpy.init(args=None)
        self._node = Node("camera_health_monitor")
        self._executor = SingleThreadedExecutor()

        def make_cb(cname: str):
            def _cb(msg: Image):
                with self._lock:
                    self._last_frame[cname] = time.monotonic()
                    w = int(getattr(msg, "width", 0) or 0)
                    h = int(getattr(msg, "height", 0) or 0)
                    if w > 0 and h > 0:
                        self._resolutions[cname] = (w, h)
            return _cb

        for cname in self.camera_names:
            for suffix in self.topic_suffixes:
                topic = f"/{cname}/{suffix}"
                try:
                    self._node.create_subscription(Image, topic, make_cb(cname), qos_profile=qos_profile_sensor_data)
                except Exception:
                    pass

        self._executor.add_node(self._node)

        def spin():
            try:
                while rclpy.ok():
                    self._executor.spin_once(timeout_sec=0.1)
            except Exception:
                pass

        self._thread = threading.Thread(target=spin, daemon=True)
        self._thread.start()

    def get_last_frame_age(self, camera_name: str) -> Optional[float]:
        with self._lock:
            t = self._last_frame.get(camera_name)
        if t is None:
            return None
        return time.monotonic() - t

    def get_resolution(self, camera_name: str) -> Optional[Tuple[int, int]]:
        with self._lock:
            return self._resolutions.get(camera_name)

    def shutdown(self):
        if not self.enabled:
            return
        try:
            if self._executor and self._node:
                self._executor.remove_node(self._node)
            if self._node:
                self._node.destroy_node()
        except Exception:
            pass
        try:
            rclpy.shutdown()
        except Exception:
            pass


@dataclass
class CamProc:
    symlink_name: str
    camera_name: str
    device_path: str
    proc: subprocess.Popen


def health_check(cam_procs: List[CamProc], monitor: Optional[RosImageMonitor], fresh_threshold: float = 10.0):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Camera health:")
    for cp in cam_procs:
        alive = cp.proc.poll() is None
        status = "DOWN"
        res_text = "unknown"

        if alive:
            fresh = False
            if monitor and monitor.enabled:
                age = monitor.get_last_frame_age(cp.camera_name)
                if age is not None and age <= fresh_threshold:
                    fresh = True
                res = monitor.get_resolution(cp.camera_name)
                if res:
                    res_text = f"{res[0]}x{res[1]}"
            status = "OK" if fresh else "RUNNING (no recent frames)"

        print(f"  - {cp.camera_name}: {status}, resolution={res_text}")


def main():
    cam_symlinks = get_connected_cameras()
    if not cam_symlinks:
        print("No cameras found.")
        return

    cam_procs: List[CamProc] = []
    for symlink in cam_symlinks:
        p = launch_camera(symlink)
        cam_name = sanitize_name_for_ros(symlink)
        cam_procs.append(
            CamProc(
                symlink_name=symlink,
                camera_name=cam_name,
                device_path=str(BY_ID_DIR / symlink),
                proc=p,
            )
        )

    # Start ROS monitor
    monitor = RosImageMonitor([cp.camera_name for cp in cam_procs])
    monitor.start()

    try:
        while True:
            time.sleep(30)
            health_check(cam_procs, monitor)
    except KeyboardInterrupt:
        print("Stopping camera processes...")
    finally:
        monitor.shutdown()
        for cp in cam_procs:
            stop_process_tree(cp.proc)


if __name__ == "__main__":
    main()