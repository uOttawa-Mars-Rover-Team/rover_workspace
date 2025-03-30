from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command


def generate_launch_description():

    # launch configurations
    use_sim_time_launch_config = LaunchConfiguration("use_sim_time")
    robot_description_file = LaunchConfiguration("robot_description_file")
    gazebo_world_file = LaunchConfiguration("gazebo_world_file")

    # declare args
    use_sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="True",
        description="Flag for node to follow sim clock",
    )

    robot_description_file_arg = DeclareLaunchArgument(
        name="robot_description_file",
        description="Path to robot description urdf file",
    )

    gazebo_world_file_arg = DeclareLaunchArgument(
        name="gazebo_world_file",
        description="Path to gazebo world file",
    )

    # nodes
    # Create a robot_state_publisher node
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": Command(["xacro ", robot_description_file]),
                "use_sim_time": use_sim_time_launch_config,
            }
        ],
    )

    joint_broad_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["joint_broad"]
    )

    diff_drive_spawner = Node(
        package="controller_manager", executable="spawner", arguments=["diff_cont"]
    )

    # Run the spawner node from the gazebo_ros package.
    # The entity name doesn't really matter if you only have a single robot.
    gazebo_spawn_entity_node = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-topic", "robot_description", "-entity", "rover"],
        output="screen",
    )

    gazebo_server_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("gazebo_ros"),
                        "launch",
                        "gzserver.launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "world": gazebo_world_file,
        }.items(),
    )

    gazebo_client_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("gazebo_ros"),
                        "launch",
                        "gzclient.launch.py",
                    ]
                )
            ]
        )
    )

    # generate launch description
    return LaunchDescription(
        [
            use_sim_time_arg,
            robot_description_file_arg,
            gazebo_world_file_arg,
            gazebo_server_cmd,
            gazebo_client_cmd,
            robot_state_publisher_node,
            gazebo_spawn_entity_node,
            diff_drive_spawner,
            joint_broad_spawner,
        ]
    )
