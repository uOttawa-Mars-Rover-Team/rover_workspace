from typing import Any

from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image


class CameraNode(Node):
    """
    A base class for camera nodes.
    """

    VALID_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    IMG_MSG_NAME_MAP = {
        "sensor_msgs/msg/Image": Image,
        "sensor_msgs/msg/CompressedImage": CompressedImage,
    }

    def __init__(self, node_name: str, **kwargs):
        super().__init__(node_name, **kwargs)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

    def validate_image_topic(
        self, img_topic_name: str, valid_topic_types: dict[str, Any] | None = None
    ) -> tuple[bool, Any | None]:
        """
        Validate that a topic exists and is of a type as specified in
        param valid_topic_types.

        :param img_topic_name: The name of the topic to check.
        :param valid_topic_types: A dict containing a map of string message
            types (e.g. "sensor_msgs/msg/Image") and their corresponding
            message types as a Python class (e.g. Image) to use. The keys of
            this dict will be used to determine if a topic is publishing a
            valid type.
        :return: (False, None) if the topic doesn't exist or doesn't have a
            valid type. (True, topic_type) otherwise, where topic_type is a
            Python class representing the type of the message being published
            at the topic.
        """
        if valid_topic_types is None:
            valid_topic_types = self.IMG_MSG_NAME_MAP

        valid_topic = False
        message_type = None

        topics = self.get_topic_names_and_types()
        for topic_name, topic_types in topics:
            if topic_name == img_topic_name:
                # topic_types is a list. It's not clear how to handle a topic
                # with multiple published types. For now, the request will be
                # aborted if the first type in the list is not as expected
                topic_type = topic_types[0]
                if topic_type in valid_topic_types:
                    valid_topic = True
                    message_type = valid_topic_types[topic_type]
                break

        return valid_topic, message_type
