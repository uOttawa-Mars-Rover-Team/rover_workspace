# Camera Nodes

To have a camera's video be published on a ROS ropic, launch the camera node using

```
roslaunch camera_nodes cam.launch
```

_Note: This should just successfully work with the first camera available to use, but some parameters may have to be modified when launching if more than 1 camera is attached to Ubuntu, etc._

## Camera Control

### Overview

The following nodes exist to make use of the camera:

- Panorama node (`src/panorama.py`)
  - Launch: `roslaunch camera_nodes panorama.launch`.
  - Receives a JSON String ROS message containing a path with existing pictures to stitch a panorama from.
- Picture node (`src/picture.py`)
  - Launch: `roslaunch camera_nodes picture.launch`.
  - Receives a JSON String ROS message containing a camera\* topic and a path on the system. Receives one image from the camera topic and saves it to the specified path.
- Video node (`src/video.py`)
  - Launch: `roslaunch camera_nodes video.launch`.
  - Receives a JSON String ROS message containing a camera\* topic, a path on the system (only required if starting a video write) and whether to START or STOP writing a video. If specified to start, it subscribes to the camera\* topic and writes frames from the camera to the specified path as a video. When specified to stop writing from a camera\* topic, it finishes writing the video and cleans itself up (unsubscribes from topic, etc.).
  - Supports image topics using both Image and CompressedImage topic types.

\* Topic containing ROS Image messages from a camera

Topics used to interact with each of these nodes should be specified in their respective launch files. The expected JSON String message types are described with examples in the Python file associated with each node.

### How-To

Steps to use any of the camera control nodes

- Connect a USB camera to the VM. It should show up under /dev/ as something like `video0`, `video1`, etc.
- Publish the camera's video to ROS using the camera node. Run `roslaunch camera_nodes cam.launch`.
- Launch any of the camera control nodes. E.g.: `roslaunch camera_nodes picture.launch`.
- Publish a message to the specified node. This can be done using `rostopic pub` ([example from ROS wiki](https://wiki.ros.org/ROS/Tutorials/UnderstandingTopics#Using_rostopic_pub)). The expected JSON String message types are described with examples in the Python file associated with each node.
