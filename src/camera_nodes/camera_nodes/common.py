import os
import pathlib
import re
from collections.abc import Iterable
from typing import Any

from rclpy.node import Node
from sensor_msgs.msg import CompressedImage, Image


class CameraNode(Node):
    """
    A base class for camera nodes.
    """

    # Image extensions which will be deemed allowable to work with
    VALID_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png"}
    # A map from ROS message "paths" to ROS image message Python classes
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
        Validate that a topic exists and is of a type as specified in param
        valid_topic_types.

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
        # Set the default value for params
        if valid_topic_types is None:
            valid_topic_types = self.IMG_MSG_NAME_MAP

        valid_topic = False
        message_type = None

        topics = self.get_topic_names_and_types()
        for topic_name, topic_types in topics:
            if topic_name == img_topic_name:
                # topic_types is a list. It's not clear what this means and how
                # to handle a topic with multiple published types. For now, the
                # request will be aborted if the first type in the list is not
                # as expected
                topic_type = topic_types[0]
                if topic_type in valid_topic_types:
                    valid_topic = True
                    message_type = valid_topic_types[topic_type]
                break

        return valid_topic, message_type

    def validate_path_dir(self, path: str, can_create_path: bool) -> bool:
        """
        Checks whether a string path is deemed a "valid" path to a directory.

        :param path: The path to validate.
        :param can_create_path: Whether the caller is willing to create the
            path, if necessary (and if doable).
        :return: Whether the path is deemed a "valid" path to a directory.
        """
        # Directory paths must end with the path separator ("/" on Linux) to be
        # distinguishable from paths to files
        if path.endswith(os.path.sep):
            # Check if the directory already exists
            if os.path.isdir(path):
                return True
            else:
                if can_create_path:
                    # Try to see if the directory path can be created without
                    # errors
                    path_accessor = pathlib.Path(path)
                    try:
                        path_accessor.mkdir(parents=True, exist_ok=True)
                    except (FileNotFoundError, OSError):
                        return False
                    path_accessor.rmdir()
                    return True
                else:
                    # Since the path doesn't exist and the caller isn't willing
                    # to create it, it's invalid
                    return False
        else:
            return False

    def validate_path_file(
        self, path: str, can_create_path: bool, valid_file_extensions: Iterable[str]
    ) -> bool:
        """
        Checks whether a string path is deemed a "valid" path to a file.

        :param path: The path to validate.
        :param can_create_path: Whether the caller is willing to create the
            path (directory part), if necessary (and if doable).
        :param valid_file_extensions: An iterable containing file extensions
            that the file in the path may have to be considered valid.
        :return: Whether is deemed a "valid" path to a directory.
        """
        if path.endswith(os.path.sep):
            return False
        else:
            path_dir, filename, file_extension = self.extract_file_path_parts(path)
            if path_dir is None:
                # If the extract_file_path_parts method can't extract the parts
                # of the path, it's considered invalid
                return False
            else:
                # Ensure that the extension is valid
                if not file_extension in valid_file_extensions or filename in {
                    "",
                    os.path.sep,
                }:
                    return False
                return self.validate_path_dir(path_dir, can_create_path)

    def extract_file_path_parts(
        self, path: str
    ) -> tuple[str | None, str | None, str | None]:
        """
        Checks whether a string path is deemed a "valid" path to a file.

        :param path: The path to validate.
        :param can_create_path: Whether the caller is willing to create the
            path (directory part), if necessary (and if doable).
        :param valid_file_extensions: An iterable containing file extensions
            that the file in the path may have to be considered valid.
        :return: Whether is deemed a "valid" path to a directory.
        """
        # Use a regex search to determine if the path is valid. This regex
        # search is more stringent than normal file/path creation rules in
        # Linux
        #
        # Valid paths must contain at least one path separator ("/" on Linux)
        # Filenames must contain a character before the extension
        matches = re.search(rf"(.*{os.path.sep})([^{os.path.sep}]+)(\..+)", path)
        if matches is None:
            return None, None, None
        path_dir = matches.group(1)
        filename = matches.group(2)
        file_extension = matches.group(3)
        return path_dir, filename, file_extension
