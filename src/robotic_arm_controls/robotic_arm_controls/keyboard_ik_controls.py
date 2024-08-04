import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pynput import keyboard

class KeyboardListener(Node):
    def __init__(self):
        super().__init__('keyboard_listener')
        self.publisher_ = self.create_publisher(String, 'key_presses', 10)
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            key_str = key.char
        except AttributeError:
            key_str = str(key)

        # Filter out unwanted keys
        if key_str in ['Key.alt', 'Key.ctrl', 'Key.shift', 'Key.backspace']:
            return

        msg = String()
        msg.data = key_str
        self.publisher_.publish(msg)
        self.get_logger().info(f'Key pressed: {key_str}')

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
