#!/usr/bin/python3
from typing import NamedTuple, TypeVar

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

        self.mode = self.get_param("mode", rclpy.Parameter.Type.STRING, "I") # ik or manual mode, default I for ik
        
        self.joy_vel_pub = self.create_publisher(Float32, '/keyboard/arm_vel', 10)
        self.gpio_pub = self.create_publisher(ArmGpio, '/peripheral_controller/peripheral_enables', 10) # for IK
        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 10) # for M
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.vel = Float32()
        self.vel.data = 1.0

        self.gpio_cmd = ArmGpio()
        self.arm_cmd = String()

        # Service client setup
        self.client = self.create_client(Trigger, 'servo_node/start_servo')


    def on_press(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)

        # Filter out unwanted keys
        if key_str in ['Key.alt', 'Key.ctrl', 'Key.shift', 'Key.backspace']:
            return

        #self.get_logger().info(f'Key pressed: {key_str}')

        # Call service when 's' key is pressed
        if key_str == 's':
            if self.client.wait_for_service(timeout_sec=1.0):
                self.send_request()
            else:
                self.get_logger().info('Service not available.')
                
        # Handling velocity from dial
        if key_str == 'm':#vel +0.1 up to 1.0 max
            if (self.vel.data < 1.0):
                self.vel.data += 0.1
                self.vel.data = round(self.vel.data, 1)
                self.joy_vel_pub.publish(self.vel)
                self.get_logger().info('Max vel: '+str(self.vel.data))
        if key_str == 'b':#vel -0.1 up to 0.1 min
            if (self.vel.data > 0.1):
                self.vel.data -= 0.1
                self.vel.data = round(self.vel.data, 1)
                self.joy_vel_pub.publish(self.vel)
                self.get_logger().info('Max vel: '+str(self.vel.data))

        # Handling stepper toggling
        if key_str == 'z':#stepper1 en
            self.gpio_cmd.stepper1_en = not self.gpio_cmd.stepper1_en
            self.get_logger().info('TW toggled: '+str(self.gpio_cmd.stepper1_en))
            if self.mode == 'M':
                self.arm_cmd.data = "stepper1;!"
                self.cmd_pub.publish(self.arm_cmd)
            else:
                self.gpio_pub.publish(self.gpio_cmd)
        if key_str == 'x':#stepper2
            self.gpio_cmd.stepper2_en = not self.gpio_cmd.stepper2_en
            self.get_logger().info('WP toggled: '+str(self.gpio_cmd.stepper2_en))
            if self.mode == 'M':
                self.arm_cmd.data = "stepper2;!"
                self.cmd_pub.publish(self.arm_cmd)
            else:
                self.gpio_pub.publish(self.gpio_cmd)
        if key_str == 'c':#stepper3 
            self.gpio_cmd.stepper3_en = not self.gpio_cmd.stepper3_en
            self.get_logger().info('WR toggled: '+str(self.gpio_cmd.stepper3_en))
            if self.mode == 'M':
                self.arm_cmd.data = "stepper3;!"
                self.cmd_pub.publish(self.arm_cmd)
            else:
                self.gpio_pub.publish(self.gpio_cmd)
        if key_str == 'v':#stepper4
            self.gpio_cmd.stepper4_en = not self.gpio_cmd.stepper4_en
            self.get_logger().info('EE toggled: '+str(self.gpio_cmd.stepper4_en))
            if self.mode == 'M':
                self.arm_cmd.data = "stepper4;!"
                self.cmd_pub.publish(self.arm_cmd)
            else:
                self.gpio_pub.publish(self.gpio_cmd)

        #Handling laser
        if key_str == '4':#laserr
            self.gpio_cmd.laser_en = not self.gpio_cmd.laser_en
            self.get_logger().info('Laser toggled: '+str(self.gpio_cmd.laser_en))
            if self.mode == 'M':
                self.cmd_pub.publish("laser;!")
            else:
                self.gpio_pub.publish(self.gpio_cmd)

        #Handling emergency stop button
        if key_str == '1':
            self.gpio_cmd.emergency_stop_en = not self.gpio_cmd.emergency_stop_en
            self.get_logger().info('Stop toggled: '+str(self.gpio_cmd.emergency_stop_en))
            if self.mode == 'M':
                self.cmd_pub.publish("stop;!")
            else:
                self.gpio_pub.publish(self.gpio_cmd)

    def send_request(self):
            request = Trigger.Request()
            self.future = self.client.call_async(request)
            self.future.add_done_callback(self.callback)
    
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
