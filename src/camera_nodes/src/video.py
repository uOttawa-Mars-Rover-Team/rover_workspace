#!/usr/bin/python

# Launch:
# roslaunch camera_nodes video.launch

import rospy
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
import cv2
from cv_bridge import CvBridge, CvBridgeError
import json
import time
import os


class VideoNode:
    """
    PictureNode subscribes to a std_msgs/String topic. It receives JSON ROS String
    messages specifying whether to start or stop writing a video to a path, and the
    ROS topic to receive images from to write the video with.

    A single video source (ROS Image topic) can not be used to write more than one
    video at a time.

    If the current Image topic is being used to write a video and VideoNode receives 
    a message asking to write a video to a different path using the occupied 
    Image topic, then the VideoNode will stop writing the active video and start 
    writing at the new path specified.

    Examples:
        String message to start writing to a path:
            {
               "action": "START",
               "path": "path/to/directory/",
               "imageTopic": "/camera/color/image_raw"
            }
        String message to stop writing to a path:
            {
               "action": "STOP",
               "imageTopic": "/camera/color/image_raw"
            }
    """

    # NOTE: VideoNode.FOURCC and VideoNode.VIDEO_EXTENSION are interdependent
    # Mismatching them may cause videos to not be created
    # From docs: https://docs.opencv.org/3.4/dd/d43/tutorial_py_video_display.html
    FOURCC = cv2.VideoWriter_fourcc(*"mp4v")
    VIDEO_EXTENSION = "mp4"
    # Define dict keys to use for the ROS subscriber, cv2 video writer and file 
    # name/path for each video currently being written
    SUB_KEY_NAME = "subscriber"
    WRITER_KEY_NAME = "writer"
    FILE_KEY_NAME = "file_name"

    def __init__(self, action_topic, output_fps):
        """
        :param str action_topic: A std_msgs/String topic with messages describing
        whether to start or stop writing a video, the video topic to use, and which path
        to write the video to
        :param float output_fps: The FPS to write videos at
        """
        self.action_topic = action_topic
        # The FPS for videos to be written at
        self.output_fps = output_fps
        rospy.Subscriber(self.action_topic, String, self.handle_action)
        self.bridge = CvBridge()
        # Store data related to the videos currently being written to
        # This dict will contain inner dict objects with key-value pairs for the
        # ROS subscriber, cv2 video writer and file name/path for the associated
        # video being written to from an Image topic
        self.writers = {}

    def handle_action(self, action_data_msg):
        """
        Handles new messages to self.action_topic. If the message is valid, it starts
        or stops writing some video to some path, if necessary.

        :param str action_data_msg: The action data message (std_msgs/String) from \
        self.action_topic
        """
        action_data = action_data_msg.data

        if not VideoNode.validate_action(action_data):
            rospy.loginfo(
                "VideoNode.handle_action(): {} is not a valid action JSON".format(
                    action_data
                )
            )
            return

        # action_data is now a valid JSON object, so it can be loaded as a dict
        action_data = json.loads(action_data)
        action = action_data["action"]
        image_topic = action_data["imageTopic"]

        if action == "START":
            # Normalize the path to ensure consistency with trailing slashes, etc.
            path = os.path.normpath(action_data["path"])
            if image_topic in self.writers:
                # Check to see if the writer is already writing to the path specified
                if (
                    os.path.dirname(self.writers[image_topic][VideoNode.FILE_KEY_NAME])
                    == path
                ):
                    # If so, don't change what's being done
                    rospy.loginfo(
                        "VideoNode.handle_action(): Already writing at {} from topic {} (currently writing to  file {}).".format(
                            path,
                            image_topic,
                            self.writers[image_topic][VideoNode.FILE_KEY_NAME],
                        )
                    )
                    return
                else:
                    # If the another path should be written to from the same Image topic, then
                    # stop writing the current video and create a new one at the specified path
                    # by calling self.handle_action again
                    rospy.loginfo(
                        "VideoNode.handle_action(): Now stopping writing to path {} from topic {}. Going to write to path {}".format(
                            self.writers[image_topic][VideoNode.FILE_KEY_NAME],
                            image_topic,
                            path,
                        )
                    )
                    self.end_writing(image_topic)
                    self.handle_action(action_data_msg)
                    return
            # Find the message type of the Image topic
            published_topics = dict(rospy.get_published_topics())
            if published_topics[image_topic] == "sensor_msgs/Image":
                image_type = Image
            elif published_topics[image_topic] == "sensor_msgs/CompressedImage":
                image_type = CompressedImage
            # Receive a single Image message from image_topic and parse it
            timeout = 5
            try:
                image = rospy.wait_for_message(image_topic, image_type, timeout=timeout)
            except rospy.ROSException:
                rospy.loginfo(
                    "VideoNode.handle_action(): Didn't receive message from {} within timeout ({} seconds)".format(
                        image_topic, timeout
                    )
                )
                return
            cv2_img = self.parse_image(image, image_type)

            if cv2_img is None:
                rospy.loginfo(
                    "VideoNode.handle_action(): was not able to convert image to cv2 image from topic {}. Aborting...".format(
                        image_topic
                    )
                )
                return

            height, width, channels = cv2_img.shape
            # Create the video's name and full path
            video_name = "{}.{}".format(int(time.time()), VideoNode.VIDEO_EXTENSION)
            full_path = os.path.join(path, video_name)

            self.writers[image_topic] = {}
            # Create a cv2.VideoWriter object to write images to the video at the specified path
            self.writers[image_topic][VideoNode.WRITER_KEY_NAME] = cv2.VideoWriter(
                full_path,
                VideoNode.FOURCC,
                fps=self.output_fps,
                frameSize=(width, height),
            )
            # Create a rospy.Subscriber to receive Image messages and call the callback
            # function (self.save_frame), passing in path as the second argument to it
            save_frame_callback = lambda image: self.save_frame(
                image, image_type, image_topic
            )
            self.writers[image_topic][VideoNode.SUB_KEY_NAME] = rospy.Subscriber(
                image_topic, image_type, save_frame_callback
            )
            # Save the full path being written to to log a message once done
            self.writers[image_topic][VideoNode.FILE_KEY_NAME] = full_path
            rospy.loginfo(
                "VideoNode.handle_action(): Writing {} at path {}".format(
                    video_name, full_path
                )
            )
        elif action == "STOP":
            self.end_writing(image_topic)

    def end_writing(self, image_topic):
        """
        Ends writing a video from a specified image topic, if valid.

        :param str image_topic: the name of the image topic
        to stop writing from
        """

        if image_topic in self.writers:
            self.writers[image_topic][VideoNode.SUB_KEY_NAME].unregister()
            self.writers[image_topic][VideoNode.WRITER_KEY_NAME].release()
            self.writers[image_topic][VideoNode.SUB_KEY_NAME]
            rospy.loginfo(
                "VideoNode.handle_action(): FINISHED writing to {}".format(
                    self.writers[image_topic][VideoNode.FILE_KEY_NAME]
                )
            )
            self.writers.pop(image_topic)

    def save_frame(self, image, image_type, image_topic):
        """
        Attempts to write an image as a video frame to the video
        at the specified path

        :param Image or CompressedImage image: The image to be written (as
        a video frame) to the video
        :param Image or CompressedImage image_type: The type of the image
        message. Should either be Image or CompressedImage
        :param str image_topic: The ROS Image topic from which the frame
        is being received from
        """
        cv2_img = self.parse_image(image, image_type)
        if cv2_img is None:
            rospy.loginfo(
                "VideoNode.save_frame(): was not able to convert image to cv2 image. Aborting..."
            )
            return
        # Use the cv2.VideoWriter for the specified path to write the frame
        # self.active_writers[path].write(cv2_img)
        self.writers[image_topic][VideoNode.WRITER_KEY_NAME].write(cv2_img)

    def parse_image(self, image, image_type):
        """
        Attemps to convert a Image message to a cv2 image.

        :param Image or CompressedImage image: The image to parse as a cv2 image
        :param Image or CompressedImage image_type: The type of the image
        message. Should either be Image or CompressedImage
        :return: A cv2 image, or None (if parsing didn't work)
        :rtype: numpy.ndarray or None
        """
        try:
            # Try creating an image from the Image message
            if image_type == Image:
                cv2_img = self.bridge.imgmsg_to_cv2(image, "bgr8")
            else:
                cv2_img = self.bridge.compressed_imgmsg_to_cv2(image, "bgr8")
            return cv2_img
        except CvBridgeError as e:
            rospy.loginfo(
                "VideoNode.parse_image(): failed to convert Image message to a cv2 image. Error {}".format(
                    e
                )
            )
            return None

    @staticmethod
    def validate_action(action):
        """
        Validates an action (str). The action must be a valid JSON
        string and must contain keys "action", "path" and "imageTopic".

        :param str action: The action to be validated.
        :return: Whether action is a valid message
        :rtype: bool
        """
        try:
            action = json.loads(action)
        except ValueError:
            return False
        if type(action) != dict:
            return False
        # Make sure the action contains the (2) necessary keys
        if not ("action" in action and "imageTopic" in action):
            return False
        if not action["action"] in {"START", "STOP"}:
            return False
        if action["action"] == "START":
            if not "path" in action:
                return False
            if not os.path.exists(action["path"]):
                return False
        image_topic = action["imageTopic"]
        if not image_topic in dict(
            rospy.get_published_topics()
        ) and image_topic not in {"sensor_msgs/Image", "sensor_msgs/CompressedImage"}:
            return False

        return True


def main():
    rospy.init_node("video", anonymous=True)
    action_topic = rospy.get_param("~action_topic", default="/video_action")
    output_fps = rospy.get_param("~output_fps", default=30.0)
    video_node = VideoNode(action_topic, output_fps)
    rospy.spin()


if __name__ == "__main__":
    main()
