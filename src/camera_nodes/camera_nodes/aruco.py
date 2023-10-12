import cv2
import rclpy
from sensor_msgs.msg import Image

from .common import CameraNode


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
        # Subscribe to a single ROS Image topic to receive images to detect
        # ArUco markers from
        self.image_subscription = self.create_subscription(
            Image, self.image_subscription_topic, self.image_callback, 10
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
        frame = self.bridge.imgmsg_to_cv2(image, desired_encoding="bgr8")

        arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        arucoParams = cv2.aruco.DetectorParameters_create()

        # Detect ArUco markers in the input frame, dismissing rejectedImgPoints
        # returned by cv2.aruco.detectMarkers
        corners, ids, _ = cv2.aruco.detectMarkers(
            frame, arucoDict, parameters=arucoParams
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
