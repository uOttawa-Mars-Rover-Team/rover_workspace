import os
import xacro
from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_chassis = get_package_share_directory("chassis_controls")

    xacro_file = os.path.join(pkg_chassis, "description", "urdf", "rover_gazebo.urdf.xacro")
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{
            "robot_description": robot_description_raw,
            "use_sim_time": True
        }],
    )

    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py"
            ])
        ]),
        launch_arguments={"gz_args": "-r empty.sdf"}.items(),
    )

    spawn_entity_node = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-string", robot_description_raw,
            "-name", "rover",
            "-z", "0.5"
        ],
        output="screen",
    )

    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist",
            "/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry",
            "/imu/data@sensor_msgs/msg/Imu@gz.msgs.IMU",
            "/scan/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked",
        ],
        output="screen",
    )

    return LaunchDescription([
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", pkg_chassis),
        robot_state_publisher_node,
        gz_sim_launch,
        spawn_entity_node,
        ros_gz_bridge,
    ])