#!/usr/bin/python3

from typing import NamedTuple, TypeVar

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from concurrent.futures import ThreadPoolExecutor
from time import sleep
from enum import Enum
from std_msgs.msg import String
from pynput import keyboard
import numpy as np
from std_msgs.msg import Float32
from general_interfaces.msg import GripperControl
from general_interfaces.msg import ToggleMessage

T = TypeVar("T")

class Joy_IK_Controller(Node):

    class Velocity(Enum):
        x = 0
        y = 1
        z = 2
        lx = 3
        ly = 4
        lz = 5

    def __init__(self, node_name: str = "joy_ik_controls"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        self.pub_rate = self.get_param("pub_rate", rclpy.Parameter.Type.DOUBLE, 20.0)
        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.40)
        self.mode = self.get_param("mode", rclpy.Parameter.Type.STRING, "I")
        self.dirWP = self.get_param("dirWP", rclpy.Parameter.Type.INTEGER, 1)
        self.dirWR = self.get_param("dirWR", rclpy.Parameter.Type.INTEGER, 1)
        self.dirTW = self.get_param("dirTW", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL1 = self.get_param("dirL1", rclpy.Parameter.Type.INTEGER, 1)
        self.dirL2 = self.get_param("dirL2", rclpy.Parameter.Type.INTEGER, 1)

        self.servo_cmd_sent = False
        self.prev_svd_pressed = False
        self.svd_pressed = False

        self.arm_cmd = String()

        self.run = True
        self.tp_executor = ThreadPoolExecutor(max_workers=3)

        self.keyb_vel_sub = self.create_subscription(Float32, "/keyboard/arm_vel", self.keyb_cb, 20)
        self.keyb_vel_sub = self.create_subscription(Float32, "/keyboard/arm_vel_tw", self.keyb_tw_cb, 20)

        # max_vel:    global scalar [0.4, 1.0], set by dial, applied to ALL joints
        # max_vel_tw: tower-only scalar [0.1, 1.0], multiplied ON TOP of max_vel for tower only
        # Tower effective speed = max_vel * max_vel_tw
        self.max_vel = 1.0
        self.max_vel_tw = 1.0

        self.servo_pub = self.create_publisher(TwistStamped, '/servo_node/delta_twist_cmds', 20)
        self.twist_stamped_msg = TwistStamped()
        self.twist_stamped_msg.header.frame_id = 'base_footprint'

        self.vel_control_pub = self.create_publisher(GripperControl, '/gripper_control/gripper_velocities', 20)
        self.vel_control_msg = GripperControl()
        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 20)

        self.joy_sub_logitech = self.create_subscription(Joy, "/joy/arm_cmd_logitech", self.joy_cb_logitech, 20)
        self.joy_sub_xbox = self.create_subscription(Joy, "/joy/arm_cmd_xbox", self.joy_cb_xbox, 20)

        self.gpio_cmd = {'stepper1_en': False, 'stepper2_en': False, 'stepper3_en': False, 'stepper4_en': False}
        self.command = String()
        self.curr_cmd = ""
        self.prev_cmd = "!"

        self.STOP_AXES = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.prev_axes = [0.0,0.0,0.0,0.0,0.0,-2.0]
        self.curr_axes = [0.0,0.0,0.0,0.0,0.0,0.0]

        self.STOP_BTNS    = [0,0,0,0,0,0]
        self.prev_btns_lt = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.curr_btns_lt = [0,0,0,0,0,0,0,0,0,0,0,0,0]
        self.prev_btns_xb = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.curr_btns_xb = [0,0,0,0,0,0,0,0,0,0,0,0]
        self.speed_axis = [0.0]

        self.speed_raw = 0.0
        self.xb_btns = [0,1,2,3,4,5,6,7,8,9,10]
        self.xb_axes = []
        if self.mode == "I":
            self.xb_axes = [1, 0, 2, 5, 3, 4]
        else:
            self.xb_axes = [0, 1, 2, 3, 4, 5]

        self.lt_btns = [0,1,2,3,4,5,6,7,8,9,10,11]
        self.lt_axes = [2, 0, 1, 5, 4, 3]


    def joy_cb_logitech(self, message: Joy) -> None:
        btn_sum = 0
        btns_zero = True

        if (len(message.buttons) == 12):
            for i in range(12):
                btn_sum += message.buttons[i]
                self.curr_btns_lt[i] = message.buttons[self.lt_btns[i]]
            if btn_sum != 0:
                btns_zero = False

            self.curr_axes[2] = message.axes[self.lt_axes[3]]
            self.curr_axes[1] = message.axes[self.lt_axes[2]]
            self.curr_axes[0] = message.axes[self.lt_axes[0]]
            self.speed_raw = message.axes[self.lt_axes[5]]

            # DEBUG: uncomment to confirm dial raw value range
            # self.get_logger().info(f"speed_raw: {self.speed_raw}")

            self.joy_parser(message)

        elif (len(message.buttons) == 11):
            self.get_logger().info("Xbox wired to logitech port")
        else:
            self.get_logger().info("Wrong controller gooba")


    def joy_cb_xbox(self, message: Joy) -> None:
        if (len(message.buttons) == 11):
            for i in range(11):
                self.curr_btns_xb[i] = message.buttons[self.xb_btns[i]]

            self.curr_axes[3] = message.axes[self.xb_axes[1]]
            self.curr_axes[4] = message.axes[self.xb_axes[0]]
            self.svd_pressed = message.axes[self.xb_axes[2]] < 0
            self.joy_parser(message)

        elif (len(message.buttons) == 12):
            self.get_logger().info("Logitech wired to xbox port")
        else:
            self.get_logger().info("Wrong controller gooba")


    def joy_parser(self, message: Joy) -> None:

        btns_zero = True
        if not self.floatArrayEqual(self.curr_axes, self.prev_axes) or not btns_zero:
            self.prev_axes = self.curr_axes

            if not self.floatArrayEqual(self.curr_axes, self.STOP_AXES) or not btns_zero:

                self.arrayRoundToMaxVelocity()

                if self.mode == "I":

                    self.twist_stamped_msg.header.stamp = self.get_clock().now().to_msg()

                    self.twist_stamped_msg.twist.linear.x = self.curr_axes[0]
                    self.twist_stamped_msg.twist.linear.y = self.curr_axes[1]
                    self.twist_stamped_msg.twist.linear.z = self.curr_axes[2]

                    self.vel_control_msg.roll_velocity = self.curr_axes[3]
                    self.twist_stamped_msg.twist.angular.y = self.curr_axes[4]
                    self.twist_stamped_msg.twist.angular.z = self.curr_axes[5]

                    if len(message.buttons) == 2:
                        if self.curr_btns_sm[0]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_sm[0] * self.max_vel
                        elif self.curr_btns_sm[1]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_sm[1] * self.max_vel

                    elif len(message.buttons) == 12:
                        if self.curr_btns_lt[0]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_lt[0] * self.max_vel
                        elif self.curr_btns_lt[1]:
                            self.vel_control_msg.ee_velocity = self.curr_btns_lt[1] * self.max_vel

                    self.tp_executor.submit(self.servo_pub_cmd, self.twist_stamped_msg)
                    self.tp_executor.submit(self.vel_control_cmd, self.vel_control_msg)

                else:
                    # Dial axis mapping:
                    #   raw -1.0  →  max_vel 1.0  (full speed)
                    #   raw  0.0  →  max_vel 0.7
                    #   raw +1.0  →  max_vel 0.4  (slowest, at motor stall floor)
                    # Formula: new_speed = 0.4 + 0.6 * (1.0 - speed_raw) / 2.0
                    #         = 0.4 + 0.3 * (1.0 - speed_raw)
                    new_speed = round(0.4 + 0.3 * (1.0 + self.speed_raw), 3)
                    new_speed = max(0.4, min(1.0, new_speed))  # clamp to [0.4, 1.0]

                    if abs(new_speed - self.max_vel) > 0.01:
                        self.max_vel = new_speed
                        self.get_logger().info(f'Max vel: {self.max_vel}')

                    self.arrayRoundToMaxVelocity()

                    prev_svd_pressed = self.prev_svd_pressed

                    if self.curr_btns_lt[11] and not self.prev_btns_lt[11]:
                        self.toggle_verbose()
                    if self.curr_btns_lt[4] and not self.prev_btns_lt[4]:
                        new_tw_vel = round(self.max_vel_tw + 0.1, 1)
                        if new_tw_vel <= 1.0:
                            self.max_vel_tw = new_tw_vel
                            self.get_logger().info(f'Max tw scalar: {self.max_vel_tw}  →  tower speed: {round(self.max_vel * self.max_vel_tw, 3)}')
                    elif self.curr_btns_lt[5] and not self.prev_btns_lt[5]:
                        new_tw_vel = round(self.max_vel_tw - 0.1, 1)
                        if new_tw_vel >= 0.1:
                            self.max_vel_tw = new_tw_vel
                            self.get_logger().info(f'Max tw scalar: {self.max_vel_tw}  →  tower speed: {round(self.max_vel * self.max_vel_tw, 3)}')

                    if self.curr_btns_xb[4]:
                        self.send_servo_command('svu', 'Shoulder camera servo: up')
                    elif self.svd_pressed:
                        self.send_servo_command('svd', 'Shoulder camera servo: down')
                    else:
                        if prev_svd_pressed or self.prev_btns_xb[4]:
                            self.servo_cmd_sent = False
                            self.send_command("svs", "Stop shoulder camera servo")
                    self.prev_svd_pressed = self.svd_pressed

                    if self.curr_btns_xb[2] and not self.prev_btns_xb[2]:
                        self.toggle_gpio('stepper1_en', 'TW', 'stepper1')
                    if self.curr_btns_xb[3] and not self.prev_btns_xb[3]:
                        self.toggle_gpio('stepper2_en', 'WP', 'stepper2')
                    if self.curr_btns_xb[1] and not self.prev_btns_xb[1]:
                        self.toggle_gpio('stepper3_en', 'WR', 'stepper3')
                    if self.curr_btns_xb[0] and not self.prev_btns_xb[0]:
                        self.toggle_gpio('stepper4_en', 'EE', 'stepper4')

                    # Save state at the END of joy_parser (after all button reads)
                    self.prev_btns_lt = list(self.curr_btns_lt)
                    self.prev_btns_xb = list(self.curr_btns_xb)

                    self.curr_cmd = "S;"
                    self.curr_cmd += str(round(self.curr_axes[0]*self.dirTW, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[1]*self.dirL1, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[2]*self.dirL2, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[3]*self.dirWP, 2))
                    self.curr_cmd += ";"
                    self.curr_cmd += str(round(self.curr_axes[4]*self.dirWR, 2))
                    self.curr_cmd += ";"

                    if self.curr_btns_lt[0]:
                        self.curr_cmd += str(-round(self.max_vel, 2))
                    elif self.curr_btns_lt[1]:
                        self.curr_cmd += str(round(self.max_vel, 2))
                    else:
                        self.curr_cmd += "0.0"
                    self.curr_cmd += ";!"

                    if self.curr_cmd != self.prev_cmd:
                        self.prev_cmd = self.curr_cmd
                        self.command.data = self.curr_cmd
                        self.tp_executor.submit(self.cmd_pub_cmd, self.command)


    def servo_pub_cmd(self, servo_msg):
        self.servo_pub.publish(servo_msg)

    def send_servo_command(self, data: str, label: str):
        if not self.servo_cmd_sent:
            self.send_command(data, label)
            self.servo_cmd_sent = True

    def send_command(self, data: str, label: str):
        self.arm_cmd.data = f"{data};!"
        self.get_logger().info(label)
        self.cmd_pub.publish(self.arm_cmd)

    def your_gamepad_poll_loop(self):
        if self.prev_btns_lt:
            btn2_released = self.prev_btns_lt[2] and not self.curr_btns_lt[2]
            btn3_released = self.prev_btns_lt[3] and not self.curr_btns_lt[3]
            if btn2_released or btn3_released:
                self.servo_cmd_sent = False
                self.send_command("svs", "Stop shoulder camera servo")
        self.prev_btns_lt = list(self.curr_btns_lt)

    def vel_control_cmd(self, vel_msg):
        self.vel_control_pub.publish(vel_msg)

    def cmd_pub_cmd(self, cmd_msg):
        self.get_logger().info("Command sent: " + cmd_msg.data)
        self.cmd_pub.publish(cmd_msg)

    """
    Snaps curr_axes values to 0 or ±speed based on deadband.

    Dial sets max_vel in [0.4, 1.0] for all joints.
    Tower (index 0) additionally scaled by max_vel_tw (LB/RB buttons).
    Tower effective speed = max_vel * max_vel_tw.
    """
    def arrayRoundToMaxVelocity(self):
        # All non-tower axes: global max_vel only
        for i in range(1, len(self.curr_axes)):
            if self.curr_axes[i] > self.deadband:
                self.curr_axes[i] = self.max_vel
            elif self.curr_axes[i] < -self.deadband:
                self.curr_axes[i] = -self.max_vel
            else:
                self.curr_axes[i] = 0.0

        # Tower (index 0): global * tw scalar
        tw_speed = self.max_vel * self.max_vel_tw
        if self.curr_axes[0] > self.deadband:
            self.curr_axes[0] = tw_speed
        elif self.curr_axes[0] < -self.deadband:
            self.curr_axes[0] = -tw_speed
        else:
            self.curr_axes[0] = 0.0

    def keyb_cb(self, message: Float32) -> None:
        self.max_vel = round(message.data, 1)

    def keyb_tw_cb(self, message: Float32) -> None:
        self.max_vel_tw = round(message.data, 1)

    def floatArrayEqual(self, arr1, arr2, tol=1e-5):
        arr1 = np.array(arr1)
        arr2 = np.array(arr2)
        return np.all(np.abs(arr1 - arr2) < tol * np.maximum(np.abs(arr1), np.abs(arr2)))

    def get_param(
        self,
        param_name: str,
        param_type: rclpy.Parameter.Type,
        default_val: T | None = None,
        logging: bool = True,
    ) -> T:
        self.declare_parameter(param_name, param_type)
        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = Parameter(param_name, param_type, default_val)
            param_val = self.get_parameter_or(param_name, default_param).value
        assert param_val is not None, "The parameter received was None."
        if logging:
            self.get_logger().info(f"Using {param_name}: {param_val}")
        return param_val

    def toggle_gpio(self, attr: str, label: str, cmd_str: str):
        self.gpio_cmd[attr] = not self.gpio_cmd[attr]
        self.get_logger().info(f'{label} toggled: {self.gpio_cmd[attr]}')
        if self.mode == 'M':
            self.arm_cmd.data = f"{cmd_str};!"
            self.cmd_pub.publish(self.arm_cmd)
        else:
            self.gpio_pub.publish(self.gpio_cmd)

    def toggle_verbose(self):
        self.get_logger().info('Verbose toggled')
        if self.mode == 'M':
            msg = String()
            msg.data = "v;!"
            self.cmd_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    controller = Joy_IK_Controller()
    rclpy.spin(controller)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
