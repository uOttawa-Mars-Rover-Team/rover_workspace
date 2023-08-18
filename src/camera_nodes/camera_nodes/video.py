import os
import pathlib
import time

import cv2
import rclpy
from rclpy.node import SrvTypeRequest, SrvTypeResponse
from rclpy.subscription import Subscription
from sensor_msgs.msg import CompressedImage, Image

from general_interfaces.srv import SaveImage

from .common import CameraNode


class VideoNode(CameraNode):
    """
    Initializes a node running 2 SaveImage type services.

    The first service receives a request with an image topic and a path and
    attempts the continuously write images from the image topic to the video at
    the path.

    The second services receives a path to a video and stops the video from
    being written, if it exists. If the path is "*", then all videos being
    written to are stopped.
    """

    VALID_VIDEO_EXTENSIONS = {".mp4"}
    # NOTE: VideoNode.FOURCC and VideoNode.VIDEO_EXTENSION are interdependent
    # Mismatching them may cause videos to not be created
    #
    # From docs:
    # https://docs.opencv.org/3.4/dd/d43/tutorial_py_video_display.html
    FOURCC = cv2.VideoWriter_fourcc(*"mp4v")
    VIDEO_EXTENSION = ".mp4"

    def __init__(self, node_name: str = "video_node", output_fps: int = 30):
        super().__init__(node_name)
        self.output_fps = output_fps
        self.start_srv = self.create_service(
            SaveImage, "start_video", self.start_video_callback
        )
        self.stop_srv = self.create_service(
            SaveImage, "stop_video", self.stop_video_callback
        )
        # Keep track of cv2.VideoWriter objects and ROS subscribers being used
        # to write any videos
        self.active_writers: dict[str, cv2.VideoWriter] = {}
        self.active_subscribers: dict[str, Subscription] = {}
        self.get_logger().info(f"Started service: {self.start_srv.srv_name}")
        self.get_logger().info(f"Started service: {self.stop_srv.srv_name}")

    def start_video_callback(
        self, request: SrvTypeRequest, response: SrvTypeResponse
    ) -> SrvTypeResponse:
        """
        Handle a SaveImage request. Verify the request and start writing images
        from the specified topic to a video at the specified path.

        :param request: The service request.
        :param response: The service response.
        :return: The modified service response.
        """
        self.get_logger().info(f"Received request with data: {request}")
        response.status = False

        # Validate the path received
        #
        # Case where path to a directory has been received
        if request.path.endswith(os.path.sep) and self.validate_path_dir(
            request.path, request.create_path
        ):
            path_dir = request.path
            path_to_dir = True
        # Case where path to a filename has been received
        elif self.validate_path_file(
            request.path, request.create_path, self.VALID_VIDEO_EXTENSIONS
        ):
            path_dir, _, _ = self.extract_file_path_parts(request.path)
            path_to_dir = False
        else:
            response.message = 'The specified path is not valid or doesn\'t exist. Ensure paths to directories end with a "/".'
            return response
        # Create the path if it doesn't already exist
        if request.create_path:
            pathlib.Path(path_dir).mkdir(parents=True, exist_ok=True)

        # Create a filename for the video if necessary
        if path_to_dir:
            full_write_path = os.path.join(
                request.path, f"{int(time.time())}{self.VIDEO_EXTENSION}"
            )
        else:
            full_write_path = request.path

        # Ensure that the topic specified exists and publishes messages of a
        # valid type
        valid_topic, message_type = self.validate_image_topic(request.image_topic)
        if not valid_topic:
            response.message = f"The requested topic {request.image_topic} was not found or does not have a valid message type."
            return response

        # Ensure that a video is not already being written at the specified
        # path
        if full_write_path in self.active_writers:
            response.message = (
                "Already writing at the specified path. Stop the video to overwrite."
            )
            return response

        # Await a single message from the specified topic
        status, image_message = self.wait_for_message(message_type, request.image_topic)
        if not status:
            response.message = (
                "Could not receive a single message from the topic. Try again."
            )
            return response

        # Convert the ROS image to a cv2 image
        cv2_image = self.convert_image(image_message)
        if cv2_image is None:
            response.message = (
                "Could not successfully convert the image from the topic. Try again."
            )
            return response
        # Get the size of the cv2 image to specify when creating a new video
        # file
        frame_height, frame_width, _ = cv2_image.shape

        # Create a cv2.VideoWriter object to write images to the video at the
        # specified path
        video_writer = cv2.VideoWriter(
            full_write_path,
            self.FOURCC,
            fps=self.output_fps,
            frameSize=(frame_width, frame_height),
        )
        # Create a subscription to the specified image topic and allow the
        # callback to write images to a video file
        save_frame_callback = lambda image: self.save_frame(image, full_write_path)
        video_topic_subscription = self.create_subscription(
            message_type, request.image_topic, save_frame_callback, 1
        )

        # Keep track of the video writer and subscriber for cleanup
        self.active_writers[full_write_path] = video_writer
        self.active_subscribers[full_write_path] = video_topic_subscription

        # Log info and end the service
        self.get_logger().info(f"Writing a video at {full_write_path}.")

        response.status = True
        response.message = full_write_path

        return response

    def stop_video_callback(
        self, request: SrvTypeRequest, response: SrvTypeResponse
    ) -> SrvTypeResponse:
        """
        Handle a SaveImage request. Verify the request and stop writing writing
        images to the video at the specified path. If path is "*", then all
        videos currently being written are stopped.

        :param request: The service request.
        :param response: The service response.
        :return: The modified service response.
        """
        response.status = True

        # Check to see if all videos should be stopped
        if request.path == "*":
            # Iterate over a list of the dict's keys to prevent modifying the
            # dict while iterating (which would lead to a RuntimeError) and
            # cleanup resources used for each video being written to
            for path in list(self.active_subscribers):
                self.cleanup_from_path(path)
            # Cleanup self.active_writers just in case it isn't empty already
            for path in self.active_writers:
                self.cleanup_from_path(path)

            response.message = f"Success. Stopped writing to all paths."
        else:
            # Check both self.active_writers and self.active_subscribers (just
            # in case) to ensure the path is actually being written to
            if (
                request.path not in self.active_writers
                or request.path not in self.active_subscribers
            ):
                response.status = False
                response.message = (
                    "The specified path is currently not being written to."
                )
                return response

            self.cleanup_from_path(request.path)

            response.message = f"Success. Stopped writing to {request.path}."

        return response

    def cleanup_from_path(self, path: str) -> None:
        """
        Stop writing a video to a path (if it's currently being written to),
        and cleanup resources that were used to write it.

        :param path: The path to the video which should be stopped and whose
            resources should be cleaned up.
        """
        if path in self.active_subscribers:
            # Destroy the subscription to cleanup
            status = self.destroy_subscription(self.active_subscribers[path])
            # Try alternative methods if self.destroy_subscription doesn't work
            if not status:
                self.active_subscribers[path].destroy()
            self.active_subscribers.pop(path)

        if path in self.active_writers:
            # Release the cv2.VideoWriter to cleanup
            self.active_writers[path].release()
            self.active_writers.pop(path)

    def save_frame(self, image: Image | CompressedImage, path: str) -> bool:
        """
        Save a ROS image to a video being written to.

        :param image: The ROS image to add to the video.
        :param path: The path to the video being written to, which the image
            should be added to.
        :return: Whether the image was successfully added to the video at path.
        """
        cv2_img = self.convert_image(image)
        if cv2_img is not None and path in self.active_writers:
            self.active_writers[path].write(cv2_img)
            return True
        return False


def main(args=None):
    rclpy.init(args=args)
    vide_node = VideoNode()
    rclpy.spin(vide_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
