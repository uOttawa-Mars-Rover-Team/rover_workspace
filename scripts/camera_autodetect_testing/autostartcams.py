
# --- HOW TO VIEW STREAMS ---
#
# 1. VIEW ON LAPTOP (Low Latency for Radio):
#    ffplay -fflags nobuffer -flags low_delay -framedrop -rtsp_transport udp rtsp://<JETSON_IP>:8554/FrontCam
#
# 2. VIEW ON JETSON (Local Debugging):
#    gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/FrontCam latency=0 ! rtph264depay ! h264parse ! nvv4l2decoder ! nvvidconv ! autovideosink
#

import sys
import os
import time
import gi
import threading
from pathlib import Path

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

RTSP_PORT = "8554"
CHECK_INTERVAL_MS = 5000 
BY_ID_DIR = Path("/dev/v4l/by-id")

BITRATE_KBIT = 600
FRAMERATE = "15/1"
MTU_SIZE = 1400

CAMERA_NAMES = {
    "usb-Logitech_Webcam_C920_HD_Pro_ABCD123-video-index0": "FrontCam",
    "usb-046d_0825_2F209020-video-index0": "ArmCam",
}

Gst.init(None)

def sanitize_name(name):
    return name.replace("usb-", "").replace("-video-index0", "").replace("_", "")

class RTSPManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.loop = GLib.MainLoop()
        
        self.server = GstRtspServer.RTSPServer()
        self.server.set_service(RTSP_PORT)
        self.mounts = self.server.get_mount_points()
        
        self.cameras = {} 
        
        GLib.timeout_add(CHECK_INTERVAL_MS, self.check_hotplug)

    def create_factory(self, device_path):
        pipeline = (
            f"( v4l2src device={device_path} ! "
            f"video/x-raw,width=640,height=480,framerate={FRAMERATE} ! "
            f"videoconvert ! "
            f"x264enc tune=zerolatency speed-preset=ultrafast "
            f"bitrate={BITRATE_KBIT} vbv-maxrate={BITRATE_KBIT} vbv-bufsize={BITRATE_KBIT//2} "
            f"intra-refresh=true sliced-threads=true key-int-max=30 ! "
            f"video/x-h264, profile=baseline ! "
            f"h264parse ! "
            f"rtph264pay name=pay0 pt=96 config-interval=-1 mtu={MTU_SIZE} )"
        )

        factory = GstRtspServer.RTSPMediaFactory()
        factory.set_launch(pipeline)
        factory.set_shared(True)
        factory.set_latency(0)
        factory.set_suspend_mode(GstRtspServer.RTSPSuspendMode.NONE)
        return factory

    def add_camera(self, device_path):
        filename = Path(device_path).name
        name = CAMERA_NAMES.get(filename, sanitize_name(filename))
        mount_path = f"/{name}"

        if mount_path in self.cameras: return

        print(f"Adding Stream: rtsp://<IP>:{RTSP_PORT}{mount_path}")
        factory = self.create_factory(device_path)
        self.mounts.add_factory(mount_path, factory)
        
        self.cameras[mount_path] = {
            "device": device_path,
            "camera_name": name,
            "startup_time": time.monotonic()
        }

    def remove_camera(self, mount_path):
        if mount_path in self.cameras:
            print(f"Removing Stream: {mount_path}")
            self.mounts.remove_factory(mount_path)
            del self.cameras[mount_path]

    def check_hotplug(self):
        if not BY_ID_DIR.exists(): 
            return True
        
        current_devs = sorted([str(f) for f in BY_ID_DIR.iterdir() if "index0" in f.name])
        active_devs = {d["device"] for d in self.cameras.values()}

        for dev in set(current_devs) - active_devs:
            self.add_camera(dev)
            
        to_remove = [m for m, d in self.cameras.items() if d["device"] not in current_devs]
        for m in to_remove:
            self.remove_camera(m)
            
        return True 

    def start(self):
        print(f"RTSP Server Started on Port: {RTSP_PORT}")
        self.check_hotplug() 
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.loop.quit()

if __name__ == "__main__":
    mgr = RTSPManager()
    mgr.start()