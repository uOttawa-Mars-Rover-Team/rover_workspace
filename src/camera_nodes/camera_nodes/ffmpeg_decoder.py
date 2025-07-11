# --- SAFE GLOBAL IMPORTS ---
# These can be imported by any module without causing conflicts.
import copy
import queue
from typing import Callable

from ffmpeg_image_transport_msgs.msg import FFMPEGPacket
from sensor_msgs.msg import Image

# --- WE DO NOT IMPORT GSTREAMER, GI, CVBRIDGE, OR NUMPY HERE ---


class FFMPEGDecoder:
    """
    A non-ROS class that decodes FFMPEGPacket messages into sensor_msgs/Image messages.

    This class encapsulates the complex GStreamer pipeline and its initialization,
    ensuring it does not conflict with a parent rclpy application. It requires an
    active rclpy.Node instance to drive its internal event loop via timers.
    """

    def __init__(self, node: "rclpy.node.Node"):
        """
        Initializes the decoder.

        This constructor is lightweight and performs no conflicting library imports.
        The full GStreamer setup is deferred until start() is called.

        :param node: An active rclpy.Node instance, used to create timers.
        """
        print("--- FFMPEGDecoder __init__ started ---")
        self._node = node
        self._output_callback: Callable[[Image], None] = None

        # Initialize all members that will be used by external libraries to None.
        self._pipeline = None
        self._appsrc = None
        self._Gst = None
        self._cv_bridge = None
        self._np = None

        self._decoded_queue = queue.Queue(maxsize=5)
        self._last_header = None
        self._is_started = False

        print(
            "--- FFMPEGDecoder __init__ finished. Call start() to initialize GStreamer. ---"
        )

    def start(self):
        """
        Performs the one-time, deferred initialization of GStreamer and OpenCV.
        This method should be called once after the FFMPEGDecoder is created.
        """
        if self._is_started:
            self._node.get_logger().warn("FFMPEGDecoder start() called more than once.")
            return

        print("--- FFMPEGDecoder.start() called ---")
        try:
            # --- STEP 1: DEFERRED, LOCAL-SCOPED IMPORTS ---
            print("Importing GStreamer, CVBridge, and NumPy libraries locally...")
            import gi

            gi.require_version("Gst", "1.0")
            gi.require_version("GstApp", "1.0")
            import numpy as np
            from cv_bridge import CvBridge
            from gi.repository import GLib, Gst, GstApp

            self._Gst = Gst
            self._cv_bridge = CvBridge()
            self._np = np

            # --- STEP 2: GSTREAMER INITIALIZATION ---
            print("Initializing GStreamer...")
            self._Gst.init(None)

            # --- STEP 3: CREATE TIMERS USING THE PROVIDED ROS NODE ---
            self._glib_context = GLib.MainContext.default()
            self._node.create_timer(0.001, self._glib_tick_callback)
            self._node.create_timer(0.01, self._process_decoded_frames_callback)
            print("GStreamer event loop integration timer created.")

            # --- STEP 4: BUILD THE PIPELINE ---
            pipeline_str = "appsrc name=ros_source ! h264parse ! avdec_h264 ! videoconvert ! video/x-raw,format=BGR ! appsink name=ros_sink"
            self._pipeline = self._Gst.parse_launch(pipeline_str)
            self._appsrc = self._pipeline.get_by_name("ros_source")
            appsink = self._pipeline.get_by_name("ros_sink")

            appsink.set_property("emit-signals", True)
            appsink.set_property("max-buffers", 2)
            appsink.set_property("drop", True)
            appsink.connect("new-sample", self._on_new_gstreamer_sample)

            # --- STEP 5: START THE PIPELINE ---
            ret = self._pipeline.set_state(self._Gst.State.PLAYING)
            if ret == self._Gst.StateChangeReturn.FAILURE:
                self._node.get_logger().fatal(
                    "Unable to set the pipeline to the playing state."
                )
                return

            self._is_started = True
            print("--- FFMPEGDecoder setup complete and is PLAYING. ---")

        except Exception as e:
            self._node.get_logger().fatal(f"Failed during FFMPEGDecoder setup: {e}")

    def on_new_image_message(self, callback: Callable[[Image], None]):
        """
        Registers a callback function to be executed when a new Image is decoded.

        :param callback: A function that accepts one argument of type sensor_msgs.msg.Image.
        """
        if not callable(callback):
            raise TypeError("Provided callback is not a callable function.")
        self._output_callback = callback
        print(f"Registered new image callback: {callback.__name__}")

    def consume(self, ffmpeg_packet: FFMPEGPacket):
        """
        Public method to provide a new FFMPEGPacket to the decoder.
        This should be called from your ROS subscriber's callback.

        :param ffmpeg_packet: The FFMPEGPacket message from the ROS topic.
        """
        if not self._is_started or self._appsrc is None:
            return

        self._last_header = ffmpeg_packet.header
        buf = self._Gst.Buffer.new_wrapped(bytes(ffmpeg_packet.data))
        self._appsrc.emit("push-buffer", buf)

    def destroy(self):
        """Shuts down the GStreamer pipeline cleanly."""
        print("--- FFMPEGDecoder.destroy() called ---")
        if self._pipeline:
            self._pipeline.set_state(self._Gst.State.NULL)
        print("--- FFMPEGDecoder destroyed. ---")

    # --- Internal (Private) Methods ---

    def _glib_tick_callback(self):
        if hasattr(self, "_glib_context") and self._glib_context:
            while self._glib_context.pending():
                self._glib_context.iteration(False)

    def _on_new_gstreamer_sample(self, sink):
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            height = caps.get_structure(0).get_value("height")
            width = caps.get_structure(0).get_value("width")
            success, map_info = buf.map(self._Gst.MapFlags.READ)
            if success:
                data_copy = map_info.data[:]
                buf.unmap(map_info)
                try:
                    frame_data = {
                        "data": data_copy,
                        "height": height,
                        "width": width,
                        "header": copy.deepcopy(self._last_header),
                    }
                    self._decoded_queue.put_nowait(frame_data)
                except queue.Full:
                    pass
            return self._Gst.FlowReturn.OK
        return self._Gst.FlowReturn.ERROR

    def _process_decoded_frames_callback(self):
        try:
            frame_data = self._decoded_queue.get_nowait()

            # Use the locally imported and stored modules
            frame = self._np.ndarray(
                (frame_data["height"], frame_data["width"], 3),
                buffer=frame_data["data"],
                dtype=self._np.uint8,
            )
            image_msg = self._cv_bridge.cv2_to_imgmsg(frame, "bgr8")
            image_msg.header = (
                frame_data["header"]
                if frame_data["header"]
                else self._node.get_clock().now().to_msg()
            )

            # If a callback is registered, call it with the new message
            if self._output_callback:
                self._output_callback(image_msg)

        except queue.Empty:
            pass
