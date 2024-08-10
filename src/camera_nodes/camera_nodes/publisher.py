import cv2
import rclpy
from sensor_msgs.msg import CompressedImage

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
        self.framerate = self.get_param("framerate", rclpy.Parameter.Type.INTEGER, 30)
        compression_quality = self.get_param(
            "compression_quality", rclpy.Parameter.Type.INTEGER, 20
        )
        self.compression_quality = min(100, compression_quality)
        self.compression_quality = max(1, self.compression_quality)
        if compression_quality != self.compression_quality:
            self.get_logger().info(
                f"Overriding use of compression_quality to {self.compression_quality}."
            )

        # Create a publisher for compressed image
        self.publisher = self.create_publisher(
            CompressedImage, f"{self.camera_name}/image_raw/compressed", self.framerate
        )

        # Initialize OpenCV capture
        self.cap = cv2.VideoCapture(self.video_device)
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

        # Convert the frame to a ROS CompressedImage message
        # Encode the image to JPEG format
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.compression_quality]
        ret, encoded_image = cv2.imencode(".jpg", frame, encode_param)
        if not ret:
            self.get_logger().error("Failed to encode and compress image!")
            return

        # Create CompressedImage message
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = f"{self.camera_name}"
        msg.format = "jpeg"
        msg.data = encoded_image.tobytes()

        # Publish the message
        self.publisher.publish(msg)
        self.get_logger().info(
            f"Publishing compressed image at {self.publisher.topic_name}"
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
