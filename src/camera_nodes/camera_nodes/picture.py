import os
import pathlib
import time

import cv2
import rclpy
from rclpy.node import SrvTypeRequest, SrvTypeResponse
from sensor_msgs.msg import CompressedImage, Image

from general_interfaces.srv import SaveImage

from .common import CameraNode


class PictureNode(CameraNode):
    """
    Initializes a node running a SaveImage type service. This service receives
    a request with an image topic and a path and attempts the save a single
    image from the image topic at the specified path.

    The path may be a directory or a path containing a directory and filename.

    If the service request has `create_path` set to true, then the specified
    directory to the path is created.

    If the path ends with a `/` it's interpreted as a directory and a file with
    a random name is saved at the specified directory (if it exists, or if
    create_path is True).

    Otherwise, the path is interpreted as a path with a filename and must
    contain a valid extension for images.
    """

    def __init__(self, node_name: str = "picture_node"):
        super().__init__(node_name)
        self.srv = self.create_service(
            SaveImage, "save_picture", self.save_picture_callback
        )
        self.get_logger().info(f"Started service: {self.srv.srv_name}")

    def save_picture_callback(
        self, request: SrvTypeRequest, response: SrvTypeResponse
    ) -> SrvTypeResponse:
        """
        Handle a SaveImage request. Verify the request and save the image from
        the topic at the specified path.

        :param request: The service request.
        :param response: The service response.
        :return: The modified service response.
        """
        self.get_logger().info(f"Received request with data: {request}")
        response.status = False

        # Validate the path received
        # Case where path to a directory has been received
        if request.path.endswith(os.path.sep) and self.validate_path_dir(
            request.path, request.create_path
        ):
            path_dir = request.path
            path_to_dir = True
        # Case where path to a filename has been received
        elif self.validate_path_file(
            request.path, request.create_path, self.VALID_IMG_EXTENSIONS
        ):
            path_dir, _, _ = self.extract_file_path_parts(request.path)
            path_to_dir = False
        else:
            response.message = 'The specified path is not valid or doesn\'t exist. Ensure paths to directories end with a "/".'
            return response

        # Create the path if it doesn't already exist
        if request.create_path:
            pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True)

        # Create a filename for the picture if necessary
        if path_to_dir:
            full_write_path = os.path.join(request.path, f"{int(time.time())}.jpg")
        else:
            full_write_path = request.path

        # Ensure that the topic specified exists and publishes messages of a
        # valid type
        valid_topic, message_type = self.validate_image_topic(request.image_topic)
        if not valid_topic:
            response.message = f"The requested topic {request.image_topic} was not found or does not have a valid message type."
            return response

        # Await a single message from the specified topic
        # Use a try/except, as the wait_for_message method has been observed to
        # possibly not work as expected at times
        try:
            status, image_message = self.wait_for_message(
                message_type, request.image_topic
            )
        except Exception as e:
            status = False
            self.get_logger().warn(
                f"Caught an exception when awaiting single message from topic: {request.image_topic}. Error message: {e}."
            )
        if not status:
            response.message = (
                "Could not receive a single message from the topic. Try again."
            )
            return response

        status = self.save_image(image_message, full_write_path)
        # Check status and make sure the file exists at the specified path
        if not status or not os.path.isfile(full_write_path):
            response.message = (
                "Failed to convert image from the topic and save to the specified path."
            )
            return response

        response.status = True
        response.message = f"Success. Saved at {full_write_path}."

        return response

    def save_image(self, image: Image | CompressedImage, path: str) -> bool:
        """
        Save an image at the specified path

        :param image: The ROS image to save.
        :param path: The path to save the image at, including the name of the
            image.
        :return: Whether the image was saved successfully.
        """
        cv2_image = self.convert_image(image)
        if cv2_image is None:
            return False

        status = cv2.imwrite(path, cv2_image)

        # Return whether cv2.imwrite() saved the image
        return status


def main(args=None):
    rclpy.init(args=args)
    picture_node = PictureNode()
    rclpy.spin(picture_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
