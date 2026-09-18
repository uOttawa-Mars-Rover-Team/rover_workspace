import os
import time

import cv2
import rclpy
from rclpy.node import SrvTypeRequest, SrvTypeResponse

from general_interfaces.srv import CreatePanorama

from .common import CameraNode


class PanoramaNode(CameraNode):
    """
    Initializes a node running a CreatePanorama type service. This service
    receives a request with a path to a directory and attempts to read all
    non-panorama images from the directory and use them to create a panorama
    and save it at the directory.

    Saved panoramas are identified with a common filename suffix and extension.
    """

    # The number of images required to stitch a panorama. This can be adjusted,
    # but using too few may cause an error in panorama generation.
    MIN_REQ_IMAGES = 3
    # The filename suffix to identify created panoramas with
    PANORAMA_SUFFIX = "_panorama"
    # The filename extension to identify created panoramas with
    PANORAMA_EXTENSION = ".jpg"

    def __init__(self, node_name: str = "panorama_node"):
        super().__init__(node_name)
        self.srv = self.create_service(
            CreatePanorama, "create_panorama", self.create_panorama_callback
        )
        self.get_logger().info(f"Started service: {self.srv.srv_name}")
        self.stitcher = cv2.Stitcher.create()

    def create_panorama_callback(
        self, request: SrvTypeRequest, response: SrvTypeResponse
    ) -> SrvTypeResponse:
        """
        Handle a `CreatePanorama` request. Verify the request and create a
        panorama from the images at the specified path.

        :param request: The service request.
        :param response: The service response.
        :return: The modified service response.
        """

        self.get_logger().info(f"Received request with data: {request}")
        response.status = False

        # Ensure that the path specified is an existing directory
        if not os.path.isdir(request.path):
            response.message = "The specified path isn't an existing directory."
            return response

        # Get all images at the directory
        image_paths = self.get_image_paths(request.path)
        # Filter out images that are already panoramas
        valid_image_paths = [
            path
            for path in image_paths
            if not path.endswith(f"{self.PANORAMA_SUFFIX}{self.PANORAMA_EXTENSION}")
        ]
        # Check to see that there are enough non-panorama images in the
        # directory to make a panorama from
        if len(valid_image_paths) < self.MIN_REQ_IMAGES:
            response.message = f"Not enough images at the specified path. {self.MIN_REQ_IMAGES} are required. {len(valid_image_paths)} were found."
            return response

        # Read the images at the paths as cv2 images and stitch the panorama
        images = [cv2.imread(path) for path in valid_image_paths]
        status, panorama = self.stitcher.stitch(images)

        # Make sure that the stitcher succeeded in creating the panorama from
        # the images
        if status != 0:
            self.get_logger().info(
                f"Failed to stitch images for request at path {request.path}. Stitch attempt returned with status: {status}."
            )
            response.message = "The stitcher failed to successfully stitch the images."
            return response

        # Create the full path name for the panorama and write the panorama
        # image to the path
        pano_filename = (
            f"{int(time.time())}{self.PANORAMA_SUFFIX}{self.PANORAMA_EXTENSION}"
        )
        pano_full_path = os.path.join(request.path, pano_filename)
        cv2.imwrite(pano_full_path, panorama)

        response.status = True
        response.message = f"Success. Saved panorama at {pano_full_path}."

        return response

    def get_image_paths(self, path: str) -> list[str]:
        """
        Returns a list of strings containing the paths to all images at
        specified directory.

        :param path: The path to the directory to list images from.
        :return: A list of strings containing the full path to each image file
            in the directory.
        """
        return [
            os.path.join(path, listing)
            for listing in os.listdir(path)
            if os.path.isfile(os.path.join(path, listing))
            and f".{listing.split('.')[-1]}" in self.VALID_IMG_EXTENSIONS
        ]


def main(args=None):
    rclpy.init(args=args)
    panorama_node = PanoramaNode()
    rclpy.spin(panorama_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
