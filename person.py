#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import numpy as np
import message_filters
from vision_msgs.msg import Detection2DArray
import tf2_geometry_msgs


class PersonTFPublisher(Node):
    def __init__(self):
        super().__init__("person_tf_publisher")

        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # CV Bridge for image conversion
        self.bridge = CvBridge()

        # Camera intrinsics
        self.camera_info = None
        self.camera_frame = self.declare_parameter("camera_frame", "camera_link").value
        self.base_frame = self.declare_parameter("base_frame", "base_link").value

        # Subscribe to camera info
        self.camera_info_sub = self.create_subscription(
            CameraInfo,
            "/camera/camera/aligned_depth_to_color/camera_info",
            self.camera_info_callback,
            10,
        )

        # Subscribe to depth image and detections using message filters for synchronization
        self.depth_sub = message_filters.Subscriber(
            self, Image, "/camera/camera/aligned_depth_to_color/image_raw"
        )

        self.detection_sub = message_filters.Subscriber(
            self,
            Detection2DArray,
            "/yolo/detections",  # Adjust topic name based on your YOLO node
        )

        # Synchronize depth and detection messages
        self.sync = message_filters.ApproximateTimeSynchronizer(
            [self.depth_sub, self.detection_sub], 10, 0.1
        )
        self.sync.registerCallback(self.sync_callback)

        self.get_logger().info("Person TF Publisher initialized")

    def camera_info_callback(self, msg):
        self.camera_info = msg

    def sync_callback(self, depth_msg, detection_msg):
        if self.camera_info is None:
            self.get_logger().warn("No camera info received yet")
            return

        # Convert depth image
        try:
            depth_image = self.bridge.imgmsg_to_cv2(
                depth_msg, desired_encoding="passthrough"
            )
        except Exception as e:
            self.get_logger().error(f"Failed to convert depth image: {e}")
            return

        # Process each detection
        person_count = 0
        for detection in detection_msg.detections:
            # Check if detection is a person (class_id depends on your model)
            # For COCO dataset, person class is typically 0
            if (
                len(detection.results) > 0
                and detection.results[0].hypothesis.class_id == "0"
            ):  # Adjust based on your class mapping
                person_count += 1

                # Get bounding box center
                bbox = detection.bbox
                center_x = int(bbox.center.position.x)
                center_y = int(bbox.center.position.y)

                # Get depth at center point
                if (
                    0 <= center_x < depth_image.shape[1]
                    and 0 <= center_y < depth_image.shape[0]
                ):
                    depth = depth_image[center_y, center_x]

                    # Skip if depth is invalid
                    if depth == 0 or np.isnan(depth) or np.isinf(depth):
                        # Try to get average depth in a small region
                        depth = self.get_average_depth(
                            depth_image, center_x, center_y, 10
                        )
                        if depth == 0:
                            continue

                    # Convert pixel to 3D point
                    point_3d = self.pixel_to_3d_point(center_x, center_y, depth)

                    # Publish TF
                    self.publish_person_tf(
                        point_3d, person_count, depth_msg.header.stamp
                    )

    def get_average_depth(self, depth_image, cx, cy, window_size):
        """Get average depth in a window around the center point"""
        x_min = max(0, cx - window_size)
        x_max = min(depth_image.shape[1], cx + window_size)
        y_min = max(0, cy - window_size)
        y_max = min(depth_image.shape[0], cy + window_size)

        roi = depth_image[y_min:y_max, x_min:x_max]
        valid_depths = roi[roi > 0]

        if len(valid_depths) > 0:
            return np.median(valid_depths)
        return 0

    def pixel_to_3d_point(self, u, v, depth):
        """Convert pixel coordinates and depth to 3D point"""
        # Camera intrinsics
        fx = self.camera_info.k[0]
        fy = self.camera_info.k[4]
        cx = self.camera_info.k[2]
        cy = self.camera_info.k[5]

        # Convert depth from mm to meters if necessary
        if depth > 10:  # Assuming depth is in mm if > 10
            depth = depth / 1000.0

        # Calculate 3D coordinates
        x = (u - cx) * depth / fx
        y = (v - cy) * depth / fy
        z = depth

        return [x, y, z]

    def publish_person_tf(self, point_3d, person_id, timestamp):
        """Publish TF for detected person"""
        t = TransformStamped()

        t.header.stamp = timestamp
        t.header.frame_id = self.camera_frame
        t.child_frame_id = f"person_{person_id}"

        t.transform.translation.x = point_3d[2]  # Z in camera frame is forward
        t.transform.translation.y = -point_3d[
            0
        ]  # X in camera frame is right (negate for left)
        t.transform.translation.z = -point_3d[
            1
        ]  # Y in camera frame is down (negate for up)

        # No rotation (person is upright)
        t.transform.rotation.x = 0.0
        t.transform.rotation.y = 0.0
        t.transform.rotation.z = 0.0
        t.transform.rotation.w = 1.0

        self.tf_broadcaster.sendTransform(t)

        self.get_logger().debug(
            f"Published TF for person_{person_id} at "
            f"x={point_3d[2]:.2f}, y={-point_3d[0]:.2f}, z={-point_3d[1]:.2f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = PersonTFPublisher()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
