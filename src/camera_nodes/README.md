# camera_nodes Package

## Purpose

- This package defines several nodes, each of which have their own purpose
  - `PanoramaNode` (`camera_nodes/panorama.py`): Allows panoramas to be stitched from pictures.
  - `PictureNode` (`camera_nodes/picture.py`): Allows pictures to be saved from a ROS image topic.
  - `VideoNode` (`camera_nodes/video.py`) Allows videos to be written from a ROS image topic.

## Usage

- Launch a node to publish images from the camera to a ROS topic: `ros2 run v4l2_camera v4l2_camera_node`
- Launched each of the nodes listed above
- Interfacing with these nodes can be done via the dashboard (in the "Camera Controls" section)
