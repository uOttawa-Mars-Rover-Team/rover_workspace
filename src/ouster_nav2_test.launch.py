#!/usr/bin/env python3
"""
One-file basic test: Ouster OS0-32 -> /scan -> SLAM Toolbox -> Nav2 (ROS 2 Jazzy).

What this does:
  1. Starts the Ouster driver (live data over Ethernet)
  2. Flattens the 3D point cloud into a 2D laser scan on /scan
  3. Publishes the TF links Nav2 needs (base_link -> os_sensor, and a
     temporary fixed odom -> base_link so you can test WITHOUT wheel odometry)
  4. Runs SLAM Toolbox (builds a live map, no pre-made map needed)
  5. Runs the Nav2 navigation stack (planner, controller, costmaps)

Run it like this (replace with your sensor's IP or hostname):
  ros2 launch ouster_nav2_test.launch.py sensor_hostname:=192.168.1.100

If running inside a Docker dev container on Windows, also pass your Windows
machine's IP on the lidar adapter, so the sensor sends data somewhere Docker
can forward from (and publish UDP ports 7502/7503 in devcontainer.json):
  ros2 launch ouster_nav2_test.launch.py sensor_hostname:=169.254.x.x udp_dest:=169.254.y.y

NOTE: the odom -> base_link transform here is a fixed placeholder so the
whole pipeline runs on a bench. For real driving you must replace it with
real odometry from your robot base, and connect /cmd_vel to your motors.
"""

import os

import lifecycle_msgs.msg
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent,
                            IncludeLaunchDescription, RegisterEventHandler,
                            TimerAction)
from launch.events import matches_action
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import LifecycleNode, Node
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState


def generate_launch_description():
    sensor_hostname = LaunchConfiguration('sensor_hostname')

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # Defined up here so the lifecycle events below can reference it.
    driver = LifecycleNode(
        package='ouster_ros',
        executable='os_driver',
        name='os_driver',
        namespace='sensor_msgs',   # topics come out as /sensor_msgs/PointCloud2 etc.
        output='screen',
        parameters=[{
            'sensor_hostname': sensor_hostname,
            'udp_dest': LaunchConfiguration('udp_dest'),
            # Fixed ports so Docker port-forwarding (-p 7502:7502/udp etc.)
            # lines up with where the driver actually listens:
            'lidar_port': 7502,
            'imu_port': 7503,
            'timestamp_mode': 'TIME_FROM_ROS_TIME',
            # Half the horizontal resolution = half the network traffic.
            # 1024 columns at 10 Hz is plenty for SLAM/Nav2, and it cuts
            # UDP packet drops through Docker dramatically. Set back to
            # '2048x10' on the Jetson if you want max detail there.
            ### 'lidar_mode': '1024x10', 
            # Only run the point-cloud processor. The extra processors
            # (2D images / laser scan / telemetry) expect a 'WINDOW' packet
            # field that this sensor's firmware (2.5.3) doesn't send, and
            # they crash the driver. We only need /sensor_msgs/PointCloud2 anyway.
            'proc_mask': 'PCL',
            'viz': False,
        }],
    )

    # SLAM Toolbox is ALSO a managed lifecycle node on ROS 2 Jazzy - like
    # the driver, it does nothing until configured and activated (that's
    # why it never printed a single log line). Defined up here so the
    # lifecycle events below can reference it.
    slam = LifecycleNode(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        namespace='',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'odom_frame': 'odom',
            'map_frame': 'map',
            'base_frame': 'base_link',
            'scan_topic': '/scan',
            'mode': 'mapping',
            'resolution': 0.05,
            'max_laser_range': 20.0,
            'minimum_time_interval': 0.2,
            'transform_publish_period': 0.02,
        }],
    )

    return LaunchDescription([

        DeclareLaunchArgument(
            'sensor_hostname',
            default_value='os-122107000000.local',
            description="Ouster sensor IP address or hostname (find it with: avahi-browse -lr _roger._tcp  or check your DHCP/link-local IP)"
        ),

        DeclareLaunchArgument(
            'udp_dest',
            default_value='',
            description="Where the sensor should send its UDP data. Leave empty for auto (direct connection, e.g. on the Jetson). In a Windows dev container, set this to your Windows adapter's IP."
        ),

        # ------------------------------------------------------------------
        # 1) Ouster driver - publishes /sensor_msgs/PointCloud2 (3D cloud) + TF
        #    os_sensor -> os_lidar.  TIME_FROM_ROS_TIME avoids clock-mismatch
        #    TF errors on a fresh setup (no PTP sync needed).
        #
        #    NOTE: os_driver is a *managed lifecycle node* - it does nothing
        #    until told to configure and activate. The two blocks after the
        #    node below do exactly that automatically:
        #      launch -> (3s) -> CONFIGURE (connects to & sets up the sensor)
        #             -> when that finishes -> ACTIVATE (data starts flowing)
        # ------------------------------------------------------------------
        driver,

        # Send CONFIGURE a few seconds after launch (gives the node time to
        # come up). Configuring is the slow part: the driver contacts the
        # sensor and rewrites its udp_dest/ports, which can take ~30-60s.
        TimerAction(
            period=3.0,
            actions=[
                EmitEvent(event=ChangeState(
                    lifecycle_node_matcher=matches_action(driver),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                )),
            ],
        ),

        # The moment configuring succeeds (driver reaches 'inactive'),
        # send ACTIVATE so data starts streaming.
        RegisterEventHandler(
            OnStateTransition(
                target_lifecycle_node=driver,
                goal_state='inactive',
                entities=[
                    EmitEvent(event=ChangeState(
                        lifecycle_node_matcher=matches_action(driver),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )),
                ],
            ),
        ),

        # Duplicate the PointCloud2 stream for consumers using this topic.
        Node(
            package='topic_tools',
            executable='relay',
            name='pointcloud_relay',
            arguments=['/sensor_msgs/PointCloud2', '/foxglove_msgs/msg/LaserScan'],
            output='screen',
        ),

        # ------------------------------------------------------------------
        # 2) 3D cloud -> 2D /scan  (takes a horizontal slice of the cloud)
        # ------------------------------------------------------------------
        Node(
            package='pointcloud_to_laserscan',
            executable='pointcloud_to_laserscan_node',
            name='pc_to_scan',
            output='screen',
            remappings=[
                ('cloud_in', '/sensor_msgs/PointCloud2'),
                ('scan', '/scan'),
            ],
            parameters=[{
                'target_frame': 'base_link',
                'transform_tolerance': 0.1,
                'min_height': -0.3,   # slice of the cloud used for the scan,
                'max_height': 0.3,    # relative to base_link (metres)
                'angle_min': -3.14159,
                'angle_max': 3.14159,
                'angle_increment': 0.0087,  # ~0.5 degrees
                'range_min': 0.3,
                'range_max': 20.0,
                'use_inf': True,
            }],
        ),

        # ------------------------------------------------------------------
        # 3) TF glue
        # base_link -> os_sensor : where the lidar sits on the robot.
        # Change the first three numbers (x y z, metres) to match your mount,
        # e.g. lidar 30 cm above the base: 0 0 0.3
        # ------------------------------------------------------------------
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_sensor_tf',
            arguments=['--x', '0', '--y', '0', '--z', '0.1',
                       '--roll', '0', '--pitch', '0', '--yaw', '0',
                       '--frame-id', 'base_link',
                       '--child-frame-id', 'os_sensor'],
        ),

        # TEMPORARY fixed odometry so Nav2/SLAM run on a bench.
        # Replace with real wheel/IMU odometry for actual autonomous driving.
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='fake_odom_tf',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--roll', '0', '--pitch', '0', '--yaw', '0',
                       '--frame-id', 'odom',
                       '--child-frame-id', 'base_link'],
        ),

        # ------------------------------------------------------------------
        # 4) SLAM Toolbox - builds the map live and publishes map -> odom.
        #    Lifecycle-managed on Jazzy, so the two blocks below configure
        #    and activate it automatically, same as the Ouster driver.
        # ------------------------------------------------------------------
        slam,

        TimerAction(
            period=5.0,
            actions=[
                EmitEvent(event=ChangeState(
                    lifecycle_node_matcher=matches_action(slam),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                )),
            ],
        ),

        RegisterEventHandler(
            OnStateTransition(
                target_lifecycle_node=slam,
                goal_state='inactive',
                entities=[
                    EmitEvent(event=ChangeState(
                        lifecycle_node_matcher=matches_action(slam),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )),
                ],
            ),
        ),

        # ------------------------------------------------------------------
        # 5) Nav2 (planner, controller, costmaps, behavior trees)
        #    Uses Nav2's stock default parameters - they already expect
        #    /scan, base_link and odom, which is what we set up above.
        #    Velocity commands come out on /cmd_vel.
        # ------------------------------------------------------------------
        # Delayed 60s: the Ouster driver needs time to reconfigure the sensor
        # (udp_dest/ports) before data flows, and Nav2 aborts if no map shows
        # up within its timeout. Starting Nav2 late lets the sensor + SLAM
        # get going first.
        TimerAction(
            period=60.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
                    ),
                    launch_arguments={
                        'use_sim_time': 'false',
                        'autostart': 'true',
                    }.items(),
                ),
            ],
        ),
    ])
