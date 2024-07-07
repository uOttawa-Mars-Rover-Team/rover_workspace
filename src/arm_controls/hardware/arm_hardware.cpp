#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"


namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Implement on_init
    };

    std::vector<hardware_interface::StateInterface> export_state_interfaces() {
        // Implement export_State_interfaces
    };

    std::vector<hardware_interface::CommandInterface> export_command_interfaces() {
        // Implement export_command_interfaces
    }

    hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        // Implement read
    }

    hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) {
        // Implement write
    };

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)