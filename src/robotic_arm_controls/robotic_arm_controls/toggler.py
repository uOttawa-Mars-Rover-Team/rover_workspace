#!/usr/bin/python3                 

from typing import NamedTuple, TypeVar # For parameter helper function

import rclpy # rospy for ROS2
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.action import ActionClient
from sensor_msgs.msg import Joy
from std_msgs.msg import String
from general_interfaces.msg import ToggleMessage
from general_interfaces.action import ZeroArm

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
    second_speed_btn: int
    third_speed_btn: int
    lowest_speed_btn: int
    norm_speed_btn: int
    btn_6: int 
    mn_mode_switch: int 
    ik_mode_switch: int 
    btn_9: int 
    zeroing_btn: int 
    actuator_hold_btn: int 

class Toggler(Node):
    MANUAL_MODE = "m"
    IK_MODE = "ik"
    
    def __init__(self, node_name: str = "toggler"):
        super().__init__(node_name)
        self.get_logger().info(f"Started node at: {self.get_fully_qualified_name()}")

        #Subscribers
        self.subscriber = self.create_subscription(Joy, "/arm_joy", self.joy_callback, 20)

        #Publishers
        self.ik_publisher = self.create_publisher(ToggleMessage, '/ik_joy', 20)
        self.m_publisher = self.create_publisher(ToggleMessage, '/m_joy', 20)
        self.mode_publisher = self.create_publisher(String, '/mode', 20)

        #Action Clients
        self.zero_client = ActionClient(self, ZeroArm, 'zero_arm')

        # The node's logger, may just use print() instead
        self.get_logger().info(f"Subscribing to messages from: {self.subscriber.topic_name}")

        self.toggle_mode = Toggler.MANUAL_MODE
        
        self.prevMessageSent = self.setAllMessageValues(ToggleMessage(), 3)
        self.prevBtnValues = ButtonValues(3,3,3,3,3,3,3,3,3,3,3,3)

        #parameters for the zeroing action
        self.isZeroing = False
    

    #Action Client Methods
    '''
    Sends a goal to the router node in order to zero the arm
    '''
    def send_zero_goal(self, joint):
        goal_msg = ZeroArm.Goal()
        goal_msg.joint = joint
        
        self.get_logger().info(f"Sending goal to zero arm: {joint}")
        
        self._send_goal_future =  self.zero_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.zero_response_callback)

    '''
    Callback for send_zero_goal once the action is accepted
    '''
    def zero_response_callback(self, future):
        goal_handle = future.result()
        
        if not goal_handle.accepted:
            self.get_logger().info("Goal rejected :(")
            return

        self.get_logger().info("Goal accepted :)")

        self.isZeroing = True
        self._goal_handle = goal_handle

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    '''
    Callback for send_zero_goal once the action is done
    '''
    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f"Result of zeroing: {result}")
        self.isZeroing = False

    '''
    Callback for completion of the cancellation of the zeroing action
    '''
    def cancel_done(self, future):
        cancel_response = future.result()

        if len(cancel_response.goals_canceling) > 0:
            self.get_logger().info('Goal successfully canceled')
        else:
            self.get_logger().info('Goal failed to cancel')

        self.isZeroing = False


    # Callbacks
    '''
    Callback for the joystick subscriber. This method is called whenever a message is received from the joystick
    '''
    def joy_callback(self, message: Joy):

        #switched = False

        axes_values = AxesValues(*message.axes)
        btn_values = ButtonValues(*message.buttons)
        
        mn_btn = btn_values.mn_mode_switch #button for ik (btn 8 on controller)
        ik_btn = btn_values.ik_mode_switch #button for manual (btn 9 on controller)
        zero_btn = btn_values.zeroing_btn #button for zeroing the arm (btn 11 on controller)

        #prints axes values of arm
        printAxes = f"\naxes_values: {axes_values}\n"

        # print message
        toPrint = f'ik: {ik_btn} manual: {mn_btn}, zero: {zero_btn}'

        newMessage = self.createMessage(axes_values, btn_values)

        if (self.isChanged(newMessage, btn_values)):
            if mn_btn and (not ik_btn):
                self.toggle_mode = Toggler.MANUAL_MODE
                toPrint += "\nSwitching to Manual"
                mode = String()
                mode.data = "M;!"
                self.mode_publisher.publish(mode)
                #switched = True

            elif (not mn_btn) and (ik_btn):
                self.toggle_mode = Toggler.IK_MODE
                toPrint += "\nSwitching to IK"
                mode = String()
                mode.data = "I;!"
                self.mode_publisher.publish(mode)
                #switched = True

            if (self.canPublish(btn_values)):
                toPrint += f"\nMessage: {newMessage.tw, newMessage.la1, newMessage.la2, newMessage.wr_pitch, newMessage.wr_roll, newMessage.ee, newMessage.speed}"

                if zero_btn and self.isZeroing:
                    future = self._goal_handle.cancel_goal_async()
                    future.add_done_callback(self.cancel_done)

                    toPrint += "\nCancelling Zeroing Request"

                elif zero_btn and not self.isZeroing:
                    self.send_zero_goal("EE")
                    toPrint += "\nZeroing EE"

                elif self.toggle_mode == Toggler.MANUAL_MODE:
                    toPrint += "\nPublishing to Manual"
                    self.m_publisher.publish(newMessage)

                elif self.toggle_mode == Toggler.IK_MODE:
                    toPrint += "\nPublishing to IK"
                    self.ik_publisher.publish(newMessage)
            
            self.get_logger().info(toPrint)
            #self.get_logger().info(printAxes)

        self.prevMessageSent = newMessage
        self.prevBtnValues = btn_values

    
    #Helper Methods
    """
    This method checks if either message or button values have changed to determine if Toggler Node can switch to another mode/publish
    """
    def isChanged(self, newMessage, btn_values):
        buttonsToIgnore = [2,3,4,5,6,9,11]
        
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
        switched = Toggler.isSwitched(self.prevBtnValues.mn_mode_switch, self.prevBtnValues.ik_mode_switch, btn_values.mn_mode_switch, btn_values.ik_mode_switch)
        
        if switched:
            return False  
        
        if self.isZeroing and not btn_values.zeroing_btn:
            return False

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