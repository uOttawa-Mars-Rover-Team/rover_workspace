#!/usr/bin/python

# Launch:
# roslaunch camera_nodes picture.launch

import rospy
from sensor_msgs.msg import Image
from std_msgs.msg import String
import cv2
from cv_bridge import CvBridge, CvBridgeError
import time
import os
import json


class PictureNode:
    """
    Example Messages:

    {
        "imageTopic": "/camera/color/image_raw",
        "path": "/home/user/Desktop/"
    }
    """

    def __init__(self, picture_topic):
        self.picture_topic = picture_topic
        rospy.Subscriber(self.picture_topic, String, self.handle_message)

    def handle_message(self, message):
        message = message.data

        if not self.validate_message(message):
            rospy.loginfo(
                "PictureNode.handle_message(): {} is not a valid message".format(
                    message
                )
            )
            return

        message = json.loads(message)
        image_topic = message["imageTopic"]
        path = message["path"]
        # Receive a single Image message from image_topic
        # NOTE: If we change the image topic to a compressed topic, use CompressedImage message type instead
        timeout = 5
        try:
            image = rospy.wait_for_message(image_topic, Image, timeout=timeout)
        except rospy.ROSException:
            rospy.loginfo(
                "PictureNode.handle_message(): Didn't receive message from {} within timeout ({} seconds)".format(
                    image_topic, timeout
                )
            )
            return
        bridge = CvBridge()

        try:
            # Try creating an image from the Image message
            cv2_img = bridge.imgmsg_to_cv2(image, "bgr8")
        except CvBridgeError as e:
            rospy.loginfo(
                "PictureNode.save_image(): failed to convert Image message to a cv2 image. Error {}".format(
                    e
                )
            )
        else:
            # Create the file name and file path, then save the image
            picture_name = "{}.jpg".format(int(time.time()))
            full_path = os.path.join(path, picture_name)
            rospy.loginfo(
                "PictureNode.save_image(): Saving {} at path {}".format(
                    picture_name, full_path
                )
            )
            cv2.imwrite(full_path, cv2_img)

    @staticmethod
    def validate_message(message):
        try:
            message = json.loads(message)
        except ValueError:
            return False
        if not ("imageTopic" in message and "path" in message):
            return False
        if not os.path.exists(message["path"]):
            return False

        return True


def main():
    rospy.init_node("picture", anonymous=True)
    picture_topic = rospy.get_param("~picture_topic", default="/picture_topic")
    picture_node = PictureNode(picture_topic)
    rospy.spin()


if __name__ == "__main__":
    main()
