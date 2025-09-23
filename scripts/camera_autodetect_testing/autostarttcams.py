import os
import re
import signal
import subprocess
import time
from pathlib import Path

BY_ID_DIR = Path("/dev/v4l/by-id")


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
    print(f"Launching: {cmd}")

    # Option 1: Discard all output
    return subprocess.Popen(
        cmd, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Option 2: Save output to log files (uncomment if you prefer this)
    # log_dir = Path("camera_logs")
    # log_dir.mkdir(exist_ok=True)
    # with open(log_dir / f"{camera_name}.log", "w") as log_file:
    #     return subprocess.Popen(
    #         cmd,
    #         preexec_fn=os.setsid,
    #         stdout=log_file,
    #         stderr=subprocess.STDOUT
    #     )


def stop_process_tree(proc: subprocess.Popen, sig=signal.SIGINT, timeout=5):
    try:
        # send signal to the whole process group
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


def main():
    procs = []
    cameras = get_connected_cameras()
    if not cameras:
        print("No cameras found.")
        return

    for cam in cameras:
        procs.append(launch_camera(cam))

    try:
        # Let them run for a bit (or replace with while True to run indefinitely)
        while True:
            pass
    except:
        print("Stopping camera processes...")
        for p in procs:
            stop_process_tree(p)


if __name__ == "__main__":
    main()
