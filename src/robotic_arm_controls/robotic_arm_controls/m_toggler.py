#!/usr/bin/python3                 

from typing import NamedTuple, TypeVar # For parameter helper function

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy
from std_msgs.msg import String
from general_interfaces.msg import ToggleMessage

"""
Ignore this; this is for parameter helper function when we launch the
node via a launch file and not running it directly; 'ros2 launch' instead of 'ros2 run'
"""
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
    laser_btn: int
    btn_3: int
    btn_4: int
    btn_5: int
    stepper1_btn: int 
    stepper2_btn: int 
    stepper3_btn: int 
    stepper4_btn: int 
    stop_btn: int 
    actuator_hold_btn: int 

class Toggler(Node):
    MANUAL_MODE = "m"
    IK_MODE = "ik"
    
    def __init__(self, node_name: str = "toggler"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        #Subscribers
        self.subscriber = self.create_subscription(Joy, "/joy/arm_cmd", self.joy_callback, 20)

        #Publishers
        self.ik_publisher = self.create_publisher(ToggleMessage, '/ik_joy', 20)
        self.m_publisher = self.create_publisher(ToggleMessage, '/m_joy', 20)
        self.mode_publisher = self.create_publisher(String, '/mode', 20)
        self.mode_publisher = self.create_publisher(String, '/mode', 20)
        self.enable_pub = self.create_publisher(String, '/enable_cmd', 20)

        # The node's logger, may just use print() instead
        self.get_logger().info(f"Subscribing to messages from: {self.subscriber.topic_name}")

        self.toggle_mode = Toggler.MANUAL_MODE
        
        self.prevMessageSent = self.setAllMessageValues(ToggleMessage(), 3)
        self.prevBtnValues = ButtonValues(3,3,3,3,3,3,3,3,3,3,3,3)

        self.stepper1_en = True
        self.stepper2_en = True
        self.stepper3_en = True
        self.stepper4_en = True
        self.laser_en = False
        self.emergency_stop_en = False
        

    # Callbacks
    '''
    Callback for the joystick subscriber. This method is called whenever a message is received from the joystick
    '''
    def joy_callback(self, message: Joy):

        #switched = False

        axes_values = AxesValues(*message.axes)
        btn_values = ButtonValues(*message.buttons)

        #prints axes values of arm
        printAxes = f"\naxes_values: {axes_values}\n"
        toPrint = ""

        newMessage = self.createMessage(axes_values, btn_values)

        if (self.isChanged(newMessage, btn_values)):

            enable_msg = String()

            # Handling stepper toggling
            if btn_values.stepper1_btn:#stepper1 en
                self.stepper1_en = not self.stepper1_en
                self.get_logger().info('TW toggled: '+str(self.stepper1_en))
                enable_msg.data = "stepper1;!"
                self.enable_pub.publish(enable_msg)
            if btn_values.stepper2_btn:#stepper2
                self.stepper2_en = not self.stepper2_en
                self.get_logger().info('WP toggled: '+str(self.stepper2_en))
                enable_msg.data = "stepper2;!"
                self.enable_pub.publish(enable_msg)
            if btn_values.stepper3_btn:#stepper3 
                self.stepper3_en = not self.stepper3_en
                self.get_logger().info('WR toggled: '+str(self.stepper3_en))
                enable_msg.data = "stepper3;!"
                self.enable_pub.publish(enable_msg)
            if btn_values.stepper4_btn:#stepper4
                self.stepper4_en = not self.stepper4_en
                self.get_logger().info('EE toggled: '+str(self.stepper4_en))
                enable_msg.data = "stepper4;!"
                self.enable_pub.publish(enable_msg)

            #Handling laser
            if btn_values.laser_btn:#laserr
                self.laser_en = not self.laser_en
                self.get_logger().info('Laser toggled: '+str(self.laser_en))
                enable_msg.data = "laser;!"
                self.enable_pub.publish(enable_msg)

            #Handling emergency stop button
            if btn_values.stop_btn:
                self.emergency_stop_en = not self.emergency_stop_en
                self.get_logger().info('Stop toggled: '+str(self.emergency_stop_en))
                enable_msg.data = "stop;!"
                self.enable_pub.publish(enable_msg)

            if (self.canPublish(btn_values)):
                toPrint += f"\nMessage: {newMessage.tw, newMessage.la1, newMessage.la2, newMessage.wr_pitch, newMessage.wr_roll, newMessage.ee, newMessage.speed}"

                if self.toggle_mode == Toggler.MANUAL_MODE:
                    toPrint += "\nPublishing to Manual"
                    self.m_publisher.publish(newMessage)

                elif self.toggle_mode == Toggler.IK_MODE:
                    toPrint += "\nPublishing to IK"
                    self.ik_publisher.publish(newMessage)
            
            #self.get_logger().info(printAxes)

        self.prevMessageSent = newMessage
        self.prevBtnValues = btn_values

    
    #Helper Methods
    """
    This method checks if either message or button values have changed to determine if Toggler Node can switch to another mode/publish
    """
    def isChanged(self, newMessage, btn_values):
        buttonsToIgnore = [3,4,5]
        
        # check if all buttons are the same as before except for the ones to ignore
        for i in range(0, len(btn_values)):
            if (btn_values[i] != self.prevBtnValues[i] and i not in buttonsToIgnore):
                return True
        
        return self.isToggleMessageChanged(newMessage)
    

    '''
    Checks all parameters of the new message for changes except for speed
    '''
    def isToggleMessageChanged(self, newMessage):
        return (newMessage.tw != self.prevMessageSent.tw or
                newMessage.la1 != self.prevMessageSent.la1 or
                newMessage.la2 != self.prevMessageSent.la2 or
                newMessage.wr_roll != self.prevMessageSent.wr_roll or 
                newMessage.wr_pitch != self.prevMessageSent.wr_pitch or 
                newMessage.ee != self.prevMessageSent.ee)


    """
    This method determines if Toggler node can publish to IK or Manual Nodes
    """
    def canPublish(self, btn_values):
        
        return True 
    
    '''
    Helper method sets all values of a toggle message to the given integer value
    '''
    def setAllMessageValues(self, message: ToggleMessage, value: int):
        message.tw = value
        message.la1 = value
        message.la2 = value
        message.wr_roll = value
        message.wr_pitch = value
        message.ee = value
        message.speed = float(value)
        
        return message

    '''
    Returns the direction of the actuator/motor based on joystick value
    '''
    def setActuatorDirection (self, actuatorAxes: float):
        direction = 0
        
        rounded_actuator = round(actuatorAxes, 0)

        if (rounded_actuator < 0):
            direction = - 1
        elif (rounded_actuator > 0):
            direction = 1

        return direction

    '''
    Creates a new message based on the axes values of the joystick
    '''
    def createMessage(self, axes_values: AxesValues, btn_values: ButtonValues):
        newMessage = ToggleMessage()

        # Setting Tower Dir
        newMessage.tw = self.setActuatorDirection(axes_values.tower)

        #LA1 Dir
        if (btn_values.actuator_hold_btn == 1):
            newMessage.la1 = self.setActuatorDirection(axes_values.actuator)

        #LA2 Dir
        else:
            newMessage.la2 = self.setActuatorDirection(axes_values.actuator)

        #CW is positive and CCW is negative
        #WR Pitch
        if (axes_values.wrist_pitch < 0):
            newMessage.wr_pitch = -1
        elif (axes_values.wrist_pitch > 0):
            newMessage.wr_pitch = 1
        else:
            newMessage.wr_pitch = 0

        #WR Roll
        if (axes_values.wrist_roll > 0):
            newMessage.wr_roll = 1
        elif (axes_values.wrist_roll < 0):
            newMessage.wr_roll = -1
        else:
            newMessage.wr_roll = 0

        #EE Dir
        if (btn_values.ee_open_btn == 1):
            newMessage.ee = 1
        elif (btn_values.ee_close_btn == 1):
            newMessage.ee = -1
        else:
            newMessage.ee = 0

        #Speed of Arm
        newMessage.speed = axes_values.speed_axis + 1.0

        return newMessage

    def isSwitched(prev_mn_btn, prev_ik_btn, mn_btn, ik_btn):
        return (prev_mn_btn != mn_btn or prev_ik_btn != ik_btn)

     
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

"""
Most of the code below should remain unchanged except maybe the node names
"""
def main(args=None):
    rclpy.init(args=args)           # if any args specified on node startup (via ros2 run <package> <node> args...)
    toggler_node = Toggler()   # class above
    rclpy.spin(toggler_node)        # spin = debounce (run for as long as it's on)
    rclpy.shutdown()                # when the spinning above stops, node should shutdown; i.e. SIGINT or otherwise


if __name__ == "__main__":
    main()