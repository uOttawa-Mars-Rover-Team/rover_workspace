#!/usr/bin/env python3
"""
Launch joy_node + rover teleop controller together.

Usage:
    ros2 launch chassis_controls controller.launch.py
"""

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():

    # Same env vars your old controller.sh set.
    # controller.py reads these via os.environ.get(...).
    env_vars = [
        SetEnvironmentVariable('ROS_DOMAIN_ID',   '0'),
        SetEnvironmentVariable('JETSON_IP',       '192.168.1.201'),
        SetEnvironmentVariable('OUTPUT_TOPIC',    'cmd_vel_teleop'),
        SetEnvironmentVariable('ARM_CMD_TOPIC',   '/arm_cmd'),
        SetEnvironmentVariable('ENABLE_BUTTON',   '4'),
        SetEnvironmentVariable('SPEED_BUTTON',    '0'),
        SetEnvironmentVariable('TURN_BUTTON',     '2'),
        SetEnvironmentVariable('DEFAULT_SPEED',   '0.7'),
        SetEnvironmentVariable('DEFAULT_TURN',    '0.4'),
    ]

    # Physical gamepad -> /joy
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        parameters=[{
            'device_id': 0,
            'deadzone': 0.05,
            'autorepeat_rate': 20.0,
        }],
        output='log',   # keep quiet so it doesn't garble the TUI
        arguments=['--ros-args', '--log-level', 'WARN'],
    )

    # Your teleop TUI node
    controller_node = Node(
        package='chassis_controls',
        executable='controller.py',   # keeps .py because it's ament_cmake
        name='combined_teleop',
        output='screen',
        emulate_tty=True,             # required for the ANSI TUI to render
    )

    return LaunchDescription(env_vars + [joy_node, controller_node])