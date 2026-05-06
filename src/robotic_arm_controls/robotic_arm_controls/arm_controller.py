"""
arm_controller.py
=================
Extends DualJoystickArmController to support per-operator YAML configs
with logical axis/button names via DeviceRegistry.

Backward compatible: the original flat YAML format still works unchanged.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from general_interfaces.msg import GripperControl
from builtin_interfaces.msg import Duration

from .device_registry import DeviceRegistry, DeviceSpec


class ArmControllerNode(Node):

    _ARM_JOINTS = ("q1", "q2", "q3", "q4")

    def __init__(self, registry: DeviceRegistry | None = None):
        super().__init__("arm_controller_node")

        self._registry = registry

        # Core params — identical to original
        self.control_mode        = self._get_param("control_mode",        Parameter.Type.STRING, "single")
        self.control_rate        = self._get_param("control_rate",         Parameter.Type.DOUBLE, 50.0)
        self.deadzone            = self._get_param("deadzone",             Parameter.Type.DOUBLE, 0.15)
        self.max_joint_velocity  = self._get_param("max_joint_velocity",   Parameter.Type.DOUBLE, 0.5)
        self.trajectory_duration = self._get_param("trajectory_duration",  Parameter.Type.DOUBLE, 0.1)

        # Mapping cache — built once on first Joy message, same as original
        self._mapping_1: dict = {}
        self._mapping_2: dict = {}

        self.joy_data_1: Joy | None = None
        self.joy_data_2: Joy | None = None
        self.current_joint_positions = [0.0] * 4

        # Topics — from operator YAML if present, else original defaults
        topic_1 = self._get_param("controller_1.topic", Parameter.Type.STRING, "/joy/controller_1")
        topic_2 = self._get_param("controller_2.topic", Parameter.Type.STRING, "/joy/controller_2")

        self.joy_sub_1 = self.create_subscription(Joy, topic_1, self.joy_callback_1, 20)
        if self.control_mode == "dual":
            self.joy_sub_2 = self.create_subscription(Joy, topic_2, self.joy_callback_2, 20)

        self.joint_state_sub = self.create_subscription(
            JointState, "/joint_states", self.joint_state_callback, 10
        )
        self.joint_state_pub = self.create_publisher(
            JointTrajectory, "/uorover_arm_controller/joint_trajectory", 10
        )
        self.gripper_pub = self.create_publisher(
            GripperControl, "/gripper_control/gripper_velocities", 10
        )

        self.get_logger().info(f"ArmControllerNode started [{self.control_mode} mode]")

    # ------------------------------------------------------------------
    # Joy callbacks — identical structure to original
    # ------------------------------------------------------------------

    def joy_callback_1(self, msg: Joy) -> None:
        if not self._mapping_1:
            self._mapping_1 = self._build_mapping(msg, slot=1)
            if not self._mapping_1:
                return
        self.joy_data_1 = msg
        self.publish_trajectory_command()
        if self.control_mode == "single":
            self.publish_gripper_command()

    def joy_callback_2(self, msg: Joy) -> None:
        if self.control_mode != "dual":
            return
        if not self._mapping_2:
            self._mapping_2 = self._build_mapping(msg, slot=2)
            if not self._mapping_2:
                return
        self.joy_data_2 = msg
        self.publish_gripper_command()

    def joint_state_callback(self, msg: JointState) -> None:
        for i, name in enumerate(msg.name):
            if name in self._ARM_JOINTS:
                self.current_joint_positions[int(name[1]) - 1] = msg.position[i]

    # ------------------------------------------------------------------
    # Publishing — identical to original
    # ------------------------------------------------------------------

    def publish_trajectory_command(self) -> None:
        if self.joy_data_1 is None:
            return

        m  = self._mapping_1
        dt = 1.0 / self.control_rate
        target_positions = [
            self.current_joint_positions[0] + self.process_axis(self.joy_data_1, m, "q1") * dt,
            self.current_joint_positions[1] + self.process_axis(self.joy_data_1, m, "q2") * dt,
            self.current_joint_positions[2] + self.process_axis(self.joy_data_1, m, "q3") * dt,
            self.current_joint_positions[3] + self.process_axis(self.joy_data_1, m, "q4") * dt,
        ]

        trajectory = JointTrajectory()
        trajectory.joint_names = list(self._ARM_JOINTS)
        trajectory.header.stamp = self.get_clock().now().to_msg()
        point = JointTrajectoryPoint()
        point.positions = target_positions
        point.time_from_start = Duration(sec=0, nanosec=int(self.trajectory_duration * 1e9))
        trajectory.points = [point]
        self.joint_state_pub.publish(trajectory)

    def publish_gripper_command(self) -> None:
        joy_data = self.joy_data_1 if self.control_mode == "single" else self.joy_data_2
        mapping  = self._mapping_1 if self.control_mode == "single" else self._mapping_2
        if joy_data is None:
            return

        gripper_msg = GripperControl()

        # q5 — roll
        if mapping.get("q5", -1) >= 0:
            gripper_msg.roll_velocity = self.process_axis(joy_data, mapping, "q5")
        else:
            if self._get_button(joy_data, mapping.get("roll_cw_button", -1)):
                gripper_msg.roll_velocity = self.max_joint_velocity
            elif self._get_button(joy_data, mapping.get("roll_ccw_button", -1)):
                gripper_msg.roll_velocity = -self.max_joint_velocity
            else:
                gripper_msg.roll_velocity = 0.0

        # q6 — end-effector
        if mapping.get("q6", -1) >= 0:
            gripper_msg.ee_velocity = self.process_axis(joy_data, mapping, "q6")
        else:
            if self._get_button(joy_data, mapping.get("gripper_open_button", -1)):
                gripper_msg.ee_velocity = self.max_joint_velocity
            elif self._get_button(joy_data, mapping.get("gripper_close_button", -1)):
                gripper_msg.ee_velocity = -self.max_joint_velocity
            else:
                gripper_msg.ee_velocity = 0.0

        self.gripper_pub.publish(gripper_msg)

    # ------------------------------------------------------------------
    # process_axis — original logic
    # ------------------------------------------------------------------

    def process_axis(self, joy_msg: Joy, mapping: dict, joint_name: str) -> float:
        axis_idx = mapping.get(joint_name, -1)
        if axis_idx < 0 or axis_idx >= len(joy_msg.axes):
            return 0.0

        value = joy_msg.axes[axis_idx]
        if abs(value) < self.deadzone:
            return 0.0

        scale       = mapping.get(f"{joint_name}_scale", 1.0)
        invert      = mapping.get(f"{joint_name}_invert", False)

        sign       = 1.0 if value >= 0 else -1.0
        normalised = sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)

        velocity = normalised * self.max_joint_velocity * scale
        if invert:
            velocity = -velocity
        return velocity

    # ------------------------------------------------------------------
    # Mapping builder — registry path first, flat-param fallback second
    # ------------------------------------------------------------------

    def _build_mapping(self, msg: Joy, slot: int) -> dict:
        """
        Called once on first Joy message for each slot, result cached.
        Tries registry (logical names from operator YAML) first.
        Falls back to original controller_types.<type>.* flat params.
        """
        category = self._get_param(f"controller_{slot}.category", Parameter.Type.STRING, "")
        device   = self._get_param(f"controller_{slot}.device",   Parameter.Type.STRING, "")

        if category and self._registry is not None:
            spec = (
                self._registry.get_device(category, device)
                if device else
                self._registry.detect_device(category, len(msg.buttons), len(msg.axes))
            )
            if spec is not None:
                mapping = self._mapping_from_registry(spec, slot)
                if mapping:
                    self.get_logger().info(
                        f"Controller {slot}: matched registry device '{spec.name}'"
                    )
                    return mapping

        # Original fallback: detect by button count
        if len(msg.buttons) == 11:
            controller_type = "xbox"
        elif len(msg.buttons) == 12:
            controller_type = "logitech"
        else:
            controller_type = self._get_param(
                f"controller_{slot}_type", Parameter.Type.STRING, ""
            )
            if not controller_type:
                self.get_logger().error(
                    f"Controller {slot}: unknown button count ({len(msg.buttons)}), "
                    f"no controller_type param set"
                )
                return {}

        self.get_logger().info(
            f"Controller {slot}: fallback detected '{controller_type}' "
            f"from button count ({len(msg.buttons)})"
        )
        return self._mapping_from_params(controller_type)

    def _mapping_from_registry(self, spec: DeviceSpec, slot: int) -> dict:
        """Build mapping dict from DeviceSpec + operator YAML binding params."""
        mapping: dict = {}
        prefix = f"controller_{slot}.bindings"

        for joint in ("q1", "q2", "q3", "q4", "q5", "q6"):
            logical = self._get_param(f"{prefix}.{joint}.axis", Parameter.Type.STRING, "")
            if logical:
                raw = spec.raw_axis(logical)
                if raw < 0:
                    self.get_logger().warn(
                        f"Controller {slot}: '{logical}' not in spec '{spec.name}' "
                        f"— {joint} disabled"
                    )
                mapping[joint]                  = raw
                mapping[f"{joint}_scale"]       = self._get_param(f"{prefix}.{joint}.scale",       Parameter.Type.DOUBLE, 1.0)
                mapping[f"{joint}_invert"]      = self._get_param(f"{prefix}.{joint}.invert",      Parameter.Type.BOOL,   False)
            else:
                mapping[joint] = -1

        for btn in ("gripper_open_button", "gripper_close_button",
                    "roll_cw_button", "roll_ccw_button"):
            logical = self._get_param(f"{prefix}.{btn}", Parameter.Type.STRING, "")
            mapping[btn] = spec.raw_button(logical) if logical else -1

        return mapping

    def _mapping_from_params(self, controller_type: str) -> dict:
        """Original flat controller_types.<type>.* param format."""
        prefix  = f"controller_types.{controller_type}"
        mapping: dict = {}
        for i in range(1, 7):
            j = f"q{i}"
            mapping[j]                  = self._get_param(f"{prefix}.{j}_axis",  Parameter.Type.INTEGER, -1)
            mapping[f"{j}_scale"]       = self._get_param(f"{prefix}.{j}_scale", Parameter.Type.DOUBLE,  1.0)
            mapping[f"{j}_invert"]      = self._get_param(f"{prefix}.{j}_invert",Parameter.Type.BOOL,    False)
        mapping["roll_cw_button"]       = self._get_param(f"{prefix}.roll_cw_button",      Parameter.Type.INTEGER, -1)
        mapping["roll_ccw_button"]      = self._get_param(f"{prefix}.roll_ccw_button",      Parameter.Type.INTEGER, -1)
        mapping["gripper_open_button"]  = self._get_param(f"{prefix}.gripper_open_button",  Parameter.Type.INTEGER, -1)
        mapping["gripper_close_button"] = self._get_param(f"{prefix}.gripper_close_button", Parameter.Type.INTEGER, -1)
        return mapping

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_button(self, joy_msg: Joy, button_idx: int) -> bool:
        if button_idx < 0 or button_idx >= len(joy_msg.buttons):
            return False
        return joy_msg.buttons[button_idx] == 1

    def _get_param(self, name: str, param_type: Parameter.Type, default):
        try:
            self.declare_parameter(name, default)
        except Exception:
            pass  # already declared
        # Use get_parameter_or so undeclared/unset params return the default
        # instead of raising ParameterNotDeclaredException
        return self.get_parameter_or(
            name, Parameter(name, param_type, default)
        ).value


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)

    try:
        from ament_index_python.packages import get_package_share_directory
        import os
        registry = DeviceRegistry.from_yaml(
            os.path.join(
                get_package_share_directory("robotic_arm_controls"),
                "config", "devices.yaml"
            )
        )
    except Exception:
        registry = None

    node = ArmControllerNode(registry=registry)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()