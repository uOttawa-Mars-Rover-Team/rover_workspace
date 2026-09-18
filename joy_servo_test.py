#!/usr/bin/env python3
"""
D-pad -> /arm_cmd publisher. Sends ONLY when state changes.
Auto-detects if D-pad is axes or buttons.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import String


# ---------- Config ----------
JOY_TOPIC = "/joy"
CMD_TOPIC = "/arm_cmd"

INVERT_X = False
INVERT_Y = False
# ----------------------------


class JoyServoTest(Node):
    def __init__(self):
        super().__init__("joy_servo_test")
        self.get_logger().info("D-pad publisher started (sends only on change)")

        self.last_cmd = None
        self.detected = False
        
        # D-pad mode: "axes" or "buttons"
        self.dpad_mode = None
        
        # For axes mode
        self.axis_x_idx = None
        self.axis_y_idx = None
        
        # For buttons mode (common mappings)
        # Xbox/GameSir style: 11=up, 12=down, 13=left, 14=right
        # Or: 12=up, 13=down, 14=left, 15=right
        self.btn_up = None
        self.btn_down = None
        self.btn_left = None
        self.btn_right = None

        self.cmd_pub = self.create_publisher(String, CMD_TOPIC, 20)
        self.create_subscription(Joy, JOY_TOPIC, self.joy_callback, 10)

    def detect_layout(self, msg: Joy):
        """Auto-detect D-pad as axes or buttons."""
        num_axes = len(msg.axes)
        num_buttons = len(msg.buttons)
        
        self.get_logger().info(f"Controller: {num_axes} axes, {num_buttons} buttons")
        
        # Check if D-pad is on axes (8+ axes usually means axes 6/7 are dpad)
        if num_axes >= 8:
            self.dpad_mode = "axes"
            self.axis_x_idx = 6
            self.axis_y_idx = 7
            self.get_logger().info("D-pad detected as AXES (6/7)")
            return True
        
        # Check for 6-axis controller (axes 4/5 might be dpad)
        if num_axes == 6:
            self.dpad_mode = "axes"
            self.axis_x_idx = 4
            self.axis_y_idx = 5
            self.get_logger().info("D-pad detected as AXES (4/5)")
            return True
        
        # Otherwise assume D-pad is buttons
        if num_buttons >= 15:
            # Common mapping: buttons 11-14 or 12-15
            self.dpad_mode = "buttons"
            if num_buttons >= 16:
                self.btn_up = 12
                self.btn_down = 13
                self.btn_left = 14
                self.btn_right = 15
            else:
                self.btn_up = 11
                self.btn_down = 12
                self.btn_left = 13
                self.btn_right = 14
            self.get_logger().info(
                f"D-pad detected as BUTTONS (up={self.btn_up}, down={self.btn_down}, "
                f"left={self.btn_left}, right={self.btn_right})"
            )
            return True
        
        # Fallback: try buttons 11-14
        if num_buttons >= 12:
            self.dpad_mode = "buttons"
            self.btn_up = 11
            self.btn_down = 12
            self.btn_left = 13
            self.btn_right = 14
            self.get_logger().warn(
                f"Guessing D-pad as BUTTONS (up={self.btn_up}, down={self.btn_down}, "
                f"left={self.btn_left}, right={self.btn_right})"
            )
            return True
        
        self.get_logger().error("Could not detect D-pad layout")
        return False

    def get_dpad_values(self, msg: Joy):
        """Returns (x, y) where x is left/right, y is up/down. Values are -1, 0, or 1."""
        x_val = 0
        y_val = 0
        
        if self.dpad_mode == "axes":
            x_raw = msg.axes[self.axis_x_idx]
            y_raw = msg.axes[self.axis_y_idx]
            
            if INVERT_X:
                x_raw = -x_raw
            if INVERT_Y:
                y_raw = -y_raw
            
            if x_raw > 0.5:
                x_val = 1
            elif x_raw < -0.5:
                x_val = -1
            
            if y_raw > 0.5:
                y_val = 1
            elif y_raw < -0.5:
                y_val = -1
        
        elif self.dpad_mode == "buttons":
            if self.btn_left < len(msg.buttons) and msg.buttons[self.btn_left]:
                x_val = 1
            elif self.btn_right < len(msg.buttons) and msg.buttons[self.btn_right]:
                x_val = -1
            
            if self.btn_up < len(msg.buttons) and msg.buttons[self.btn_up]:
                y_val = 1
            elif self.btn_down < len(msg.buttons) and msg.buttons[self.btn_down]:
                y_val = -1
            
            if INVERT_X:
                x_val = -x_val
            if INVERT_Y:
                y_val = -y_val
        
        return x_val, y_val

    def joy_callback(self, msg: Joy):
        if not self.detected:
            if not self.detect_layout(msg):
                return
            self.detected = True

        x_val, y_val = self.get_dpad_values(msg)

        cmd_str = f"SV;A;{x_val};{y_val}!"

        if cmd_str != self.last_cmd:
            msg_out = String()
            msg_out.data = cmd_str
            self.cmd_pub.publish(msg_out)
            self.get_logger().info(f"Published: {cmd_str}")
            self.last_cmd = cmd_str


def main(args=None):
    rclpy.init(args=args)
    node = JoyServoTest()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
