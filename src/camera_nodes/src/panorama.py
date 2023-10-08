#!/usr/bin/python

# Launch:
# roslaunch camera_nodes panorama.launch

import rospy
from std_msgs.msg import String
import cv2
import time
import os
import json


class PanoramaNode:
    """
    PanoramaNode subscribes to a std_msgs/String topic. Once it receives a
    JSON String message with a valid path (a path/directory that exists), it
    attempts to create a panorama from the images at the specified path
    and save the panorama at the path.

    Message Example:
    {"path": "/home/user/pano"}
    """

    VALID_IMAGE_ENDINGS = (".png", ".jpg", ".jpeg")
    PANORAMA_SUFFIX = "_panorama"

    def __init__(self, path_topic):
        """
        :param str path_topic: A std_msgs/String topic with messages containing paths
        to images ready to be stitched into a panorama
        """
        self.path_topic = path_topic
        rospy.Subscriber(self.path_topic, String, self.panorama)

    def panorama(self, path):
        """
        Attempts to create a panorama using the images at a specified path.

        :param str path: The path to gather images from and write the panorama to
        """
        path = json.loads(path.data)["path"]

        if not self.validate_path(path):
            rospy.loginfo(
                "PanoramaNode.panorama(): {} is not a valid directory. The path passed in must be a valid directory and must contain at least 2 images.".format(
                    path
                )
            )
            return

        # Get the non-panorama image names at path, and read them as cv2 images
        images = [
            image_name
            for image_name in PanoramaNode.get_images(path)
            if not ".".join(image_name.split(".")[:-1]).endswith(
                PanoramaNode.PANORAMA_SUFFIX
            )
        ]
        images = [cv2.imread(os.path.join(path, image)) for image in images]

        # Create a cv2 stitcher and attempt to stich images into a panorama
        # Docs for status codes: https://docs.opencv.org/3.4/d2/d8d/classcv_1_1Stitcher.html
        stitcher = cv2.createStitcher(try_use_gpu=False)
        status, result = stitcher.stitch(images)

        if status == 0:
            # Create the image name and path, and write the image to the path
            output_name = "{}{}.jpg".format(
                int(time.time()), PanoramaNode.PANORAMA_SUFFIX
            )
            output_path = os.path.join(path, output_name)
            cv2.imwrite(output_path, result)
            rospy.loginfo(
                "PanoramaNode.panorama(): Successfully wrote panorama ({}) to {}".format(
                    output_name, output_path
                )
            )
        else:
            rospy.loginfo(
                "PanoramaNode.panorama(): Panorama creation was UNSUCCESSFUL with error code {} for cv2.createStitcher()".format(
                    status
                )
            )

    def validate_path(self, path):
        """
        Validates a path to make sure it exists and contains at least 2 images
        to be stitched into a panorama.

        :param str path: The path to be validated
        :return: whether the path exists
        :rtype: bool
        """
        if not os.path.exists(path):
            return False
        # If there are less than 2 images, a panorama shouldn't be created
        if len(PanoramaNode.get_images(path)) < 2:
            return False

        return True

    @staticmethod
    def get_images(path):
        """
        Returns the names of all the images (containing extensions part of
        PanoramaNode.VALID_IMAGE_ENDINGS) at a specified path.

        :param str path: The path to be checked for images
        :return: A list containing image names at the path
        :rtype: list
        """
        return [
            file
            for file in os.listdir(path)
            if file.lower().endswith(PanoramaNode.VALID_IMAGE_ENDINGS)
        ]


def main():
    rospy.init_node("panorama", anonymous=True)
    path_topic = rospy.get_param("~path_topic", default="/panorama_path")
    panorama_node = PanoramaNode(path_topic)
    rospy.spin()


if __name__ == "__main__":
    main()
