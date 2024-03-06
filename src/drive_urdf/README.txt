instructions for rviz demo

    cd ws and build
    ros2 launch drive_urdf launch.py
    bottom right corner -> add -> RobotModel
    set Fixed Frame -> base_link and Description Topic -> /robot_description

it should automatically open the joint state publisher also
