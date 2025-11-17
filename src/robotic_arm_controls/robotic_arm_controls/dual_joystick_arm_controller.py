import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from sensor_msgs.msg import Joy, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from general_interfaces.msg import GripperControl
from builtin_interfaces.msg import Duration
import numpy as np

class DualJoystickArmController(Node):
    def __init__(self):
        super().__init__('dual_joystick_arm_controller')

        self.control_mode = self.get_param("control_mode", rclpy.Parameter.Type.STRING, "single")
        self.control_rate = self.get_param("control_rate", rclpy.Parameter.Type.DOUBLE, 50.0) 
        self.deadzone = self.get_param("deadzone", rclpy.Parameter.Type.DOUBLE, 0.15)
        self.max_joint_velocity = self.get_param("max_joint_velocity", rclpy.Parameter.Type.DOUBLE, 0.5)

        self.current_joint_positions = [0.0] * 4
        self.joy_data_1 = None
        self.joy_data_2 = None
        self.controller_1_type = None
        self.controller_2_type = None

        self.joy_sub_1 = self.create_subscription(Joy, '/joy/controller_1', self.joy_callback_1, 20)

        if self.control_mode == "dual":
            self.joy_sub_2 = self.create_subscription(Joy, '/joy/controller_2', self.joy_callback_2, 20)

        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.joint_state_callback, 10)
        self.joint_state_pub = self.create_publisher(JointTrajectory, '/uorover_arm_controller/joint_trajectory', 10)

        self.gripper_pub = self.create_publisher(GripperControl, '/gripper_control/gripper_velocities', 10)
        self.get_logger().info("Dual Joystick Arm Controller Node Initialized")

    def joy_callback_1(self, msg: Joy):

        if self.controller_1_type is None:
            if len(msg.buttons) == 11:
                self.controller_1_type = "xbox"
            elif len(msg.buttons) == 12:
                self.controller_1_type = "logitech"
            else:
                self.get_logger().error("Unknown controller type for controller 1")
                return
            
        self.joy_data_1 = msg
        self.publish_trajectory_command()

        if self.control_mode == "single":
            self.publish_gripper_command()

    def joy_callback_2(self, msg: Joy):

        if self.control_mode != "dual":
            return
        
        if self.controller_2_type is None:
            if len(msg.buttons) == 11:
                self.controller_2_type = "xbox"
            elif len(msg.buttons) == 12:
                self.controller_2_type = "logitech"
            else:
                self.get_logger().error("Unknown controller type for controller 2")
                return
        
        self.joy_data_2 = msg

        self.publish_gripper_command()
    
    def joint_state_callback(self, msg: JointState):

        for i, name in enumerate(msg.name):
            if name in ['q1', 'q2', 'q3', 'q4']:
                joint_index = int(name[1]) - 1
                self.current_joint_positions[joint_index] = msg.position[i]

    def publish_trajectory_command(self):
        if self.joy_data_1 is None:
            return

        mapping = self.get_axis_mapping(controller_num=1)
        q1_vel = self.process_axis(self.joy_data_1, mapping['q1'], 'q1', controller_num=1)
        q2_vel = self.process_axis(self.joy_data_1, mapping['q2'], 'q2', controller_num=1)
        q3_vel = self.process_axis(self.joy_data_1, mapping['q3'], 'q3', controller_num=1)
        q4_vel = self.process_axis(self.joy_data_1, mapping['q4'], 'q4', controller_num=1)

        dt = 1.0 / self.control_rate
        target_positions = [
            self.current_joint_positions[0] + q1_vel * dt,
            self.current_joint_positions[1] + q2_vel * dt,
            self.current_joint_positions[2] + q3_vel * dt,
            self.current_joint_positions[3] + q4_vel * dt,
        ]

        trajectory = JointTrajectory()
        trajectory.joint_names = ['q1', 'q2', 'q3', 'q4']
        trajectory.headers.stamp = self.get_clock().now().to_msg()

        point = JointTrajectoryPoint()
        point.positions = target_positions
        point.time_from_start = Duration(sec=int(dt), nanosec=int(self.trajectory_duration * 1e9))

        trajectory.points = [point]
        self.joint_state_pub.publish(trajectory)

    def publish_gripper_command(self):
        if self.control_mode == "single":
            joy_data = self.joy_data_1
            controller_num = 1
        else:
            joy_data = self.joy_data_2
            controller_num = 2
        
        if joy_data is None:
            return
        
        mapping = self.get_axis_mapping(controller_num=controller_num)
        gripper_msg = GripperControl()

        if mapping.get('q5_axis', -1) >= 0:
            gripper_msg.roll_velocity = self.process_axis(
                joy_data, mapping['q5_axis'], 'q5', controller_num=controller_num
            )
        
        else:
            if self.get_button(joy_data, mapping.get('roll_cw_button', -1)):
                gripper_msg.roll_velocity = self.max_joint_velocity
            elif self.get_button(joy_data, mapping.get('roll_ccw_button', -1)):
                gripper_msg.roll_velocity = -self.max_joint_velocity
            else:
                gripper_msg.roll_velocity = 0.0
    
        if mapping.get('q6_axis', -1) >= 0:
            gripper_msg.ee_velocity = self.process_axis(
                joy_data, mapping['q6_axis'], 'q6', controller_num=controller_num
            )
        
        else:
            if self.get_button(joy_data, mapping.get('gripper_open_button', -1)):
                gripper_msg.ee_velocity = self.max_joint_velocity
            elif self.get_button(joy_data, mapping.get('gripper_close_button', -1)):
                gripper_msg.ee_velocity = -self.max_joint_velocity
            else:
                gripper_msg.ee_velocity = 0.0
        
        self.gripper_pub.publish(gripper_msg)

    def process_axis(self, joy_msg, axis_idx, joint_name, controller_num):
        if axis_idx < 0 or axis_idx >= len(joy_msg.axes):
            return 0.0
        
        value = joy_msg.axes[axis_idx]
        mapping = self.get_axis_mapping(controller_num=controller_num)

        if abs(value) < self.deadzone:
            return 0.0
        
        scale = mapping.get(f'{joint_name}_scale', 1.0)
        inverse = mapping.get(f'{joint_name}_inverse', False)

        sign = 1.0 if value >= 0 else -1.0
        scaled = sign * (abs(value) - self.deadzone) / (1.0 - self.deadzone)
        scaled *= self.max_joint_velocity * scale
        if inverse:
            scaled = -scaled
        
        return scaled
    
    def get_button(self, joy_msg, button_idx):
        if button_idx < 0 or button_idx >= len(joy_msg.buttons):
            return False
        return joy_msg.buttons[button_idx] == 1
    
    def get_axis_mapping(self, controller_num):
        if controller_num ==1:
            controller_type = self.controller_1_type
        else:
            controller_type = self.controller_2_type
        if controller_type is None:
            return {}
        
        prefix = f'controller_types.{controller_type}.'

        mapping = {}

        for i in range(1, 7):
            mapping[f'q{i}_axis']= self.get_param(
                f'{prefix}q{i}_axis', rclpy.Parameter.Type.INTEGER, -1
            )
            mapping[f'q{i}_scale']= self.get_param(
                f'{prefix}q{i}_scale', rclpy.Parameter.Type.DOUBLE, 1.0
            )
            mapping[f'q{i}_invert']= self.get_param(
                f'{prefix}q{i}_invert', rclpy.Parameter.Type.BOOL, False
            )
        
        mapping['roll_cw_button'] = self.get_param(
            f'{prefix}roll_cw_button', rclpy.Parameter.Type.INTEGER, -1
        )
        mapping['roll_ccw_button'] = self.get_param(
            f'{prefix}roll_ccw_button', rclpy.Parameter.Type.INTEGER, -1
        )
        mapping['gripper_open_button'] = self.get_param(
            f'{prefix}gripper_open_button', rclpy.Parameter.Type.INTEGER, -1
        )
        mapping['gripper_close_button'] = self.get_param(
            f'{prefix}gripper_close_button', rclpy.Parameter.Type.INTEGER, -1
        )   

        return mapping

    def get_param(self, param_name, param_type, default_val):
        self.declare_parameter(param_name, param_type)

        if default_val is None:
            param_val = self.get_parameter(param_name).value
        else:
            default_param = rclpy.parameter.Parameter(param_name, param_type, default_val)
            param_val = self.get_parameter_or(param_name, default_param).value

        if param_val is None:
            self.get_logger().error(f"Parameter {param_name} could not be retrieved and has no default value.")
            return default_val

        return param_val
    
def main(args=None):
    rclpy.init(args=args)
    controller = DualJoystickArmController()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        pass
    finally:
        controller.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()