#ifndef ARM_CONTROLS__ARM_HARDWARE_HPP_
#define ARM_CONTROLS__ARM_HARDWARE_HPP_

#include <sstream>
#include <string>
#include <iomanip> // For std::setprecision
#include <chrono>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/node.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp/rclcpp.hpp"

#include "../serial_communication_library/include/serial_communication.hpp"

namespace arm_controls {
    using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

    const double PI = 3.14159265358979;
    const string IK_START_COMMAND = "I;!";
    double DEFLT_PERIPHERAL_STATE[] = {true, true, true, true, false, false};
    rclcpp::Duration peripheral_msg_period_(0, 200000000);

    int num_joints;
    int num_peripherals;

    class HARDWARE_INTERFACE_PUBLIC ArmSystem: public hardware_interface::SystemInterface {
        public:
            CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;
            std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
            std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
            hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) override;
            hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration &period) override;
                    
            enum Joint { TOWER = 0, SHOULDER, ELBOW, WRIST, LAST };

            //Vectors for joint interfaces
            //NOTE: These vectors must contain doubles beacause of the way the CommandInterface and StateInterface constructors are defined in ros2 control
            std::vector<double> joint_position_command_;
            std::vector<double> joint_velocity_command_;
            std::vector<double> joint_position_state_;
            std::vector<double> joint_velocity_state_;
            //Vectors for gpio interfaces 
            std::vector<double> peripheral_command_;
            std::vector<double> peripheral_state_;


            std::string prev_position_command_; // string to save the previous position command sent ot the arduino
           
            SerialCommunication serialObject;
    };
} // namespace arm_controls

#endif