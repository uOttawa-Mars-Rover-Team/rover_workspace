import cv2
import rclpy
import rclpy.qos
from cv_bridge import CvBridge
from sensor_msgs.msg import CompressedImage, Image

from .common import CameraNode


class CameraPublisherNode(CameraNode):
    def __init__(self, node_name: str = "camera_publisher"):
        super().__init__(node_name)

        self.camera_name = self.get_param(
            "camera_name", rclpy.Parameter.Type.STRING, "usb_cam"
        )
        self.video_device = self.get_param(
            "video_device", rclpy.Parameter.Type.STRING, "/dev/video0"
        )
        self.framerate = self.get_param("framerate", rclpy.Parameter.Type.INTEGER, 15)
        compression_quality = self.get_param(
            "compression_quality", rclpy.Parameter.Type.INTEGER, 20
        )
        self.compression_quality = min(100, compression_quality)
        self.compression_quality = max(1, self.compression_quality)
        if compression_quality != self.compression_quality:
            self.get_logger().info(
                f"Overriding use of compression_quality to {self.compression_quality}."
            )
        self.codec = self.get_param("codec", rclpy.Parameter.Type.STRING, "MJPG")
        if len(self.codec) != 4:
            raise ValueError("The codec must have a length of 4.")

        self.bridge = CvBridge()

        self.qos_profile_raw = self.get_param(
            "qos_profile_raw", rclpy.Parameter.Type.STRING, "SENSOR_DATA"
        )
        qos_raw = rclpy.qos.QoSPresetProfiles.get_from_short_key(self.qos_profile_raw)
        self.qos_profile_compressed = self.get_param(
            "qos_profile_compressed", rclpy.Parameter.Type.STRING, "SENSOR_DATA"
        )
        qos_compressed = rclpy.qos.QoSPresetProfiles.get_from_short_key(
            self.qos_profile_compressed
        )

        self.publisher = self.create_publisher(
            Image, f"{self.camera_name}/image_raw", qos_raw
        )
        # Create a publisher for compressed image
        self.compressed_publisher = self.create_publisher(
            CompressedImage, f"{self.camera_name}/image_raw/compressed", qos_compressed
        )

        # Initialize OpenCV capture
        self.cap = cv2.VideoCapture(self.video_device)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*self.codec))

        self.resolution = self.get_param(
            "resolution", rclpy.Parameter.Type.INTEGER, 480
        )
        resolution_map = {
            240: 320,
            480: 640,
            720: 1280,
            1080: 1920,
        }
        default_resolution = 480
        if self.resolution not in resolution_map:
            self.get_logger().error(
                f"Given invalid resolution of {self.resolution}. Using {default_resolution}."
            )

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution_map[self.resolution])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution)
        if not self.cap.isOpened():
            self.get_logger().error("Failed to open camera!")
            raise RuntimeError("Failed to open camera!")

        # Create a timer to periodically capture and publish images
        self.timer = self.create_timer(1 / self.framerate, self.timer_callback)

    def timer_callback(self):
        # Capture frame-by-frame
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error("Failed to capture image!")
            return

        img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        img_msg.header.stamp = self.get_clock().now().to_msg()
        img_msg.header.frame_id = self.camera_name

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.compression_quality]
        ret, jpeg_arr = cv2.imencode(".jpg", frame, encode_param)
        if not ret:
            self.get_logger().error("JPEG encoding failed!")
            return

        compressed_msg = CompressedImage()
        compressed_msg.header = img_msg.header
        compressed_msg.format = "jpeg"
        # jpeg_arr is a 1-D np.uint8 array of bytes; we need a Python bytes object
        compressed_msg.data = jpeg_arr.tobytes()

        # Publish the message
        self.publisher.publish(img_msg)
        self.compressed_publisher.publish(compressed_msg)
        self.get_logger().info(f"Publishing image at {self.publisher.topic_name}")
        self.get_logger().info(
            f"Publishing compressed image at {self.compressed_publisher.topic_name}"
        )

    def __del__(self):
        # Release the camera when the node is destroyed
        if self.cap.isOpened():
            self.cap.release()


def main(args=None):
    rclpy.init(args=args)
    camera_publisher_node = CameraPublisherNode()
    rclpy.spin(camera_publisher_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
