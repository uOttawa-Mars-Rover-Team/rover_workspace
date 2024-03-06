from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    drive_control = Node(
            name="drive_control",
            package="chassis_controls",
            executable="drive_control",
            output="screen")

    power_data = Node(
            name="power_data",
            package="chassis_controls",
            executable="power_data",
            output="screen")

    return LaunchDescription([drive_control, power_data])



