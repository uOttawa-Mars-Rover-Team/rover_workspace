import os
from ament_index_python import get_package_share_directory
from ament_index_python.packages import get_package_share_directory
from launch_ros.substitutions import FindPackageShare

import xacro
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

#THis code relies on the realsense packages:
#librealsense2-dkms, librealsense2-dev, librealsense2-utils


#Terminal commands:
#ros2 launch autonomous_navigation 3d_depth_cam.launch.py 
#ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 map odom
#ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom base_link
#rviz2



def generate_launch_description():
    pkg_path = os.path.join(get_package_share_directory("autonomous_navigation"))

    urdf_file = os.path.join(pkg_path, "urdf", "ab1", "robot.urdf.xacro")
    robot_description_config = xacro.process_file(urdf_file)
    rviz_config_file = os.path.join(pkg_path, "rviz/nav2_config.rviz")

    #copied from waypoints.launch.py
    nav2_params = os.path.join(pkg_path, "config/nav2_no_map_params.yaml")
    configured_params = RewrittenYaml(
        source_file=nav2_params, root_key="", param_rewrites="", convert_types=True
    )
    remappings =[]

    obstacles_detection = Node(
        package='rtabmap_util',
        #namespace='obstacles_detection',
        executable='obstacles_detection',
        name='sim',

        remappings = remappings + [

            ('cloud', 'camera/camera/depth/color/points'),

            #publish to obstacles
            ("obstacles","/filtered/obstacles"),
            #publish to ground
            ("ground","/filtered/ground")
        ],
        parameters = [nav2_params],
        output='screen'
    )

    # copied from waypoints.launch.py
    use_sim_time_arg = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="False",
        description="Flag for node to follow sim clock",
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

    #copied from waypoints.launch.py
    rviz_config_arg = DeclareLaunchArgument(
        name="rvizconfig",
        default_value=rviz_config_file,
        description="Absolute path to rviz config file",
    )
    #copied from waypoints.launch.py
    navigation2_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_path, "launch", "navigation.launch.py")),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file": configured_params,
            "autostart": "True",
        }.items(),
    )


#ros2 launch realsense2_camera rs_launch.py depth_module.profile:=640x480x30 pointcloud.enable:=True


    rs_cam_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("realsense2_camera"), "launch", "rs_launch.py"
            )
        ),
        launch_arguments={"pointcloud.enable": "true"}.items(),
    )


    return LaunchDescription([
        obstacles_detection,
        rviz_config_arg,
        use_sim_time_arg,
        rs_cam_cmd,
        navigation2_cmd,
        robot_state_publisher_node


    ])