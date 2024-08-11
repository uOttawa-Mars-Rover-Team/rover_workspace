#!/usr/bin/python3
from typing import NamedTuple, TypeVar

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pynput import keyboard
from std_msgs.msg import Float32

T = TypeVar("T")

class KeyboardListener(Node):
    def __init__(self):
        super().__init__('keyboard_listener')

        self.joy_vel_pub = self.create_publisher(Float32, '/keyboard/arm_vel', 10)
        self.cmd_pub = self.create_publisher(String, '/arm_cmd', 10) # for M
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        # Commands being sent to the arduino
        self.vel = Float32()
        self.vel.data = 1.0
        self.arm_cmd = String()

    def on_press(self, key):
        # This is for special keys that don't have the char attribute
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key) #if there is no char attribute it's a special key that can just be converte to a string 

        # Filter out unwanted keys
        if key_str in ['Key.alt', 'Key.ctrl', 'Key.shift', 'Key.backspace']:
            return

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
            self.arm_cmd.data = "stepper1;!"
            self.get_logger().info('Stepper 1 toggle')
            self.cmd_pub.publish(self.arm_cmd)

        if key_str == 'x':#stepper2
            self.arm_cmd.data = "stepper2;!"
            self.get_logger().info('Stepper 2 toggle')
            self.cmd_pub.publish(self.arm_cmd)

        if key_str == 'c':#stepper3 
            self.arm_cmd.data = "stepper3;!"
            self.get_logger().info('Stepper 3 toggle')
            self.cmd_pub.publish(self.arm_cmd)

        if key_str == 'v':#stepper4
            self.arm_cmd.data = "stepper4;!"
            self.get_logger().info('Stepper 4 toggle')
            self.cmd_pub.publish(self.arm_cmd)

        #Handling laser
        if key_str == '4':#laser
            self.arm_cmd.data = "laser;!"
            self.get_logger().info('Laser toggle')
            self.cmd_pub.publish(self.arm_cmd)

        #Handling laser
        if key_str == '3':#disable arduino stepper protection from unsafe angles
            self.arm_cmd.data = "stepper_safety;!"
            self.get_logger().info('Stepper safety toggle')
            self.cmd_pub.publish(self.arm_cmd)

        #Handling emergency stop button
        if key_str == '1':
            self.arm_cmd.data = "stop;!"
            self.get_logger().info('Emergency stop')
            self.cmd_pub.publish(self.arm_cmd)

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
