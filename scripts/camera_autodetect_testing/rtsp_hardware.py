#!/usr/bin/env python3
"""
RTSP Streaming Server for Jetson — udev + Auto-Negotiation
 
- Detects USB cameras via udev netlink (no polling)
- Probes each camera at PLAYING state to verify USB bandwidth
- Cascades through resolutions and formats until one works
- Releases cameras when nobody is watching (SUSPEND → RESET)
 
Dependencies:
    pip install pyudev
 
Viewing:
  Laptop (low-latency):
    ffplay -fflags nobuffer -flags low_delay -framedrop \
           -rtsp_transport udp rtsp://<JETSON_IP>:8554/<CamName>
 
  Jetson (local debug):
    gst-launch-1.0 rtspsrc location=rtsp://127.0.0.1:8554/<CamName> latency=0 \
      ! rtph265depay ! h265parse ! nvv4l2decoder ! nvvidconv ! autovideosink
"""
 
import signal
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
 
import pyudev
 
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst, GstRtspServer, GLib
 
# ─── Configuration ────────────────────────────────────────
RTSP_PORT       = "8554"
BY_ID_DIR       = Path("/dev/v4l/by-id")
SETTLE_DELAY_MS = 1500
 
BITRATE_BPS     = 250_000
IDR_INTERVAL    = 30
MTU             = 1400
 
PROBE_TIMEOUT_NS = 8 * Gst.SECOND      # max wait per strategy
PROBE_BUFFERS    = 3                    # frames to capture during probe
PROBE_SETTLE_S   = 0.5                  # pause between failed probes
 
# Resolutions tried in order — first working match wins.
# MJPEG is attempted at every resolution first (less USB bandwidth),
# then RAW is attempted at every resolution.
CAPTURE_PREFS: List[Tuple[int, int, str]] = [
    (640,  480, "15/1"),
]
 
# Map camera serial (ID_SERIAL_SHORT) → friendly stream name.
# Run once with cameras plugged in, check the log for serial numbers,
# then fill this in.
CAMERA_NAMES: Dict[str, str] = {
    "81BF29DE": "FrontCam",
    "7B260EE0": "ArmCam",
}
 
# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rtsp-server")
 
Gst.init(None)
 
# Serialise probes so two cameras don't fight over USB bandwidth
_probe_lock = threading.Lock()
 
# ─── Encoder tail (shared by every pipeline) ─────────────
_ENCODER = (
    f"nvv4l2h265enc "
    f"bitrate={BITRATE_BPS} peak-bitrate={BITRATE_BPS} "
    f"control-rate=1 preset-level=1 "
    f"iframeinterval={IDR_INTERVAL} "
    f"insert-sps-pps=true insert-vui=true maxperf-enable=true ! "
    f"h265parse ! "
    f"rtph265pay name=pay0 pt=96 config-interval=-1 mtu={MTU}"
)
 
 
# ─── Helpers ──────────────────────────────────────────────
 
def _udev_props(by_id_path: str, ctx: pyudev.Context) -> Tuple[str, str]:
    """Return (serial, model) via udev properties."""
    try:
        real = str(Path(by_id_path).resolve())
        dev = pyudev.Devices.from_device_file(ctx, real)
        return dev.get("ID_SERIAL_SHORT", ""), dev.get("ID_MODEL", "")
    except Exception:
        return "", ""
 
 
def _resolve_name(by_id_path: str, serial: str, model: str) -> str:
    """
    Resolve a camera to a friendly, URL-safe stream name.
 
    Lookup cascade:
      1. Full by-id filename in CAMERA_NAMES
      2. Serial number in CAMERA_NAMES
      3. Auto:  <Model>-<last 4 of serial>
      4. Sanitised filename
    """
    filename = Path(by_id_path).name
 
    if filename in CAMERA_NAMES:
        return CAMERA_NAMES[filename]
    if serial and serial in CAMERA_NAMES:
        return CAMERA_NAMES[serial]
    if model:
        clean = model.replace("_", "-")
        suffix = f"-{serial[-4:]}" if len(serial) >= 4 else ""
        return f"{clean}{suffix}"
    return (
        filename
        .replace("usb-", "")
        .replace("-video-index0", "")
        .replace("_", "-")
    )
 
 
def _is_usable(path: Path) -> bool:
    try:
        return path.resolve(strict=True).is_char_device()
    except (OSError, ValueError):
        return False
 
 
# ─── Pipeline probing ────────────────────────────────────
 
def _probe(launch_str: str) -> bool:
    """
    Build *launch_str* → fakesink, go to PLAYING, wait for
    PROBE_BUFFERS frames.  Returns True only if real frames
    were produced (= USB bandwidth is available).
    """
    pipe = None
    try:
        pipe = Gst.parse_launch(
            f"{launch_str} ! fakesink num-buffers={PROBE_BUFFERS} sync=false"
        )
        ret = pipe.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            return False
 
        bus = pipe.get_bus()
        msg = bus.timed_pop_filtered(
            PROBE_TIMEOUT_NS,
            Gst.MessageType.EOS | Gst.MessageType.ERROR,
        )
        if msg is None:
            return False
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            log.debug("    probe error: %s", err.message)
            if "space" in (dbg or "").lower():
                log.warning(
                    "    USB bandwidth exhausted at this setting — "
                    "trying lower resolution …"
                )
            return False
        return msg.type == Gst.MessageType.EOS
 
    except GLib.Error as e:
        log.debug("    probe exception: %s", e.message)
        return False
    finally:
        if pipe is not None:
            pipe.set_state(Gst.State.NULL)
            pipe.get_state(3 * Gst.SECOND)
 
 
def _find_pipeline(dev: str) -> Optional[Tuple[str, str]]:
    """
    Try capture strategies in order.  Returns (label, rtsp_pipeline)
    or None.
 
    Order:
      ① MJPEG at each preferred resolution  (least USB bandwidth)
      ② RAW   at each preferred resolution
      ③ MJPEG native (camera picks its own resolution)
      ④ RAW   native
    """
    SRC  = f"v4l2src device={dev} do-timestamp=true"
    NVMM = "video/x-raw(memory:NVMM),format=NV12"
 
    strategies: List[Tuple[str, str, str]] = []
 
    # ── MJPEG at each preferred resolution ────
    for w, h, fps in CAPTURE_PREFS:
        tag = f"{w}×{h}@{fps.split('/')[0]}fps"
        caps = f"image/jpeg,width={w},height={h},framerate={fps}"
        strategies.append((
            f"MJPEG {tag}",
            f"{SRC} ! {caps} ! nvv4l2decoder mjpeg=1",
            f"( {SRC} ! {caps} ! "
            f"nvv4l2decoder mjpeg=1 ! nvvidconv ! {NVMM} ! {_ENCODER} )",
        ))
 
    # ── RAW at each preferred resolution ──────
    for w, h, fps in CAPTURE_PREFS:
        tag = f"{w}×{h}@{fps.split('/')[0]}fps"
        caps = f"video/x-raw,width={w},height={h},framerate={fps}"
        strategies.append((
            f"RAW {tag}",
            f"{SRC} ! {caps}",
            f"( {SRC} ! {caps} ! "
            f"videoconvert ! video/x-raw,format=I420 ! "
            f"nvvidconv ! {NVMM} ! {_ENCODER} )",
        ))
 
    # ── Native resolution fallbacks ───────────
    strategies.append((
        "MJPEG native",
        f"{SRC} ! image/jpeg ! nvv4l2decoder mjpeg=1",
        f"( {SRC} ! image/jpeg ! "
        f"nvv4l2decoder mjpeg=1 ! nvvidconv ! {NVMM} ! {_ENCODER} )",
    ))
    strategies.append((
        "RAW native",
        f"{SRC} ! video/x-raw",
        f"( {SRC} ! video/x-raw ! "
        f"videoconvert ! video/x-raw,format=I420 ! "
        f"nvvidconv ! {NVMM} ! {_ENCODER} )",
    ))
 
    for label, probe_cmd, pipeline in strategies:
        log.info("    probe  %-24s", label)
        if _probe(probe_cmd):
            log.info("    ✓ selected: %s", label)
            return label, pipeline
        time.sleep(PROBE_SETTLE_S)
 
    return None
 
 
# ─── Stream bookkeeping ──────────────────────────────────
 
class CameraStream:
    __slots__ = ("device", "name", "mount", "mode", "serial", "added_at")
 
    def __init__(self, device: str, name: str, mount: str,
                 mode: str, serial: str):
        self.device   = device
        self.name     = name
        self.mount    = mount
        self.mode     = mode
        self.serial   = serial
        self.added_at = time.monotonic()
 
    def __repr__(self) -> str:
        return f"<CameraStream {self.name!r} [{self.mode}] @ {self.device}>"
 
 
# ─── RTSP Manager ────────────────────────────────────────
 
class RTSPManager:
    def __init__(self, port: str = RTSP_PORT):
        self._port   = port
        self._loop   = GLib.MainLoop()
        self._server = GstRtspServer.RTSPServer()
        self._server.set_service(port)
        self._mounts = self._server.get_mount_points()
 
        self._streams: Dict[str, CameraStream] = {}
        self._pending: set = set()
        self._rescan_pending = False
 
        self._udev_ctx = pyudev.Context()
        self._udev_mon = pyudev.Monitor.from_netlink(self._udev_ctx)
        self._udev_mon.filter_by(subsystem="video4linux")
 
    # ── add / remove ──────────────────────────
 
    def _add(self, device_path: str) -> None:
        serial, model = _udev_props(device_path, self._udev_ctx)
        name  = _resolve_name(device_path, serial, model)
        mount = f"/{name}"
 
        if mount in self._streams or mount in self._pending:
            return
 
        log.info(
            "Discovered %-20s  serial=%-10s  model=%s",
            name, serial or "—", model or "—",
        )
        if serial and serial not in CAMERA_NAMES:
            log.info(
                '  hint: add to CAMERA_NAMES  →  "%s": "%s"',
                serial, name,
            )
 
        self._pending.add(mount)
        threading.Thread(
            target=self._probe_and_mount,
            args=(device_path, name, mount, serial),
            daemon=True,
            name=f"probe-{name}",
        ).start()
 
    def _probe_and_mount(self, device_path: str, name: str,
                         mount: str, serial: str) -> None:
        with _probe_lock:                          # one camera at a time
            result = _find_pipeline(device_path)
 
        if result is None:
            log.warning("✗ No working pipeline for %s — skipped", name)
            GLib.idle_add(self._pending.discard, mount)
            return
 
        label, pipeline = result
        GLib.idle_add(
            self._mount, device_path, name, mount, pipeline, label, serial,
        )
 
    def _mount(self, device_path: str, name: str, mount: str,
               pipeline: str, label: str, serial: str) -> int:
        self._pending.discard(mount)
 
        if mount in self._streams:
            return GLib.SOURCE_REMOVE
        if not Path(device_path).exists():
            log.info("  %s vanished during probe — skipped", name)
            return GLib.SOURCE_REMOVE
 
        factory = GstRtspServer.RTSPMediaFactory()
        factory.set_launch(pipeline)
        factory.set_shared(True)
        factory.set_latency(0)
 
        # RESET releases the camera when nobody is watching,
        # freeing USB bandwidth for other cameras on the same bus.
        factory.set_suspend_mode(GstRtspServer.RTSPSuspendMode.RESET)
 
        factory.connect(
            "media-configure",
            lambda _f, media, n=name: self._on_media_configure(media, n),
        )
 
        self._mounts.add_factory(mount, factory)
        self._streams[mount] = CameraStream(
            device_path, name, mount, label, serial,
        )
        log.info(
            "+ %-20s  rtsp://<IP>:%s%-22s  [%s]",
            name, self._port, mount, label,
        )
        return GLib.SOURCE_REMOVE
 
    def _remove(self, mount: str) -> None:
        stream = self._streams.pop(mount, None)
        if stream is None:
            return
        self._mounts.remove_factory(mount)
        log.info("- %-20s  (was %s)", stream.name, stream.device)
 
    # ── media bus monitor ─────────────────────
 
    @staticmethod
    def _on_media_configure(media, cam_name: str) -> None:
        element = media.get_element()
        bus = element.get_bus()
        bus.add_signal_watch()
 
        def _on_msg(_bus, msg):
            if msg.type == Gst.MessageType.ERROR:
                err, dbg = msg.parse_error()
                log.error("[%s] Pipeline error: %s", cam_name, err.message)
                if dbg:
                    log.debug("[%s]   debug: %s", cam_name, dbg)
                if "space" in (dbg or "").lower():
                    log.error(
                        "[%s]   ⚠ USB bandwidth exhausted — "
                        "try a USB 3.0 port, lower resolution, "
                        "or separate USB controllers",
                        cam_name,
                    )
            elif msg.type == Gst.MessageType.WARNING:
                warn, _ = msg.parse_warning()
                log.warning("[%s] Pipeline warning: %s", cam_name, warn.message)
 
        bus.connect("message", _on_msg)
        log.info("[%s] Client connected", cam_name)
        media.connect(
            "unprepared",
            lambda _, n=cam_name: log.info("[%s] Client disconnected", n),
        )
 
    # ── device sync ───────────────────────────
 
    def _sync_devices(self) -> None:
        self._rescan_pending = False
 
        if not BY_ID_DIR.exists():
            for mount in list(self._streams):
                self._remove(mount)
            return
 
        current = {
            str(p) for p in BY_ID_DIR.iterdir()
            if "index0" in p.name and _is_usable(p)
        }
        known = {s.device for s in self._streams.values()}
 
        for dev in sorted(current - known):
            self._add(dev)
 
        stale = [m for m, s in self._streams.items() if s.device not in current]
        for mount in stale:
            self._remove(mount)
 
    # ── udev events ───────────────────────────
 
    def _schedule_rescan(self) -> None:
        if not self._rescan_pending:
            self._rescan_pending = True
            GLib.timeout_add(SETTLE_DELAY_MS, self._deferred_rescan)
 
    def _deferred_rescan(self) -> bool:
        self._sync_devices()
        return GLib.SOURCE_REMOVE
 
    def _on_udev_event(self, _channel, _condition) -> bool:
        device = self._udev_mon.poll(timeout=0)
        if device is None:
            return True
        log.info("udev  %-8s  %s", device.action, device.device_node or "?")
        if device.action in ("add", "remove", "change", "unbind"):
            self._schedule_rescan()
        return True
 
    # ── lifecycle ─────────────────────────────
 
    def start(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, self._shutdown)
 
        self._udev_mon.start()
        channel = GLib.IOChannel.unix_new(self._udev_mon.fileno())
        GLib.io_add_watch(
            channel, GLib.PRIORITY_DEFAULT, GLib.IOCondition.IN,
            self._on_udev_event,
        )
 
        self._server.attach(None)
        log.info("RTSP server listening on port %s", self._port)
        self._sync_devices()
        self._loop.run()
        log.info("Server shut down cleanly")
 
    def _shutdown(self) -> bool:
        log.info("Signal caught — shutting down …")
        self._loop.quit()
        return GLib.SOURCE_REMOVE
 
 
if __name__ == "__main__":
    RTSPManager().start()