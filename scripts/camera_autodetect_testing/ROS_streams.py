#ROS2 Implementation that works and is tested.


import os
import re
import signal
import subprocess
import time
import threading
from pathlib import Path
from dataclasses import dataclass

# change after ben asks me to
HEALTH_CHECK_INTERVAL = 10
MAX_RESTART_ATTEMPTS = 1
FRAME_TIMEOUT = 2
HOTPLUG_CHECK_INTERVAL = 1

BY_ID_DIR = Path("/dev/v4l/by-id")

import rclpy
from rclpy.node import Node
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


def get_connected_cameras():
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
    print(f"Launching: {camera_name}")
    # Put each launch in its own process group so we can stop the whole tree
    return subprocess.Popen(
        cmd, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def stop_process_tree(proc: subprocess.Popen, timeout=2):
    # Check if already dead
    if proc.poll() is not None:
        return

    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return

    # Use SIGKILL (force) - this WILL work or else ill be very sad
    try:
        print(f"Force killing process group {pgid}")
        os.killpg(pgid, signal.SIGKILL)
        proc.wait(timeout=1)  # SIGKILL is instant
    except ProcessLookupError:
        pass  # Already dead
    except Exception as e:
        print(f"Failed to kill process: IDK WHY BRO I HATE CODING")


@dataclass  # dont have to make a class with init and stuff like that cuz im lazy  cuz its only initalization
class CameraInfo:
    symlink_name: str
    camera_name: str
    proc: subprocess.Popen
    restart_count: int = 0
    startup_time: float = 0


class ImageMonitor:  # cant use @dataclass cuz of it being complicated and its my first time using @dataclass
    def __init__(self):
        self.last_frames = {}
        self.resolutions = {}
        self.subscriptions = {}
        self.lock = threading.Lock()
        self.node = None
        self.running = False

    def start(self):
        if self.running:
            return

        rclpy.init(args=None)
        self.node = Node("camera_health_monitor")
        executor = SingleThreadedExecutor()
        executor.add_node(self.node)
        self.running = True

        def ros_spin():
            while self.running and rclpy.ok():
                executor.spin_once(timeout_sec=0.1)

        # keep the thread running not killing it like the other code
        threading.Thread(target=ros_spin, daemon=True).start()

    def add_camera(self, camera_name: str):
        with self.lock:
            if camera_name in self.subscriptions:
                return

        def make_callback(name):
            def on_image(msg: Image):
                with self.lock:
                    self.last_frames[name] = time.monotonic()
                    self.resolutions[name] = (msg.width, msg.height)

            return on_image

        topic = f"/{camera_name}/image_raw"
        sub = self.node.create_subscription(
            Image,
            topic,
            make_callback(camera_name),
            qos_profile=qos_profile_sensor_data,
        )

        with self.lock:
            self.subscriptions[camera_name] = sub

    def remove_camera(
        self, camera_name: str
    ):  # removes camera when wanted (can be called in future if needed)
        with self.lock:
            if camera_name in self.subscriptions:
                self.node.destroy_subscription(self.subscriptions[camera_name])
                del self.subscriptions[camera_name]
            if camera_name in self.last_frames:
                del self.last_frames[camera_name]
            if camera_name in self.resolutions:
                del self.resolutions[camera_name]

    def get_frame_age(
        self, camera_name: str
    ):  # needed for figure out if camera freezes or dies
        with self.lock:
            if camera_name not in self.last_frames:
                return None
            return time.monotonic() - self.last_frames[camera_name]

    def get_resolution(self, camera_name: str):
        with self.lock:
            return self.resolutions.get(camera_name)

    def shutdown(self):  # kills when wanted
        self.running = False
        if self.node:
            self.node.destroy_node()
        rclpy.shutdown()


class CameraManager:  # manages cameras and their processes
    def __init__(self, monitor):
        self.monitor = monitor
        self.cameras = {}
        self.lock = threading.RLock()
        self.running = False

    def add_camera(self, symlink_name):
        with self.lock:
            if symlink_name in self.cameras:
                return

            camera_name = sanitize_name_for_ros(symlink_name)
            proc = launch_camera(symlink_name)

            cam = CameraInfo(
                symlink_name=symlink_name,
                camera_name=camera_name,
                proc=proc,
                startup_time=time.monotonic(),
            )

            self.cameras[symlink_name] = cam
            self.monitor.add_camera(camera_name)

    def remove_camera(self, symlink_name):  # removes camera when unplugged
        with self.lock:
            if symlink_name not in self.cameras:
                return

            cam = self.cameras[symlink_name]
            stop_process_tree(cam.proc)
            self.monitor.remove_camera(cam.camera_name)
            del self.cameras[symlink_name]

    def restart_camera(self, symlink_name):  # restarts camera when needed
        with self.lock:
            if symlink_name not in self.cameras:
                return

            cam = self.cameras[symlink_name]

            # Stop trying after max attempts
            if cam.restart_count >= MAX_RESTART_ATTEMPTS:
                print(
                    f"{cam.camera_name} max restarts, lol the camera is dead (surya did it)"
                )
                return

            print(f"Restarting {cam.camera_name}")
            stop_process_tree(cam.proc)

            cam.proc = launch_camera(symlink_name)
            cam.restart_count += 1
            cam.startup_time = time.monotonic()

    def check_hotplug(self):
        # Check for new or removed cameras
        current_cameras = set(get_connected_cameras())

        with self.lock:
            existing_cameras = set(self.cameras.keys())

        # Add new cameras
        for symlink in current_cameras - existing_cameras:
            print(f"New camera detected: {symlink}")
            self.add_camera(symlink)

        # Remove unplugged cameras
        for symlink in existing_cameras - current_cameras:
            print(f"Camera disconnected: {symlink}")
            self.remove_camera(symlink)

    def health_check(self):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] Camera health:")

        with self.lock:
            if not self.cameras:
                print("  No cameras")
                return

            for symlink, cam in list(self.cameras.items()):
                # Check if process is alive
                if cam.proc.poll() is not None:
                    print(f"  - {cam.camera_name}: DEAD")
                    self.restart_camera(symlink)
                    continue

                # Give camera time to start up
                if time.monotonic() - cam.startup_time < 3:
                    print(f"  - {cam.camera_name}: STARTING")
                    continue

                # Check if getting frames
                frame_age = self.monitor.get_frame_age(cam.camera_name)
                resolution = self.monitor.get_resolution(cam.camera_name)

                if frame_age is not None and frame_age < FRAME_TIMEOUT:
                    res_str = (
                        f"{resolution[0]}x{resolution[1]}" if resolution else "unknown"
                    )
                    print(
                        f"  - {cam.camera_name}: Working, resolution={res_str}, age={frame_age:.1f}s, restarts(attempted)={cam.restart_count}"
                    )
                else:
                    print(f"  - {cam.camera_name}: nothing to view (no video frames)")
                    self.restart_camera(symlink)

    def start(self):
        if self.running:
            return

        self.running = True

        # Add cameras that are already connected
        for symlink in get_connected_cameras():
            self.add_camera(symlink)

        # Start health check loop
        def health_loop():
            while self.running:
                self.health_check()
                time.sleep(HEALTH_CHECK_INTERVAL)

        def hotplug_loop():
            while self.running:
                time.sleep(HOTPLUG_CHECK_INTERVAL)
                self.check_hotplug()

        threading.Thread(target=health_loop, daemon=True).start()
        threading.Thread(target=hotplug_loop, daemon=True).start()

    def stop(self):
        self.running = False
        with self.lock:
            for symlink in list(self.cameras.keys()):
                self.remove_camera(symlink)


def main():
    # Start the ROS monitor (runs in background thread)
    monitor = ImageMonitor()
    monitor.start()

    # Start camera manager
    manager = CameraManager(monitor)
    manager.start()

    try:
        # Run until interrupted
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping camera processes")
    finally:
        manager.stop()
        monitor.shutdown()


if __name__ == "__main__":
    main()
