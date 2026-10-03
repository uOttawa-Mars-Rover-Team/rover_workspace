#!/usr/bin/env python3
"""
RTSP Streaming Server for Jetson — udev + Auto-Negotiation

- Detects USB cameras via udev netlink (no polling)
- Probes each camera at PLAYING state to verify USB bandwidth
- Cascades through resolutions and formats until one works
- Releases cameras when nobody is watching (SUSPEND → RESET)

Dependencies:
    pip install pyudev

Viewing (Windows client):
    gst-launch-1.0 rtspsrc location=rtsp://<JETSON_IP>:8554/FrontCam latency=100 \
      ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink sync=false

  OR with ffplay:
    ffplay -fflags nobuffer -flags low_delay -framedrop \
           -rtsp_transport udp rtsp://<JETSON_IP>:8554/FrontCam
"""

import logging
import re
import signal
import subprocess
import threading
import time
from fractions import Fraction
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import gi
import pyudev

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GLib, Gst, GstRtspServer

# ─── Configuration ────────────────────────────────────────
RTSP_PORT = "8554"
BY_ID_DIR = Path("/dev/v4l/by-id")
SETTLE_DELAY_MS = 1500

BITRATE_BPS = 2_000_000  # raised — 250kbps was too low for H.264
IDR_INTERVAL = 30
MTU = 1400

PROBE_TIMEOUT_NS = 8 * Gst.SECOND
PROBE_BUFFERS = 3
PROBE_SETTLE_S = 0.5

CAPTURE_PREFS: List[Tuple[int, int, str]] = [
    (640, 480, "15/1"),
    (800, 600, "15/1"),
    (1280, 720, "15/1"),  # fallback if 640x480 fails
]

# Format priority at a given resolution — most bandwidth-efficient capture
# codec wins, *then* we pick the framerate closest to CAPTURE_PREFS from
# whatever that codec actually offers. "RAW" covers every raw fourcc the
# device reports (YUYV, NV12, GREY, …) since v4l2src negotiates the pixel
# format itself once width/height/framerate are pinned.
FORMAT_PRIORITY: List[str] = ["H264", "MJPG", "RAW"]

# Rough bytes-per-pixel used only to *rank/gate* candidates, not for exact
# accounting. Good enough to stop us from e.g. picking MJPEG@8K120 over
# RAW@640x480x15 just because MJPEG outranks RAW in FORMAT_PRIORITY.
BANDWIDTH_BYTES_PER_PIXEL: Dict[str, float] = {
    "H264": 0.04,  # camera-side hardware encode — very low bits/pixel
    "MJPG": 0.25,  # motion-JPEG, mid-quality estimate
    "RAW": 2.0,  # uncompressed (YUYV/NV12/etc.) — worst case ~2 bytes/px
}

# Hard ceiling on *estimated* USB capture bandwidth per camera. Candidates
# above this are skipped even if their format/fps would otherwise win.
# ~40MB/s is a conservative shared-bus budget for USB2 Hi-Speed; raise it
# if every camera has its own USB3 controller.
MAX_CAPTURE_MBPS = 40.0

# ── IMPORTANT: Run once, check logs for serial numbers, fill these in ──
# Serial shown in log as:  hint: add to CAMERA_NAMES → "XXXXXXXX": "Name"
CAMERA_NAMES: Dict[str, str] = {
    "0825-BCC0": "FrontCam",  # <── ADD YOUR ACTUAL SERIAL HERE
    # "81BF29DE": "FrontCam",
    # "7B260EE0": "ArmCam",
}

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("rtsp-server")

Gst.init(None)

_probe_lock = threading.Lock()

# ─── Encoder ─────────────────────────────────────────────
# H.264 instead of H.265 — universally supported by clients
# Uses nvv4l2h264enc (Jetson hardware encoder)
_ENCODER = (
    f"nvv4l2h264enc "
    f"bitrate={BITRATE_BPS} peak-bitrate={BITRATE_BPS} "
    f"control-rate=1 preset-level=1 "
    f"iframeinterval={IDR_INTERVAL} "
    f"insert-sps-pps=true insert-vui=true maxperf-enable=true ! "
    f"h264parse ! "
    f"rtph264pay name=pay0 pt=96 config-interval=-1 mtu={MTU}"
)

# ─── Helpers ──────────────────────────────────────────────


def _udev_props(by_id_path: str, ctx: pyudev.Context) -> Tuple[str, str]:
    """Return (serial, model) via udev properties."""
    try:
        real = str(Path(by_id_path).resolve())
        dev = pyudev.Devices.from_device_file(ctx, real)
        serial = dev.get("ID_SERIAL_SHORT", "")
        model = dev.get("ID_MODEL", "")

        # Log ALL properties once so you can identify your camera
        log.debug("udev props for %s:", by_id_path)
        for k, v in dev.items():
            log.debug("  %-35s = %s", k, v)

        return serial, model
    except Exception as e:
        log.debug("udev_props error: %s", e)
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

    # Auto-generate but log it prominently so user can add it
    if model:
        clean = "".join(c if c.isalnum() else "-" for c in model)
        suffix = f"-{serial[-4:]}" if len(serial) >= 4 else ""
        name = f"{clean}{suffix}"
    else:
        name = (
            filename.replace("usb-", "").replace("-video-index0", "").replace("_", "-")
        )

    log.warning('  *** Camera not in CAMERA_NAMES! Auto-name: "%s"', name)
    log.warning('  *** Add to CAMERA_NAMES:  "%s": "YourName"', serial or filename)
    log.warning(
        "  *** Stream URL will be:   rtsp://192.168.1.201:%s/%s", RTSP_PORT, name
    )
    return name


def _is_usable(path: Path) -> bool:
    try:
        return path.resolve(strict=True).is_char_device()
    except (OSError, ValueError):
        return False


# ─── Pipeline probing ────────────────────────────────────


def _probe(launch_str: str) -> bool:
    """
    Build launch_str → fakesink, go to PLAYING, wait for
    PROBE_BUFFERS frames. Returns True only if real frames arrived.
    """
    full = f"{launch_str} ! fakesink num-buffers={PROBE_BUFFERS} sync=false"
    log.debug("    probe pipeline: %s", full)
    pipe = None
    try:
        pipe = Gst.parse_launch(full)
        ret = pipe.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            log.debug("    probe: set_state returned FAILURE")
            return False

        bus = pipe.get_bus()
        msg = bus.timed_pop_filtered(
            PROBE_TIMEOUT_NS,
            Gst.MessageType.EOS | Gst.MessageType.ERROR,
        )
        if msg is None:
            log.debug("    probe: timed out (no EOS/ERROR)")
            return False
        if msg.type == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            log.debug("    probe error: %s | %s", err.message, dbg)
            if dbg and "space" in dbg.lower():
                log.warning("    USB bandwidth exhausted — trying lower res …")
            return False
        return msg.type == Gst.MessageType.EOS

    except GLib.Error as e:
        log.debug("    probe exception: %s", e.message)
        return False
    finally:
        if pipe is not None:
            pipe.set_state(Gst.State.NULL)
            pipe.get_state(3 * Gst.SECOND)


_FOURCC_FAMILY: Dict[str, str] = {
    "H264": "H264",
    "MJPG": "MJPG",
    "MJPEG": "MJPG",
}


def _query_v4l2_caps(dev: str) -> Dict[str, Dict[Tuple[int, int], List[float]]]:
    """
    Query real capture capabilities via `v4l2-ctl --list-formats-ext`,
    grouped into families: H264 / MJPG / RAW (every other raw fourcc —
    YUYV, NV12, GREY, …). Returns {} if v4l2-ctl is missing or the output
    can't be parsed — callers fall back to the old preference-only probing.
    """
    try:
        out = subprocess.run(
            ["v4l2-ctl", "-d", dev, "--list-formats-ext"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
    except Exception as e:
        log.debug("v4l2-ctl caps query failed for %s: %s", dev, e)
        return {}

    caps: Dict[str, Dict[Tuple[int, int], List[float]]] = {}
    family: Optional[str] = None
    size: Optional[Tuple[int, int]] = None

    for line in out.splitlines():
        m = re.search(r"\[\d+\]:\s*'(\w+)'", line)
        if m:
            family = _FOURCC_FAMILY.get(m.group(1), "RAW")
            size = None
            continue
        m = re.search(r"Size:\s*Discrete\s*(\d+)x(\d+)", line)
        if m and family:
            size = (int(m.group(1)), int(m.group(2)))
            continue
        m = re.search(r"\(([\d.]+)\s*fps\)", line)
        if m and family and size:
            caps.setdefault(family, {}).setdefault(size, []).append(float(m.group(1)))

    return caps


def _estimate_mbps(family: str, w: int, h: int, fps: float) -> float:
    bpp = BANDWIDTH_BYTES_PER_PIXEL.get(family, 2.0)
    return (w * h * bpp * fps) / (1024 * 1024)


def _fps_fraction(fps: float) -> str:
    frac = Fraction(fps).limit_denominator(1001)
    return f"{frac.numerator}/{frac.denominator}"


def _family_strategy(
    family: str, w: int, h: int, fps: float, SRC: str, NVMM: str
) -> Tuple[str, str, str]:
    fps_str = _fps_fraction(fps)
    tag = f"{w}x{h}@{fps:g}fps"

    if family == "H264":
        caps = f"video/x-h264,width={w},height={h},framerate={fps_str}"
        return (
            f"H264 {tag}",
            f"{SRC} ! {caps} ! nvv4l2decoder ! nvvidconv ! video/x-raw",
            # Camera already outputs H.264 — parse + payload directly,
            # skipping the decode/re-encode round-trip entirely.
            f"( {SRC} ! {caps} ! h264parse config-interval=1 ! "
            f"rtph264pay name=pay0 pt=96 mtu={MTU} )",
        )
    if family == "MJPG":
        caps = f"image/jpeg,width={w},height={h},framerate={fps_str}"
        return (
            f"MJPG {tag}",
            f"{SRC} ! {caps} ! jpegdec ! videoconvert ! video/x-raw",
            f"( {SRC} ! {caps} ! "
            f"nvv4l2decoder mjpeg=1 ! nvvidconv ! {NVMM} ! {_ENCODER} )",
        )
    caps = f"video/x-raw,width={w},height={h},framerate={fps_str}"
    return (
        f"RAW {tag}",
        f"{SRC} ! {caps}",
        f"( {SRC} ! {caps} ! "
        f"videoconvert ! video/x-raw,format=I420 ! "
        f"nvvidconv ! {NVMM} ! {_ENCODER} )",
    )


def _legacy_pref_strategies(SRC: str, NVMM: str) -> List[Tuple[str, str, str]]:
    """Old exact-fps-only MJPEG/RAW cascade — used only when v4l2-ctl caps
    aren't available, so behaviour still degrades gracefully."""
    strategies: List[Tuple[str, str, str]] = []
    for w, h, fps in CAPTURE_PREFS:
        strategies.append(
            _family_strategy("MJPG", w, h, float(fps.split("/")[0]), SRC, NVMM)
        )
    for w, h, fps in CAPTURE_PREFS:
        strategies.append(
            _family_strategy("RAW", w, h, float(fps.split("/")[0]), SRC, NVMM)
        )
    return strategies


def _find_pipeline(dev: str) -> Optional[Tuple[str, str]]:
    """
    Try capture strategies in order. Returns (label, rtsp_pipeline) or None.

    Strategy order: for each preferred resolution (CAPTURE_PREFS, in order),
    walk FORMAT_PRIORITY (H264 > MJPG > RAW) and take the framerate closest
    to that preference's target that the camera actually offers — skipping
    any candidate whose estimated USB bandwidth exceeds MAX_CAPTURE_MBPS.
    Native fallbacks are tried last, unchanged from before.
    """
    SRC = f"v4l2src device={dev} do-timestamp=true"
    NVMM = "video/x-raw(memory:NVMM),format=NV12"

    caps = _query_v4l2_caps(dev)
    strategies: List[Tuple[str, str, str]] = []

    if caps:
        for w, h, fps_pref in CAPTURE_PREFS:
            target_fps = float(fps_pref.split("/")[0])
            for family in FORMAT_PRIORITY:
                available = caps.get(family, {}).get((w, h))
                if not available:
                    continue
                for fps in sorted(set(available), key=lambda f: abs(f - target_fps)):
                    est = _estimate_mbps(family, w, h, fps)
                    if est > MAX_CAPTURE_MBPS:
                        log.debug(
                            "    skip %s %dx%d@%gfps — est. %.1f MB/s exceeds cap",
                            family,
                            w,
                            h,
                            fps,
                            est,
                        )
                        continue
                    strategies.append(_family_strategy(family, w, h, fps, SRC, NVMM))
                    break  # closest-fitting fps for this resolution/format only
    else:
        log.warning(
            "    v4l2-ctl caps unavailable for %s (install v4l-utils?) — "
            "falling back to exact-fps probing",
            dev,
        )
        strategies.extend(_legacy_pref_strategies(SRC, NVMM))

    # ── Native fallbacks ──────────────────────────────────
    strategies.append(
        (
            "MJPEG native",
            f"{SRC} ! image/jpeg ! jpegdec ! videoconvert ! video/x-raw",
            f"( {SRC} ! image/jpeg ! "
            f"nvv4l2decoder mjpeg=1 ! nvvidconv ! {NVMM} ! {_ENCODER} )",
        )
    )
    strategies.append(
        (
            "RAW native",
            f"{SRC} ! video/x-raw",
            f"( {SRC} ! video/x-raw ! "
            f"videoconvert ! video/x-raw,format=I420 ! "
            f"nvvidconv ! {NVMM} ! {_ENCODER} )",
        )
    )

    for label, probe_cmd, pipeline in strategies:
        log.info("    probe  %-28s %s", label, probe_cmd)
        if _probe(probe_cmd):
            log.info("    ✓ selected: %s", label)
            return label, pipeline
        time.sleep(PROBE_SETTLE_S)

    return None


# ─── Stream bookkeeping ──────────────────────────────────


class CameraStream:
    __slots__ = ("device", "name", "mount", "mode", "serial", "added_at")

    def __init__(self, device: str, name: str, mount: str, mode: str, serial: str):
        self.device = device
        self.name = name
        self.mount = mount
        self.mode = mode
        self.serial = serial
        self.added_at = time.monotonic()

    def __repr__(self) -> str:
        return f"<CameraStream {self.name!r} [{self.mode}] @ {self.device}>"


# ─── RTSP Manager ────────────────────────────────────────


class RTSPManager:
    def __init__(self, port: str = RTSP_PORT):
        self._port = port
        self._loop = GLib.MainLoop()
        self._server = GstRtspServer.RTSPServer()
        self._server.set_service(port)
        self._mounts = self._server.get_mount_points()

        self._streams: Dict[str, CameraStream] = {}
        self._pending: set = set()
        self._rescan_pending = False

        self._udev_ctx = pyudev.Context()
        self._udev_mon = pyudev.Monitor.from_netlink(self._udev_ctx)
        self._udev_mon.filter_by(subsystem="video4linux")

    # ── add / remove ──────────────────────────────────────

    def _add(self, device_path: str) -> None:
        serial, model = _udev_props(device_path, self._udev_ctx)
        name = _resolve_name(device_path, serial, model)
        mount = f"/{name}"

        if mount in self._streams or mount in self._pending:
            return

        log.info(
            "Discovered %-20s  serial=%-14s  model=%s",
            name,
            serial or "—",
            model or "—",
        )
        if serial and serial not in CAMERA_NAMES:
            log.info(
                '  hint: add to CAMERA_NAMES  →  "%s": "%s"',
                serial,
                name,
            )

        self._pending.add(mount)
        threading.Thread(
            target=self._probe_and_mount,
            args=(device_path, name, mount, serial),
            daemon=True,
            name=f"probe-{name}",
        ).start()

    def _probe_and_mount(
        self, device_path: str, name: str, mount: str, serial: str
    ) -> None:
        with _probe_lock:
            result = _find_pipeline(device_path)

        if result is None:
            log.warning("✗ No working pipeline for %s — skipped", name)
            GLib.idle_add(self._pending.discard, mount)
            return

        label, pipeline = result
        GLib.idle_add(
            self._mount,
            device_path,
            name,
            mount,
            pipeline,
            label,
            serial,
        )

    def _mount(
        self,
        device_path: str,
        name: str,
        mount: str,
        pipeline: str,
        label: str,
        serial: str,
    ) -> int:
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
        factory.set_suspend_mode(GstRtspServer.RTSPSuspendMode.RESET)

        factory.connect(
            "media-configure",
            lambda _f, media, n=name: self._on_media_configure(media, n),
        )

        self._mounts.add_factory(mount, factory)
        self._streams[mount] = CameraStream(
            device_path,
            name,
            mount,
            label,
            serial,
        )
        log.info(
            "+ %-20s  rtsp://192.168.1.201:%s%-22s  [%s]",
            name,
            self._port,
            mount,
            label,
        )
        log.info(
            "  Windows client:  "
            "gst-launch-1.0 rtspsrc location=rtsp://192.168.1.201:%s%s latency=100 "
            "! rtph264depay ! h264parse ! avdec_h264 "
            "! videoconvert ! autovideosink sync=false",
            self._port,
            mount,
        )
        return GLib.SOURCE_REMOVE

    def _remove(self, mount: str) -> None:
        stream = self._streams.pop(mount, None)
        if stream is None:
            return
        self._mounts.remove_factory(mount)
        log.info("- %-20s  (was %s)", stream.name, stream.device)

    # ── media bus monitor ─────────────────────────────────

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
                if dbg and "space" in dbg.lower():
                    log.error(
                        "[%s]   ⚠ USB bandwidth exhausted — "
                        "try USB 3.0, lower resolution, or separate controllers",
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

    # ── device sync ───────────────────────────────────────

    def _sync_devices(self) -> None:
        self._rescan_pending = False

        if not BY_ID_DIR.exists():
            for mount in list(self._streams):
                self._remove(mount)
            return

        current = {
            str(p) for p in BY_ID_DIR.iterdir() if "index0" in p.name and _is_usable(p)
        }
        known = {s.device for s in self._streams.values()}

        for dev in sorted(current - known):
            self._add(dev)

        stale = [m for m, s in self._streams.items() if s.device not in current]
        for mount in stale:
            self._remove(mount)

    # ── udev events ───────────────────────────────────────

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

    # ── lifecycle ─────────────────────────────────────────

    def start(self) -> None:
        for sig in (signal.SIGINT, signal.SIGTERM):
            GLib.unix_signal_add(GLib.PRIORITY_HIGH, sig, self._shutdown)

        self._udev_mon.start()
        channel = GLib.IOChannel.unix_new(self._udev_mon.fileno())
        GLib.io_add_watch(
            channel,
            GLib.PRIORITY_DEFAULT,
            GLib.IOCondition.IN,
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
