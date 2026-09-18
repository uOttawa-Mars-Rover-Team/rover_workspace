import cv2
import rclpy
from ffmpeg_image_transport_msgs.msg import FFMPEGPacket
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import CompressedImage, Image

from .common import CameraNode
from .ffmpeg_decoder import FFMPEGDecoder


class ArucoDecoderNode(CameraNode):
    """
    Initializes a node to detect, annotate and display ArUco markers in images.
    """

    def __init__(self, node_name: str = "aruco_decoder_node"):
        super().__init__(node_name)

        # Define `image_topic` as a required launch parameter, which specifies
        # the name of the ROS Image topic to subscribe to
        self.image_subscription_topic = self.get_param(
            "image_topic", rclpy.Parameter.Type.STRING
        )
        self.image_is_compressed = self.get_param(
            "is_compressed", rclpy.Parameter.Type.BOOL, default_val=False
        )
        self.image_is_ffmpeg = self.get_param(
            "is_ffmpeg", rclpy.Parameter.Type.BOOL, default_val=False
        )
        # Subscribe to a single ROS Image topic to receive images to detect
        # ArUco markers from

        if self.image_is_ffmpeg:
            self.get_logger().info("Subscribing to FFMPEG messages")
            self.ffmpeg_decoder = FFMPEGDecoder(self)
            self.ffmpeg_decoder.start()
            self.image_subscription = self.create_subscription(
                FFMPEGPacket,
                self.image_subscription_topic,
                self.ffmpeg_decoder.consume,
                qos_profile_sensor_data,
            )
            self.ffmpeg_decoder.on_new_image_message(self.image_callback)
        else:
            self.get_logger().info(
                f"Subscribing to {'CompressedImage' if self.image_is_compressed else 'Image'} messages"
            )
            self.image_subscription = self.create_subscription(
                CompressedImage if self.image_is_compressed else Image,
                self.image_subscription_topic,
                self.image_callback,
                qos_profile_sensor_data,
            )
        self.get_logger().info(
            f"Subscribing to messages from: {self.image_subscription.topic_name}"
        )

    def image_callback(self, image: Image) -> None:
        """
        Display the Image message with cv2. Detect and annotate ArUco markers
        if present.
        """

        # Convert the ROS image to an OpenCV image. Use output encoding as
        # "bgr8", however openCV seems to convert it into a grayscale image
        # anyways
        if self.image_is_compressed:
            frame = self.bridge.compressed_imgmsg_to_cv2(image, desired_encoding="bgr8")
        else:
            frame = self.bridge.imgmsg_to_cv2(image, desired_encoding="bgr8")

        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

        # Try new API
        try:
            parameters = cv2.aruco.DetectorParameters()
            detector = cv2.aruco.ArucoDetector(dictionary, parameters)
            corners, ids, _ = detector.detectMarkers(frame)
        except AttributeError:
            # Fall back to old API
            parameters = cv2.aruco.DetectorParameters_create()
            corners, ids, _ = cv2.aruco.detectMarkers(
                frame, dictionary, parameters=parameters
            )

        # Check to see at least one ArUco marker was detected
        if len(corners) > 0:
            # Flatten the ArUco IDs list
            ids = ids.flatten()

            # Loop over the detected ArUCo corners
            for markerCorner, markerID in zip(corners, ids):
                # Extract the marker corners (which are always returned in
                # top-left, top-right, bottom-right, and bottom-left order)
                corners = markerCorner.reshape((4, 2))
                (topLeft, topRight, bottomRight, bottomLeft) = corners

                # Convert each of the (x, y)-coordinate pairs to integers
                topLeft = (int(topLeft[0]), int(topLeft[1]))
                topRight = (int(topRight[0]), int(topRight[1]))
                bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
                bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

                # Colours
                green = (0, 255, 0)
                red = (0, 0, 255)

                # Draw the bounding box of the ArUCo detection
                cv2.line(frame, topLeft, topRight, green, 2)
                cv2.line(frame, topRight, bottomRight, green, 2)
                cv2.line(frame, bottomRight, bottomLeft, green, 2)
                cv2.line(frame, bottomLeft, topLeft, green, 2)

                # Compute and draw the center (x, y)-coordinates of the ArUco
                # marker
                cX = int((topLeft[0] + bottomRight[0]) / 2.0)
                cY = int((topLeft[1] + bottomRight[1]) / 2.0)
                cv2.circle(frame, (cX, cY), 4, red, -1)

                # Draw the ArUco marker ID on the frame
                cv2.putText(
                    frame,
                    f"ID: {markerID}",
                    (topLeft[0], topLeft[1] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    green,
                    2,
                )

        # Show the image frame in a window
        cv2.imshow(self.get_fully_qualified_name(), frame)
        # Allow for following image frames to be shown in the window (for a
        # live video-like viewing experience)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    aruco_decoder_node = ArucoDecoderNode()
    rclpy.spin(aruco_decoder_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
