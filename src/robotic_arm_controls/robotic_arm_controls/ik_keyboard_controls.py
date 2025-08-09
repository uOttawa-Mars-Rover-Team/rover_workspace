#!/usr/bin/python3
from typing import NamedTuple, TypeVar
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from std_msgs.msg import String
from pynput import keyboard
from std_msgs.msg import Float32
from general_interfaces.msg import ArmGpio
from std_srvs.srv import Trigger

T = TypeVar("T")

class KeyboardListener(Node):
    def __init__(self):
        super().__init__('keyboard_listener')

        self.mode = self.get_param("mode", rclpy.Parameter.Type.STRING, "I")  # Get operational mode parameter: 'I' for IK mode or 'M' for manual
        
         # ROS2 publishers
        self.joy_vel_pub = self.create_publisher(Float32, '/keyboard/arm_vel', 10)
        self.gpio_pub = self.create_publisher(ArmGpio, '/peripheral_controller/peripheral_enables', 10) # for IK
        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 10) # for M

        # Start listening to keyboard input
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        # Initialize messages
        self.vel = Float32()
        self.vel.data = 1.0
        self.gpio_cmd = ArmGpio()
        self.arm_cmd = String()

        # ROS2 service client
        self.client = self.create_client(Trigger, 'servo_node/start_servo')

        # This delay ensures that the joy node has been instantiated before this message has been published
        # which solves the problem of the joy node and keyboard initial velocity being different
        time.sleep(1) 
        self.joy_vel_pub.publish(self.vel)


    """
    Handles key press events and maps keys to corresponding actions
    """
    def on_press(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)

        # Filter out unwanted keys
        if key_str in ['Key.alt', 'Key.ctrl', 'Key.shift', 'Key.backspace']:
            return

        # Key-to-action mapping
        key_actions = {
            's': self.send_request,                                                         # Call service
            '.': lambda: self.adjust_velocity(0.1),                                         # Increment velocity by 1
            ',': lambda: self.adjust_velocity(-0.1),                                        # Decrement velocity by 1
            'z': lambda: self.toggle_gpio('stepper1_en', 'TW', 'stepper1'),                 # Toggle stepper motors
            'x': lambda: self.toggle_gpio('stepper2_en', 'WP', 'stepper2'),
            'n': lambda: self.toggle_gpio('stepper3_en', 'WR', 'stepper3'),     
            'm': lambda: self.toggle_gpio('stepper4_en', 'EE', 'stepper4'),     
            'v': self.toggle_verbose,                                             # Toggle verbose mode
            '4': lambda: self.toggle_gpio('laser_en', 'Laser', 'laser'),                    # Toggle laser
            '1': lambda: self.toggle_gpio('emergency_stop_en', 'Stop', 'stop'),             # Toggle emergency stop
            'o': lambda: self.send_camera_servo_cmd('svu', 'Shoulder camera servo: up'),    # Move servo up
            'l': lambda: self.send_camera_servo_cmd('svd', 'Shoulder camera servo: down'),  # Move servo down
        }

        action = key_actions.get(key_str)
        if action:
            action()


    """
    Stops the servo when keys 'o' or 'l' are released
    """
    def on_release(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)

        if key_str in ['o', 'l']:
            self.send_arm_cmd("svs", "Stop shoulder camera servo")
    

    """
    Toggles a GPIO field and publishes either command or GPIO message depending on mode
    """
    def toggle_gpio(self, attr: str, label: str, cmd_str: str):
        current = getattr(self.gpio_cmd, attr)     # Retrieve current value of the specified GPIO attribute
        setattr(self.gpio_cmd, attr, not current)   # Set the attribute to its opposite (toggle it)

        self.get_logger().info(f'{label} toggled: {not current}')
        if self.mode == 'M':
            self.arm_cmd.data = f"{cmd_str};!"
            self.cmd_pub.publish(self.arm_cmd)
        else:
            self.gpio_pub.publish(self.gpio_cmd)


    """
    Toggles verbose mode 
    """
    def toggle_verbose(self):
        self.get_logger().info('Verbose toggled')
        if self.mode == 'M':
            msg = String()
            msg.data = "v;!"
            self.cmd_pub.publish(msg)


    """
    Attempts to call a ROS2 service, logging if it's unavailable
    Sends a request to the ROS2 Trigger service
    """
    def send_request(self):
        if self.client.wait_for_service(timeout_sec=1.0):
            request = Trigger.Request()
            self.future = self.client.call_async(request)
            self.future.add_done_callback(self.callback)
        else:
            self.get_logger().info('Service not available.')


    """
    Adjusts the velocity within [0.1, 1.0] range and publishes it
    """
    def adjust_velocity(self, delta):
        new_vel = round(self.vel.data + delta, 1)
        if 0.1 <= new_vel <= 1.0:
            self.vel.data = new_vel
            self.joy_vel_pub.publish(self.vel)
            self.get_logger().info(f'Max vel: {str(self.vel.data)}')


    """
    Sends a command to control shoulder camera servo mount
    """
    def send_camera_servo_cmd(self, data: str, label: str):
        self.arm_cmd.data = data
        self.get_logger().info(label)
        self.cmd_pub.publish(self.arm_cmd)


    def callback(self, future):
        try:
            response = future.result()
            self.get_logger().info(f'Success: {response.success}, Message: {response.message}')
        except Exception as e:
            self.get_logger().error(f'Service call failed: {e}')


    """
    Helper function to declare and get the value of a ROS launch parameter,
    including support for default values.
    """
    def get_param(
        self,
        param_name: str,
        param_type: rclpy.Parameter.Type,
        default_val: T | None = None,
        logging: bool = True,
    ) -> T:

        # Must declare existence of parameter before retrieving it
        self.declare_parameter(param_name, param_type)

        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = Parameter(param_name, param_type, default_val)
            # Returns parameter if it exists, else returns default_param
            param_val = self.get_parameter_or(param_name, default_param).value

        assert param_val is not None, "The parameter received was None."

        if logging:
            self.get_logger().info(f"Using {param_name}: {param_val}")

        return param_val
    

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
