#ifndef ARM_CONTROLS__ARM_HARDWARE_HPP_
#define ARM_CONTROLS__ARM_HARDWARE_HPP_

#include <sstream>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

#include "general_interfaces/msg/arm_pose.hpp" // IWYU pragma: keep
#include "rclcpp/node.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "../serial_communication_library/include/serial_communication.hpp"
#include "rclcpp/rclcpp.hpp"

//#include <general_interfaces/msg/detail/arm_pose__struct.h>
//#include <unordered_map>

namespace arm_controls {
    using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;
    const int numInterfaces = 6;
    const int PI = 3.14159265358979323846;
    const string IK_START_COMMAND = "!I;!";

    class HARDWARE_INTERFACE_PUBLIC ArmSystem
    : public hardware_interface::SystemInterface {
        public:
            CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;
            std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
            std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;
            hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) override;
            hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) override;
        
            // interfaces
            std::vector<double> joint_position_command_;
            std::vector<double> joint_position_state_;
            std::vector<double> joint_velocity_state_;

            SerialCommunication serialObject;
            //std::unordered_map<std::string, std::vector<std::string>> joint_interfaces = {{"position", {}}, {"velocity", {}}};

            enum Joint { TOWER = 0, SHOULDER, ELBOW, WRIST, LAST };
    };
} // namespace arm_controls

#endif

//d;TW;EL;SH;PT;RL
//f;TW;EL;SH;PT;RL