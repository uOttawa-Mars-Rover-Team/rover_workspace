# camera_nodes Package

## Purpose

- This package defines several nodes, each of which have their own purpose
  - `PanoramaNode` (`camera_nodes/panorama.py`): Allows panoramas to be stitched from pictures at a path.
  - `PictureNode` (`camera_nodes/picture.py`): Allows pictures to be read from a ROS image topic and saved to a path.
  - `VideoNode` (`camera_nodes/video.py`) Allows videos to be written from a ROS image topic.
  - `ArucoDecoderNode` (`camera_nodes/aruco.py`) A node that subscribes to images, then displays them, detecting and annotating ArUco markers in the image if present. Running this node creates a window (to display images) using OpenCV.

## Installing dependencies

- To install dependencies (for only this package), run the following command at the root of the workspace

```bash
rosdep install --from-paths src/camera_nodes --ignore-src -r -y
```

## Usage

### Publish Images From Camera

- Launch a node to publish images from the camera to a ROS topic (requires a usb camera to be connected)

```bash
ros2 launch camera_nodes cam.launch.py
```

### Running All Camera Nodes

- Launch all the camera nodes (picture, panorama, video)

```bash
ros2 launch camera_nodes nodes.launch.py
```

### Running the Aruco Node

The aruco node is currently set to launch separately from the other camera nodes since it creates a opencv image window.

- Launch the aruco detection node

```bash
ros2 launch camera_nodes aruco.launch.py
```

- Launch the aruco node and set the the `image_topic` parameter to `/image_raw`

```bash
ros2 launch camera_nodes aruco.launch.py -- image_topic:=/image_raw
```

### Interacting With the Nodes

- Instead of doing so via the CLI (i.e. with `ros2 service call ...`), interacting with these nodes can be done via the dashboard (in the "Camera Controls" section)

  - The dashboard can be run using the instructions from `src/dashboard/README.md`

- **Useful:** Launch the built-in `rqt_image_view` node to view the images being published on various topics

```bash
ros2 run rqt_image_view rqt_image_view
```

### Controlling cameras with `camera_control_app.py`

The app from `camera_control_app.py` can be used to start and stop publishers for specified cameras quickly given a JSON config file. Compared to using traditional launch files, this app provides a user interface to start and stop publishers quickly and doesn't require multiple terminals to be opened to launch publishers for multiple cameras.

Running this app requires a JSON config file . Example config file:

```
{
  "title": "Camera Controls - Robotic Arm Config.",
  "cameras": {
    "arm": "params1.yaml",
    "end_effector": "params2.yaml"
  }
}
```

To run the app, use the `camera_nodes` package's console script for the app and pass in the path to the JSON config file being used. Example:

```
ros2 run camera_nodes controls src/camera_nodes/config/arm_config.json
```

### Misc Resources

- [Camera Information Wiki Page](https://gitlab.com/uorover/rover_workspace/-/wikis/Camera-Information)
