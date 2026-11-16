import json
from pathlib import Path
import xml.etree.ElementTree as ET

package = Path.cwd() / "src/robotic_arm_description"
data = json.loads((package / "config/cad_geometry.json").read_text())

for folder in ("urdf", "config", "launch"):
    (package / folder).mkdir(exist_ok=True)

XACRO = "http://www.ros.org/wiki/xacro"
ET.register_namespace("xacro", XACRO)


def element(parent, tag, **attributes):
    return ET.SubElement(
        parent, tag, {key: str(value) for key, value in attributes.items()}
    )


def numbers(values):
    return " ".join(f"{value:.12g}" for value in values)


robot = ET.Element("robot", name="rover_arm")

element(
    robot, f"{{{XACRO}}}arg", name="mesh_root",
    default="$(find robotic_arm_description)/meshes"
)
element(
    robot, f"{{{XACRO}}}arg", name="controllers_file",
    default="$(find robotic_arm_description)/config/controllers.yaml"
)

robot.append(ET.Comment(
    "Prototype: limits, masses and inertias are provisional."
))

link_names = {
    name: "arm_" + name.lower() + "_link"
    for name in data["links"]
}

element(robot, "link", name="world")
anchor = element(robot, "joint", name="world_to_arm_base", type="fixed")
element(anchor, "parent", link="world")
element(anchor, "child", link=link_names["Base"])

colors = [
    "0.5 0.5 0.55 1",
    "0.75 0.25 0.15 1",
    "0.3 0.35 0.4 1",
    "0.5 0.55 0.6 1",
    "0.2 0.4 0.6 1",
    "0.6 0.6 0.65 1",
    "0.3 0.3 0.35 1",
]

for (name, info), color in zip(data["links"].items(), colors):
    link = element(robot, "link", name=link_names[name])

    visual = element(link, "visual")
    geometry = element(visual, "geometry")
    element(
        geometry, "mesh",
        filename=f"file://$(arg mesh_root)/visual/{name}.stl"
    )
    material = element(visual, "material", name=name + "_color")
    element(material, "color", rgba=color)

    collision = element(link, "collision")
    geometry = element(collision, "geometry")
    element(
        geometry, "mesh",
        filename=f"file://$(arg mesh_root)/collision/{name}.stl"
    )

    inertial = element(link, "inertial")
    element(
        inertial, "origin",
        xyz=numbers(info["provisional_com_m"]), rpy="0 0 0"
    )
    element(inertial, "mass", value=info["provisional_mass_kg"])
    ixx, iyy, izz = info["provisional_box_inertia"]
    element(
        inertial, "inertia",
        ixx=ixx, iyy=iyy, izz=izz,
        ixy=0, ixz=0, iyz=0
    )

controlled_joints = []

for info in data["joints"]:
    joint = element(
        robot, "joint", name=info["name"], type=info["type"]
    )
    element(joint, "parent", link=link_names[info["parent"]])
    element(joint, "child", link=link_names[info["child"]])
    element(joint, "origin", xyz=numbers(info["origin_m"]), rpy="0 0 0")

    if info["type"] == "revolute":
        controlled_joints.append(info["name"])
        element(joint, "axis", xyz=numbers(info["axis"]))
        joint.append(ET.Comment(
            "Temporary: +/-90 degrees from exported CAD pose, not hardware limits."
        ))
        element(
            joint, "limit",
            lower=-1.57079632679, upper=1.57079632679,
            velocity=0.25, effort=10.0
        )
        element(joint, "dynamics", damping=0.1, friction=0.0)

control = element(robot, "ros2_control", name="ArmGazeboSystem", type="system")
hardware = element(control, "hardware")
element(hardware, "plugin").text = "gz_ros2_control/GazeboSimSystem"

for name in controlled_joints:
    joint = element(control, "joint", name=name)
    command = element(joint, "command_interface", name="velocity")
    element(command, "param", name="min").text = "-0.25"
    element(command, "param", name="max").text = "0.25"
    position = element(joint, "state_interface", name="position")
    element(position, "param", name="initial_value").text = "0.0"
    element(joint, "state_interface", name="velocity")

gazebo = element(robot, "gazebo")
plugin = element(
    gazebo, "plugin",
    filename="libgz_ros2_control-system.so",
    name="gz_ros2_control::GazeboSimROS2ControlPlugin"
)
element(plugin, "parameters").text = "$(arg controllers_file)"

ET.indent(robot, space="  ")
ET.ElementTree(robot).write(
    package / "urdf/arm.urdf.xacro",
    encoding="utf-8", xml_declaration=True
)

controller_yaml = """controller_manager:
  ros__parameters:
    update_rate: 100
    use_sim_time: true
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster
    arm_velocity_controller:
      type: velocity_controllers/JointGroupVelocityController

arm_velocity_controller:
  ros__parameters:
    joints:
"""
controller_yaml += "".join(
    f"      - {name}\n" for name in controlled_joints
)
(package / "config/controllers.yaml").write_text(controller_yaml)

(package / "CMakeLists.txt").write_text("""cmake_minimum_required(VERSION 3.8)
project(robotic_arm_description)
find_package(ament_cmake REQUIRED)
install(DIRECTORY urdf meshes config launch
  DESTINATION share/${PROJECT_NAME})
ament_package()
""")

(package / "package.xml").write_text("""<?xml version="1.0"?>
<package format="3">
  <name>robotic_arm_description</name>
  <version>0.1.0</version>
  <description>CAD-derived rover arm simulation prototype.</description>
  <maintainer email="ocaro009@uottawa.ca">uOttawa Mars Rover Team</maintainer>
  <license>BSD</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <exec_depend>xacro</exec_depend>
  <exec_depend>robot_state_publisher</exec_depend>
  <exec_depend>ros_gz_sim</exec_depend>
  <exec_depend>ros_gz_bridge</exec_depend>
  <exec_depend>gz_ros2_control</exec_depend>
  <exec_depend>controller_manager</exec_depend>
  <exec_depend>joint_state_broadcaster</exec_depend>
  <exec_depend>velocity_controllers</exec_depend>
  <exec_depend>robotic_arm_controls</exec_depend>
  <exec_depend>ament_index_python</exec_depend>
  <exec_depend>launch</exec_depend>
  <exec_depend>launch_ros</exec_depend>
  <export><build_type>ament_cmake</build_type></export>
</package>
""")

print("Created arm.urdf.xacro, controllers.yaml, and ROS package files.")
print("Controlled joints:", ", ".join(controlled_joints))


# Apply validated prototype simulation settings.
# These values are provisional and are not hardware specifications.
arm_path = package / "urdf/arm.urdf.xacro"
ET.register_namespace("xacro", "http://www.ros.org/wiki/xacro")
tree = ET.parse(arm_path)
root = tree.getroot()

mount = root.find("./joint[@name='world_to_arm_base']")
if mount is None:
    raise RuntimeError("Base mounting joint is missing.")
origin = mount.find("origin")
if origin is None:
    origin = ET.SubElement(mount, "origin")
origin.set("xyz", "0 0 1.0")
origin.set("rpy", "0 0 0")

for name in ("shoulder_joint", "elbow_joint"):
    limit = root.find(f"./joint[@name='{name}']/limit")
    if limit is None:
        raise RuntimeError(f"Missing limit for {name}")
    limit.set("effort", "100.0")

tree.write(arm_path, encoding="utf-8", xml_declaration=True)

config_path = package / "config/controllers.yaml"
config = config_path.read_text()
config = config.replace(
    "    update_rate: 100\n",
    "    update_rate: 100\n    enforce_command_limits: true\n",
    1,
)
config_path.write_text(config)
print("Applied provisional mount, torque limits, and command-limit enforcement.")

# Strip trailing whitespace from generated Xacro.
arm_path.write_text(
    "\n".join(line.rstrip() for line in arm_path.read_text().splitlines()) + "\n"
)
