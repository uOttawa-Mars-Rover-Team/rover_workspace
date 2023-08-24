from typing import NamedTuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy

from general_interfaces.msg import ArmControl


class AxesValues(NamedTuple):
    """
    Define properties for each of the 6 axes on the joystick
    """

    y_axis: float
    x_axis: float
    _: float
    z_axis: float
    wrist_roll: float
    wrist_pitch: float


class ButtonValues(NamedTuple):
    """
    Define properties for each of the 12 buttons on the joystick
    """

    ee_close_btn: int
    ee_open_btn: int
    _: int
    _: int
    _: int
    _: int
    half_speed_btn: int
    norm_speed_btn: int
    onepfive_speed_btn: int
    double_speed_btn: int
    _: int
    _: int


class IKArmControllerNode(Node):
    """
    Initializes a node to receive Joy messages from the joystick, which are
    published as ArmControl messages to a topic and eventually used to perform
    inverse kinematics for the robot arm.
    """

    # Default Constants
    DEADBAND = 0.35
    DEFAULT_MULTIPLIER = 1

    def __init__(self, node_name: str = "ik_arm_controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Subscribe to joystick control messages
        self.joy_subscriber = self.create_subscription(
            Joy, "joy", self.joy_control_callback, 10
        )
        self.get_logger().info(
            f"Subscribing to messages from: {self.joy_subscriber.topic_name}"
        )

        # Set the multiplier using the default value, allowing it to change
        # depending on the speed buttons
        self.multiplier = self.DEFAULT_MULTIPLIER

        # Publish messages to the inverse kinematics (ik) topic
        self.ik_control_publisher = self.create_publisher(ArmControl, "ik_msg", 1000)

        # Serial settings
        #
        # self.ARDUINO = serial.Serial(port='/dev/ttyACM0', baudrate=115200, timeout=.1)

    def joy_control_callback(self, message: Joy) -> None:
        # Unpack each of the message.axes array and message.buttons array into
        # an AxesValues and ButtonValues named tuple, respectively
        axes_values = AxesValues(*message.axes)
        btn_values = ButtonValues(*message.buttons)
        movements = ArmControl()

        """
        if btn_values.half_speed_btn:
            self.multiplier = 3
            self.get_logger().info("Speed multiplier changed to 12.5%")
        elif btn_values.half_speed_btn:
            self.multiplier = 2
            self.get_logger().info("Speed multiplier changed to 25%")
        elif btn_values.norm_speed_btn:
            self.multiplier = 1
            self.get_logger().info("Speed multiplier changed to 50%")
        elif btn_values.double_speed_btn:
            self.multiplier = 0
            self.get_logger().info("Speed multiplier changed to 100%")
        """

        # Main axes:
        #
        # Big stick forward/backward
        if abs(axes_values.x_axis) >= self.DEADBAND:
            movements.dx = int(axes_values.x_axis * 1000) >> self.multiplier
        # Big stick side-to-side
        if abs(axes_values.y_axis) >= self.DEADBAND:
            movements.dy = int(axes_values.y_axis * 1000) >> self.multiplier

        """
        # Dial up/down
        if abs(axes_values.z_axis) >= self.DEADBAND:
            movements.dz = int(axes_values.z_axis * 1000) >> self.multiplier

        # Wrist
        #
        # Small joy up/down
        if abs(axes_values.wrist_pitch) >= self.DEADBAND:
            movements.wp = int((axes_values.wrist_pitch / 2.0) * self.multiplier * 10)

        # Small joy side-to-side
        if abs(axes_values.wrist_roll) >= self.DEADBAND:
            movements.wr = int((axes_values.wrist_roll / 2.0) * self.multiplier * 10)
        """

        # End-effector
        #
        # Front trigger: close
        if btn_values.ee_close_btn:
            movements.ee = 16 >> self.multiplier
        # Thumb trigger: open
        if btn_values.ee_open_btn:
            movements.ee = 16 >> self.multiplier

        # Move the arm
        self.pub_ik_message(movements)

    def pub_ik_message(self, message: ArmControl) -> None:
        self.ik_control_publisher.publish(message)
        # Log the message sent, and the specific topic name it was sent to
        self.get_logger().info(
            f"Sent to {self.ik_control_publisher.topic_name} data: {message}"
        )


def main(args=None):
    rclpy.init(args=args)
    ik_arm_controller_node = IKArmControllerNode()
    rclpy.spin(ik_arm_controller_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
