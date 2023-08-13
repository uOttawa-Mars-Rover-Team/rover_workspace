import os
import time

import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.impl.implementation_singleton import rclpy_implementation as _rclpy
from rclpy.node import Node, SrvTypeRequest, SrvTypeResponse
from rclpy.signals import SignalHandlerGuardCondition
from rclpy.utilities import timeout_sec_to_nsec
from sensor_msgs.msg import CompressedImage, Image

from general_interfaces.srv import SaveImage


class PictureNode(Node):
    """
    Initializes node running a SaveImage type service. This service receives a
    request with an image topic and a path and attempts the save a single image
    from the image topic at the specified path.
    """

    def __init__(self, node_name: str = "picture_node"):
        super().__init__(node_name)
        self.srv = self.create_service(
            SaveImage, "save_picture", self.save_picture_callback
        )
        self.bridge = CvBridge()

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

        # Ensure that the path specified is valid
        if not os.path.exists(request.path):
            response.message = "The specified path doesn't exist."
            return response

        # Ensure that the topic specified is valid and publishes a message of
        # the right type
        topic_exists = False
        topics = self.get_topic_names_and_types()
        for topic_name, topic_types in topics:
            if topic_name == request.image_topic:
                topic_exists = True
                # topic_types is a list. It's not clear how to handle a topic
                # with multiple published types. For now, the request will be
                # aborted
                topic_type = topic_types[0]
                if topic_type == "sensor_msgs/msg/Image":
                    message_type = Image
                elif topic_type == "sensor_msgs/msg/CompressedImage":
                    message_type = CompressedImage
                else:
                    response.message = f"The requested topic {request.image_topic} does not have a valid message type."
                    return response
                break

        if not topic_exists:
            response.message = (
                f"The requested topic {request.image_topic} was not found."
            )
            return response

        # Await a single message from the specified topic
        status, image_message = self.wait_for_message(message_type, request.image_topic)

        if not status:
            response.message = "Could not receive a single message from the topic."
            return response

        # Save the image at the specified path with a default name
        picture_name = f"{int(time.time())}.jpg"
        full_path = os.path.join(request.path, picture_name)
        status = self.save_image(image_message, full_path)
        if not status or not os.path.isfile(full_path):
            response.message = (
                "Failed to convert image from the topic and save to the specified path."
            )
            return response

        response.status = True
        response.message = "Success."

        return response

    def save_image(self, image: Image | CompressedImage, path: str) -> bool:
        """
        Save an image at the specified path

        :param image: The image to save.
        :param path: The path to save the image at, including the name of the
            image.
        :return: Whether the image was saved successfully.
        """
        try:
            if type(image) is Image:
                cv2_image = self.bridge.imgmsg_to_cv2(image)
            elif type(image) is CompressedImage:
                cv2_image = self.bridge.compressed_imgmsg_to_cv2(image)
            else:
                return False
        except CvBridgeError:
            return False

        status = cv2.imwrite(path, cv2_image)

        # Return whether cv2.imwrite() saved the image
        return status

    # Source code take and modified from:
    # https://github.com/ros2/rclpy/blob/540b809b1b4d6fc064cfd392834123f713593be4/rclpy/rclpy/wait_for_message.py
    # This feature was not yet implemented on ros2 humble when taken
    def wait_for_message(self, msg_type, topic: str, time_to_wait: int = -1):
        """
        Wait for the next incoming message.

        :param msg_type: message type
        :param topic: topic name to wait for message
        :time_to_wait: seconds to wait before returning
        :return: (True, msg) if a message was successfully received, (False,
            ()) if message could not be obtained or shutdown was triggered
            asynchronously on the context.
        """
        context = self.context
        wait_set = _rclpy.WaitSet(1, 1, 0, 0, 0, 0, context.handle)
        wait_set.clear_entities()

        sub = self.create_subscription(msg_type, topic, lambda _: None, 1)
        wait_set.add_subscription(sub.handle)
        sigint_gc = SignalHandlerGuardCondition(context=context)
        wait_set.add_guard_condition(sigint_gc.handle)

        timeout_nsec = timeout_sec_to_nsec(time_to_wait)
        wait_set.wait(timeout_nsec)

        subs_ready = wait_set.get_ready_entities("subscription")
        guards_ready = wait_set.get_ready_entities("guard_condition")

        if guards_ready:
            if sigint_gc.handle.pointer in guards_ready:
                return (False, None)

        if subs_ready:
            if sub.handle.pointer in subs_ready:
                msg_info = sub.handle.take_message(sub.msg_type, sub.raw)
                return (True, msg_info[0])

        return (False, None)


def main(args=None):
    rclpy.init(args=args)
    picture_node = PictureNode()
    rclpy.spin(picture_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
