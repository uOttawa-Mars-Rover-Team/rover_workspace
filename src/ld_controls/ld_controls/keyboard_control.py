import rclpy
from pynput import keyboard
from pynput.keyboard import Key
from rclpy.node import Node
from std_msgs.msg import Empty, UInt8


class KeyboardControlNode(Node):
    """
    Initializes a node, which then initializes multiple publishers and starts
    listening for key presses. When certain keys are pressed, data is published
    to a specified topic.
    """

    def __init__(self, node_name: str = "life_detection_control"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Setup publishers
        # VacHose
        self.vac_hose_pub = self.create_publisher(UInt8, "vac_hose_cmd", 100)
        self.get_logger().info(
            f"Publishing messages at: {self.vac_hose_pub.topic_name}"
        )
        # FunnelFlap
        self.funnel_flap_pub = self.create_publisher(Empty, "funnel_flap_cmd", 100)
        self.get_logger().info(
            f"Publishing messages at: {self.funnel_flap_pub.topic_name}"
        )
        # VacMotor
        self.vac_motor_pub = self.create_publisher(UInt8, "vac_motor_cmd", 100)
        self.get_logger().info(
            f"Publishing messages at: {self.vac_motor_pub.topic_name}"
        )
        # Beaker
        self.beaker_pub = self.create_publisher(UInt8, "beaker_cmd", 100)
        self.get_logger().info(f"Publishing messages at: {self.beaker_pub.topic_name}")
        # Agitate
        self.agitate_pub = self.create_publisher(UInt8, "agitate_cmd", 100)
        self.get_logger().info(f"Publishing messages at: {self.agitate_pub.topic_name}")
        # WeatherCollection
        self.weather_collection_pub = self.create_publisher(
            Empty, "weather_collection_cmd", 100
        )
        self.get_logger().info(
            f"Publishing messages at: {self.weather_collection_pub.topic_name}"
        )

        # Keep track of whether any key is being pressed
        self.key_pressed = False

        self.get_logger().info(f"Listening for key presses...")
        # Setup a keyboard listener
        with keyboard.Listener(
            on_release=self.on_key_release, on_press=self.on_key_press
        ) as listener:
            # Block any calling threads until this thread terminates
            listener.join()

    def on_key_release(self, key) -> None:
        """
        Callback to deal with key releases on the keyboard.
        """

        # Keys with characters (letters, numbers, brackets, etc.) on them will
        # have the "char" attribute. Functional keys, such as backspace, tab,
        # etc. will not.
        if hasattr(key, "char"):
            # Replace the value of key, since only 1 key is passed into
            # this function when called
            key = key.char

        # A map of key to publishers and data they should publish when each
        # key is pressed
        key_publisher_map = {
            Key.up: (self.vac_hose_pub, UInt8(data=3)),
            Key.down: (self.vac_hose_pub, UInt8(data=4)),
            "a": (self.agitate_pub, UInt8(data=0)),
        }

        if key in key_publisher_map:
            # Publish the specified data (from key_publisher_map) and log a message
            publisher, data = key_publisher_map[key]

            self.get_logger().info(f"Key RELEASE detected: {key}")
            self.get_logger().info(
                f"Publishing data ({data}) at topic: {publisher.topic_name}"
            )
            publisher.publish(data)

        self.key_pressed = False

    def on_key_press(self, key) -> None:
        """
        Callback to deal with key presses on the keyboard.
        """

        if self.key_pressed == False:
            # Keys with characters (letters, numbers, brackets, etc.) on them will
            # have the "char" attribute. Functional keys, such as backspace, tab,
            # etc. will not.
            if hasattr(key, "char"):
                # Replace the value of key, since only 1 key is passed into
                # this function when called
                key = key.char

            # A map of key to publishers and data they should publish when each
            # key is pressed
            key_publisher_map = {
                Key.up: (self.vac_hose_pub, UInt8(data=2)),
                Key.down: (self.vac_hose_pub, UInt8(data=1)),
                Key.right: (self.beaker_pub, UInt8(data=1)),
                Key.left: (self.beaker_pub, UInt8(data=2)),
                "f": (self.funnel_flap_pub, Empty()),
                "v": (self.vac_motor_pub, UInt8(data=1)),
                "r": (self.vac_motor_pub, UInt8(data=2)),
                "a": (self.agitate_pub, UInt8(data=1)),
                "w": (self.weather_collection_pub, Empty()),
            }

            if key == "x":
                # Exit the entire program
                self.get_logger().info(
                    'Key "x" was pressed. Exiting the entire program...'
                )
                exit()

            if key in key_publisher_map:
                # Publish the specified data (from key_publisher_map) and log a message
                publisher, data = key_publisher_map[key]

                self.get_logger().info(f"Key PRESS detected: {key}")
                self.get_logger().info(
                    f"Publishing data ({data}) at topic: {publisher.topic_name}"
                )
                publisher.publish(data)

            self.key_pressed = True


def main(args=None):
    rclpy.init(args=args)
    keyboard_control_node = KeyboardControlNode()
    rclpy.spin(keyboard_control_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
