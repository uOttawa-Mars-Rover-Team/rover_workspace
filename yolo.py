#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from vision_msgs.msg import (
    Detection2DArray,
    Detection2D,
    ObjectHypothesisWithPose,
    BoundingBox2D,
)
from cv_bridge import CvBridge
from ultralytics import YOLO
import torch


class YOLODetectionNode(Node):
    def __init__(self):
        super().__init__("yolo_detection_node")

        # Parameters
        self.model_path = self.declare_parameter("model_path", "yolo11n.engine").value
        self.confidence_threshold = self.declare_parameter(
            "confidence_threshold", 0.5
        ).value
        self.device = self.declare_parameter("device", "cuda:0").value

        # Initialize YOLO
        self.model = YOLO(self.model_path)

        # CV Bridge
        self.bridge = CvBridge()

        # Publishers and Subscribers
        self.image_sub = self.create_subscription(
            Image, "/camera/camera/color/image_raw", self.image_callback, 10
        )

        self.detection_pub = self.create_publisher(
            Detection2DArray, "/yolo/detections", 10
        )

        # Get class names from model
        self.class_names = self.model.names if hasattr(self.model, "names") else {}

        self.get_logger().info(
            f"YOLO Detection Node initialized with model: {self.model_path}"
        )

    def image_callback(self, msg):
        try:
            # Convert ROS image to OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

            # Run YOLO inference
            results = self.model(cv_image, conf=self.confidence_threshold)

            # Create detection message
            detection_array = Detection2DArray()
            detection_array.header = msg.header

            for r in results:
                boxes = r.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = Detection2D()

                        # Bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                        # Set center coordinates
                        detection.bbox.center.position.x = float((x1 + x2) / 2)
                        detection.bbox.center.position.y = float((y1 + y2) / 2)

                        detection.bbox.size_x = float(x2 - x1)
                        detection.bbox.size_y = float(y2 - y1)

                        # Class and confidence
                        hypothesis = ObjectHypothesisWithPose()
                        class_id = int(box.cls)

                        # Set the class_id as string
                        hypothesis.hypothesis.class_id = str(class_id)
                        hypothesis.hypothesis.score = float(box.conf)

                        detection.results.append(hypothesis)
                        detection_array.detections.append(detection)

            self.detection_pub.publish(detection_array)

        except Exception as e:
            self.get_logger().error(f"Error in image callback: {e}")
            import traceback

            self.get_logger().error(f"Traceback: {traceback.format_exc()}")


def main(args=None):
    rclpy.init(args=args)
    node = YOLODetectionNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
