#!/usr/bin/python3

import signal
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple, TypeVar

import rclpy
import serial
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy

T = TypeVar("T")


class AxesValues(NamedTuple):
    """
    Define properties for each of the 6 axes on the joystick. Use default
    property names for unused vales.
    """

    axes_0: float
    actuator: float
    tower: float
    speed_axis: float
    wrist_roll: float
    wrist_pitch: float


class ButtonValues(NamedTuple):
    """
    Define properties for each of the 12 buttons on the joystick. Use default
    property names for unused vales.
    """

    ee_close_btn: int
    ee_open_btn: int
    second_speed_btn: int
    third_speed_btn: int
    lowest_speed_btn: int
    norm_speed_btn: int
    force_stop_btn: int
    btn_7: int
    btn_8: int
    btn_9: int
    btn_10: int
    actuator_hold_btn: int


class MArmControllerNode(Node):
    """
    Initializes a node used to receive Joy messages from the joystick and send
    messages associated with these control commands to the robotic arm Arduino,
    allowing for manual control of the robotic arm.
    """

    # Define constants
    ROUND_PRECISION = 3
    SPEED_DEADBAND = 0.05
    MOTOR_CAP = 1000

    def __init__(self, node_name: str = "m_arm_controller"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        # Stores message to serial
        self.movement = ""
        # Record previous cmds so as to not repeat them
        self.partsInMotion = ["stop;!"]

        self.deadband = self.get_param("deadband", rclpy.Parameter.Type.DOUBLE, 0.35)

        self.speed = 1.0
        self.multiplier = 1.0
        self.actuator_cap = self.get_param(
            "actuator_cap", rclpy.Parameter.Type.INTEGER, 600
        )

        # Joy subscriber
        self.joy_subscriber = self.create_subscription(
            Joy, "arm_joy", self.joy_control_callback, 20
        )
        self.get_logger().info(
            f"Subscribing to messages from: {self.joy_subscriber.topic_name}"
        )

        self.startup = True  # if true, next connection will send the stop cmd at a delay of 1s, else 0.001s
        self.connecting = True  # boolean for connection status
        self.RETRY_DELAY = self.get_param(
            "timeout_delay", rclpy.Parameter.Type.DOUBLE, 0.1
        )  # time (s) to attempt serial connection

        # Using signal lib for timeout mechanism
        signal.signal(
            signal.SIGALRM, self.connect_serial
        )  # when SIGALRM triggers, run self.connect_serial
        signal.setitimer(
            signal.ITIMER_REAL, self.RETRY_DELAY, 0
        )  # manually SIGALRM to start serial connection

        signal.signal(signal.SIGINT, self.graceful_shutdown)
        self.run = True  # threads will stop running if false
        self.tp_executor = ThreadPoolExecutor(max_workers=2)
        self.reader = self.tp_executor.submit(self.read_loop)

        self.serial_device = self.get_param("serial_dev", rclpy.Parameter.Type.STRING)
        self.baudrate = self.get_param("baudrate", rclpy.Parameter.Type.INTEGER, 115200)

    def connect_serial(self, signal_num, frame) -> None:
        """
        Connects to serial; used on startup, timeouts or can be manually done
        """
        try:
            self.connecting = True
            self.get_logger().info("Establishing serial connection...")
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
            self.ARDUINO = serial.Serial(
                port=self.serial_device,
                baudrate=self.baudrate,
                timeout=self.RETRY_DELAY,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )
            signal.setitimer(signal.ITIMER_REAL, 0, 0)
            self.get_logger().info("Connection to serial established")
            if not self.startup:
                timer = threading.Timer(0.001, self.force_stop)
            else:
                timer = threading.Timer(1, self.force_stop)
                self.startup = False
            timer.start()
        except:
            self.get_logger().warn(
                f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s"
            )
            self.connecting = True
            self.connect_serial

    def force_stop(self):
        """
        Emergency stop
        """
        try:
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
            self.ARDUINO.write(bytes("stop;!",'utf-8'))
            signal.setitimer(signal.ITIMER_REAL, 0, 0)

            self.get_logger().info("Movement msg to serial: stop;!")
            self.connecting = False
        except:
            self.get_logger().warn(
                f"Connection Error: serial failed, trying every {self.RETRY_DELAY}s"
            )
            self.connecting = True
            self.connect_serial

    def graceful_shutdown(self, sig, frame) -> None:
        """
        Tell threads to shutdown
        """
        self.get_logger().info("Terminating all threads...")
        self.run = False
        self.tp_executor.shutdown()
        self.get_logger().info("Shutting node down...")
        raise SystemExit

    def read_loop(self):
        """
        Reader thread loop running read_serial as long as self.run
        """
        while self.run:
            if not self.connecting and self.ARDUINO.in_waiting:
                byte_chunk = self.ARDUINO.read_until(b'!')
                self.get_logger().info(byte_chunk[:-1])
        os.kill(os.getpid(), 9)

    def write_serial(self):
        """
        Executes derived movement from the Joy (usually "/joy") topic
        """
        if not self.connecting:
            try:
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
                self.ARDUINO.write(bytes(self.movement,'utf-8'))
                self.get_logger().info(f"Movement msg to serial: {self.movement}")
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
            except:
                signal.setitimer(signal.ITIMER_REAL, 0, 0)
                self.get_logger().warn("Connection Error: could not write serial")
                signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)
        else:
            signal.setitimer(signal.ITIMER_REAL, self.RETRY_DELAY, 0)

    def joy_control_callback(self, message: Joy) -> None:
        """
        Main loop for Joy msg processing
        """
        axes_values = AxesValues(*message.axes)
        btn_values = ButtonValues(*message.buttons)

        if btn_values.force_stop_btn and btn_values.actuator_hold_btn:
            self.startup = True
            self.get_logger().info("Forcing serial reconnection")
            signal.setitimer(signal.ITIMER_REAL, 0.001, 0)
            time.sleep(1)
        elif not self.connecting:
            # Map: [-1.0, 1.0] -> [0.0, 2.0]
            if axes_values.speed_axis < 0:
                self.speed = 1 - round(
                    abs(axes_values.speed_axis), self.ROUND_PRECISION
                )
            else:
                self.speed = 1 + round(axes_values.speed_axis, self.ROUND_PRECISION)
            self.speed /= 2

            # Speed toggles, 50%, 100%, 150% & 200%
            if btn_values.lowest_speed_btn and self.multiplier != 0.25:
                self.multiplier = 0.25
                self.get_logger().info("Speed multiplier changed to 25%")
            elif btn_values.second_speed_btn and self.multiplier != 0.5:
                self.multiplier = 0.5
                self.get_logger().info("Speed multiplier changed to 50%")
            elif btn_values.third_speed_btn and self.multiplier != 0.75:
                self.multiplier = 0.75
                self.get_logger().info("Speed multiplier changed to 75%")
            elif btn_values.norm_speed_btn and self.multiplier != 1.0:
                self.multiplier = 1.0
                self.get_logger().info("Speed multiplier changed to 100%")

            # Checking all axes are stationary (less than deadband)
            axes_stationary = True
            for name, value in axes_values._asdict().items():
                axes_values.speed_axis
                # Ignore speed axis
                if name != "speed_axis" and abs(value) > self.deadband:
                    axes_stationary = False
                    break

            # Checking no buttons currently pressed
            buttons_unpressed = True
            if axes_stationary:
                for value in btn_values:
                    if value:
                        buttons_unpressed = False
                        break

            # If both axes & buttons are untouched or if speed dial's low, send the stop cmd
            # Or ignore all conditions and send stop if the force stop button is pressed
            stop_condition = (axes_stationary and buttons_unpressed) or (
                self.speed <= self.SPEED_DEADBAND
            )
            if ((self.partsInMotion[-1] != "stop;!") & stop_condition) or (
                axes_stationary and btn_values.force_stop_btn
            ):
                self.partsInMotion = ["stop;!"]
                self.movement = "stop;!"
                self.write_serial()

            # At least an axis or button pressed while speed > speed threshold
            elif self.speed > self.SPEED_DEADBAND:
                self.speed *= self.multiplier
                tmp_speed = int(self.actuator_cap * self.speed)

                # Arm & forearm
                tmp_axis = axes_values.actuator
                if abs(tmp_axis) > self.deadband:
                    if btn_values.actuator_hold_btn:
                        self.movement = "L1;"
                    else:
                        self.movement = "L2;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        if (
                            tmp_speed < 105
                        ):  # no movement, but current observed; waste of power
                            self.movement += str(105) + ";!"
                        else:
                            self.movement += str(int(tmp_speed)) + ";!"
                        self.write_serial()

                self.speed *= self.MOTOR_CAP  # All below parts have motor cap
                tmp_speed = (
                    int(self.speed) >> 0
                )  # WR has ~1/2 speed mult.; equiv to >> 1

                # Wrist Roll
                tmp_axis = axes_values.wrist_roll
                if abs(tmp_axis) > self.deadband:
                    self.movement = "L1;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "1;"
                        else:
                            self.movement += "-1;"
                        self.movement += "600;!"
                        self.write_serial()

                # WP & EE have ~1/4 speed multiplier; equiv to >> 2
                tmp_speed >>= 0
                tmp_str = "600;!"

                # Wrist Pitch
                tmp_axis = axes_values.wrist_pitch
                if abs(tmp_axis) > self.deadband:
                    self.movement = "L2;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "1;"
                        else:
                            self.movement += "-1;"
                        self.movement += tmp_str
                        self.write_serial()

                # End effector
                if btn_values.ee_open_btn ^ btn_values.ee_close_btn:
                    self.movement = "EE;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if btn_values.ee_open_btn:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        self.movement += tmp_str
                        self.write_serial()

                # Tower
                tmp_axis = axes_values.tower
                if abs(tmp_axis) > self.deadband:
                    self.movement = "TW;"
                    if self.movement not in self.partsInMotion:
                        self.partsInMotion.append(self.movement)
                        if tmp_axis < 0:
                            self.movement += "-1;"
                        else:
                            self.movement += "1;"
                        self.movement += str(int(tmp_speed >> 1)) + ";!"
                        self.write_serial()

    def get_param(
        self,
        param_name: str,
        param_type: rclpy.Parameter.Type,
        default_val: T | None = None,
        logging: bool = True,
    ) -> T:
        """
        Helper function to declare and get the value of a ROS launch parameter,
        including support for default values.
        """

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


def main(args=None):
    rclpy.init(args=args)
    m_arm_controller_node = MArmControllerNode()
    rclpy.spin(m_arm_controller_node)
    rclpy.shutdown()


if __name__ == "__main__":
    main()
