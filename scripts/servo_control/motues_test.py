import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math

class MoteusEmulator(Node):
    def __init__(self):
        # Name the ROS 2 node
        super().__init__('moteus_emulator_node')
        
        # Create a publisher on the topic '/moteus_cmd_echo'
        self.publisher_ = self.create_publisher(JointState, '/moteus_cmd_echo', 10)
        
        # Create a timer to trigger the callback at 100Hz (0.01 seconds)
        self.timer = self.create_timer(0.01, self.timer_callback)
        self.get_logger().info("ROS 2 Moteus Emulator started. Publishing to /moteus_cmd_echo")

    def timer_callback(self):
        # Construct the standard ROS 2 JointState message
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = ['neo_drive_wheel_1']
        
        # Populate the target commands (matching your tuned values)
        msg.position = [math.nan]
        msg.velocity = [10.0]
        msg.effort = [0.1]  # Effort maps to your maximum_torque limit

        # Broadcast the message to the ROS 2 graph
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MoteusEmulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()