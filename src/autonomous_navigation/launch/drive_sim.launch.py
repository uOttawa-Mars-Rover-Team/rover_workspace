import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
)
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    package_name = "autonomous_navigation"

    # Config and URDF paths
    pkg_path = os.path.join(get_package_share_directory("autonomous_navigation"))
    urdf_file = os.path.join(pkg_path, "urdf", "drive_urdf.urdf")
    joy_config_file = os.path.join(
        get_package_share_directory("autonomous_navigation"),
        "config",
        "f310.config.yaml",
    )
    ekf_config_file = os.path.join(pkg_path, "config/ekf.yaml")
    gz_bridge_config_file = os.path.join(pkg_path, "config/gz_bridge.yaml")
    rviz_config_file = os.path.join(pkg_path, "rviz/urdf_config.rviz")
    gazebo_world_file = os.path.join(pkg_path, "world/smalltown.world")

    # URDF
    robot_description_config = xacro.process_file(urdf_file)

    # Launch configurations
    joy_device_launch_config = LaunchConfiguration(
        "joy_device"
    )  # Joystick device for teleop control

    # Launch arguments
    joy_device_arg = DeclareLaunchArgument("joy_device", default_value="/dev/input/js2")
    use_sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="True",
        description="Flag for node to follow sim clock",
    )
    rviz_config_arg = DeclareLaunchArgument(
        name="rvizconfig",
        default_value=rviz_config_file,
        description="Absolute path to rviz config file",
    )

    # Create a robot_state_publisher node
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description_config.toxml(),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }
        ],
    )

    # Spawn the robot into Gazebo from the robot_description topic. The entity
    # name doesn't really matter if you only have a single robot.
    gazebo_spawn_entity_node = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", "rover", "-z", "0.3"],
        output="screen",
    )

    # Bridge the Gazebo clock and the simulated sensors into ROS topics.
    gz_bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": gz_bridge_config_file,
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }
        ],
        output="screen",
    )

    # Gazebo (gz sim) finds meshes via GZ_SIM_RESOURCE_PATH and the
    # gz_ros2_control system plugin via GZ_SIM_SYSTEM_PLUGIN_PATH.
    ament_share_paths = os.pathsep.join(
        os.path.join(prefix, "share")
        for prefix in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep)
        if prefix
    )
    resource_path_action = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", ament_share_paths
    )
    plugin_path_action = AppendEnvironmentVariable(
        "GZ_SIM_SYSTEM_PLUGIN_PATH",
        os.path.join(os.environ.get("CONDA_PREFIX", "/usr"), "lib"),
    )
    ogre_path_action = AppendEnvironmentVariable(
        "OGRE2_RESOURCE_PATH",
        os.path.join(os.environ.get("CONDA_PREFIX", "/usr"), "lib", "OGRE-Next"),
    )

    diff_drive_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["diff_cont"]
    )

    joint_broad_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["joint_broad"]
    )

    joy_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node_sim",
        parameters=[
            {"dev": joy_device_launch_config, "deadzone": 0.3, "autorepeat_rate": 20.0}
        ],
    )

    teleop_node = Node(
        package="teleop_twist_joy",
        executable="teleop_node",
        name="teleop_twist_joy",
        parameters=[
            joy_config_file,
            {
                "max_speed": 1,
                "speed_levels": 3,
                "publish_stamped_twist": True,
            },
        ],
        remappings=[("cmd_vel", "diff_cont/cmd_vel")],
    )

    robot_localization_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[
            ekf_config_file,
            {"use_sim_time": LaunchConfiguration("use_sim_time")},
        ],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", LaunchConfiguration("rvizconfig")],
    )

    # Launch them all!
    return LaunchDescription(
        [
            joy_device_arg,
            use_sim_time_arg,
            rviz_config_arg,
            resource_path_action,
            plugin_path_action,
            ogre_path_action,
            # macOS cannot run the gz server and GUI in one process
            # (https://github.com/gazebosim/gz-sim/issues/44), so start them
            # separately; this also works on Linux.
            ExecuteProcess(
                cmd=["gz", "sim", "-s", "-r", gazebo_world_file],
                output="screen",
            ),
            ExecuteProcess(
                cmd=["gz", "sim", "-g"],
                output="screen",
            ),
            gz_bridge_node,
            robot_state_publisher_node,
            gazebo_spawn_entity_node,
            diff_drive_spawner,
            joint_broad_spawner,
            joy_node,
            teleop_node,
            robot_localization_node,
            rviz_node,
        ]
    )
