"""Launch a obstacle segmentation in a component container."""

import launch
from launch_ros.descriptions import ComposableNode
from launch_ros.actions import ComposableNodeContainer


def generate_launch_description():
    """Generate launch description with multiple components."""
    container = ComposableNodeContainer(
        name="obstacle_detection",
        namespace="",
        package="rclcpp_components",
        executable="component_container",
        composable_node_descriptions=[
            ComposableNode(
                package="rtabmap_util",
                plugin="rtabmap_util::PointCloudXYZ",
                name="points_xyz_rt",
                remappings=[
                    ("depth/image", "/camera/depth/image_rect_raw"),
                    ("depth/camera_info", "/camera/depth/camera_info"),
                    ("cloud", "/camera/depth/color/points"),
                ],
                parameters=[
                    {"decimation": 4},
                    {"voxel_size": 0.05},
                    {"approx_sync": False},
                ],
            ),
            ComposableNode(
                package="rtabmap_util",
                plugin="rtabmap_util::ObstaclesDetection",
                name="obstacle_detection_rt",
                remappings=[("cloud", "/cropped_pointcloud")],
                parameters=[
                    {"frame_id": "camera_link"},
                    {"wait_for_transform": 1.0},
                    {"Grid/MaxGroundHeight": "0.04"},
                ],
            ),
        ],
        output="screen",
    )
    return launch.LaunchDescription([container])
