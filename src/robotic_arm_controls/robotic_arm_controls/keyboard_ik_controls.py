import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from pynput import keyboard
from std_msgs.msg import Float32
from general_interfaces.msg import ArmGpio


class KeyboardListener(Node):
    def __init__(self):
        super().__init__('keyboard_listener')
        self.joy_vel_pub = self.create_publisher(Float32, '/joy_vel', 10)
        self.gpio_pub = self.create_publisher(ArmGpio, '/peripheral_controller/peripheral_enables', 10)
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

        self.vel = Float32()
        self.vel.data = 1.0

        self.gpio_cmd = ArmGpio()

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

        #self.get_logger().info(f'Key pressed: {key_str}')


        # Handling stepper toggling
        if key_str == 'z':#stepper1 en
            self.get_logger().info('TW toggled')
            if self.gpio_cmd.stepper1_en:
                self.gpio_cmd.stepper1_en = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.stepper1_en = True
                self.gpio_pub.publish(self.gpio_cmd)
        if key_str == 'x':#stepper2
            self.get_logger().info('WP toggled')
            if self.gpio_cmd.stepper2_en:
                self.gpio_cmd.stepper2_en = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.stepper2_en = True
                self.gpio_pub.publish(self.gpio_cmd)
        if key_str == 'c':#stepper3 
            self.get_logger().info('WR toggled')
            if self.gpio_cmd.stepper3_en:
                self.gpio_cmd.stepper3_en = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.stepper3_en = True
                self.gpio_pub.publish(self.gpio_cmd)
            self.joy_vel_pub.publish(self.vel)
        if key_str == 'v':#stepper4
            self.get_logger().info('EE toggled')
            if self.gpio_cmd.stepper4_en:
                self.gpio_cmd.stepper4_en = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.stepper4_en = True
                self.gpio_pub.publish(self.gpio_cmd)
                
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

        #Handling laser
        if key_str == 'f':#stepper4
            self.get_logger().info('Laser toggled')
            if self.gpio_cmd.laser_en:
                self.gpio_cmd.laser_en = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.laser_en = True
                self.gpio_pub.publish(self.gpio_cmd)

        #Handling emergency stop button
        if key_str == '1':#stepper4
            self.get_logger().info('Stop toggled')
            if self.gpio_cmd.stop:
                self.gpio_cmd.stop = False
                self.gpio_pub.publish(self.gpio_cmd)
            else:
                self.gpio_cmd.stop = True
                self.gpio_pub.publish(self.gpio_cmd)

def main(args=None):
    rclpy.init(args=args)
    node = KeyboardListener()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
