#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"


namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Parent class on init fills the info object out with URDF details 
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }

        // intialize joint position and velocity interfaces with 0s
        // initialize joint interface map with joint names from info_ object
        
        // establish serial comms

        return CallbackReturn::SUCCESS;
    };

    std::vector<hardware_interface::StateInterface> export_state_interfaces() {
        // declare state interface vector

        // create the state interface objects joint and add them to the vector

        //return state_interfaces
    };

    std::vector<hardware_interface::CommandInterface> export_command_interfaces() {
        // declare command interface vector
        
        // create command interfaces for positions

        // return command interfaces
    }

    hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        // read positions from arduino over the serial port

        // update joint_position_state and joint_velocity_state with new values

        return hardware_interface::return_type::OK;
    }

    hardware_interface::return_type write(const rclcpp::Time & time, const rclcpp::Duration & period) {
        // read the joint_position_command_ vector to see updated target positions

        // send target position values to arduino over serial port

        return hardware_interface::return_type::OK;
    };

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)