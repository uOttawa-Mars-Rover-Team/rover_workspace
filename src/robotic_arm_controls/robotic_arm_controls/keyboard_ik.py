#!/usr/bin/python3

import os
import signal
from pynput import keyboard
import rclpy
from rclpy.parameter import Parameter
import std_msgs.msg

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
T = TypeVar("T")

"""
Node that interfaces between spacemouse joy node (receive spacemouse arrays) 
and the servo node (sends TwistStamped msgs)
"""
class KeystrokeListener(Node):

    def __init__(self, node_name: str = "controller"):
        super().__init__(node_name)

        # Pubs and subs
        self.pub_glyph = self.node.create_publisher(std_msgs.msg.String, 'glyphkey_pressed', 10)

        # Info
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")
        self.get_logger().info(f"Logging keystrokes")
        self.get_logger().info(f"Publishing messages to: {self.pub_glyph.topic_name}")

        self.prev = [] #prev array of joy values (float array)
        self.curr = []

        # Params

    def spin(self):
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            while rclpy.ok() and listener.running:
                rclpy.spin_once(self.node, timeout_sec=0.1)

    def on_release(self, key):
        pass
    
    def on_press(self, key):
        try:
            char = getattr(key, 'char', None)
            if isinstance(char, str):
                self.node.get_logger().info('pressed ' + char)
                self.pub_glyph.publish(self.pub_glyph.msg_type(data=char))
            else:
                try:
                    # Known keys like spacebar, ctrl
                    name = key.name
                    vk = key.value.vk
                except AttributeError:
                    # Unknown keys like headphones skip song button
                    name = 'UNKNOWN'
                    vk = key.vk
                self.node.get_logger().info('pressed {} ({})'.format(name, vk))
                # Note: These values are not cross-platform. When ROS 2 supports Enums, use them instead
                self.pub_code.publish(self.pub_code.msg_type(data=vk))
        except Exception as e:
            self.node.get_logger().error(str(e))
            raise

        if key == keyboard.Key.esc:
            self.node.get_logger().info('stopping listener')
            raise keyboard.Listener.StopException
            os.kill(os.getpid(), signal.SIGINT)


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

"""
Most of the code below should remain unchanged except maybe the node names
""" 
def main(args=None):
    rclpy.init(args=args)           # if any args specified on node startup (via ros2 run <package> <node> args...)
    KeystrokeListener().spin()
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise

if __name__ == "__main__":
    main()
