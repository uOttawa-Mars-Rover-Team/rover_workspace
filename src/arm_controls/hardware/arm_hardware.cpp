#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <string>
#include <iomanip> // For std::setprecision

namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Serial comms initialized when serial comm object is intialized
        
        // Parent class on init fills the info object out with URDF details 
        // If URDF can't be read, return ERROR
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }

        // intialize joint position and velocity interfaces with 0s
        joint_position_state_.assign(numInterfaces, 0);
        joint_velocity_state_.assign(numInterfaces, 0);
        
        joint_position_command_.assign(numInterfaces, 0);

        serialObject.connect_serial(0);


        // for loop to check URDF
                
        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> ArmSystem::export_state_interfaces() {
        std::vector<hardware_interface::StateInterface> state_interfaces;

        // create the state interface objects and add them to the vector
        for (auto i = 0u; i < info_.joints.size(); i++){
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
            
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
        }

        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> ArmSystem::export_command_interfaces() {
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        // create command interface objects and place them in the vector
        for (auto i = 0u; i < info_.joints.size(); i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
        }

        return command_interfaces;
    }

    hardware_interface::return_type ArmSystem::read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        //TO REMOVE AFTER IMPLEMENTING PROPER READ:
        std::string serialReadResult = "";
        //std::string serialReadResult = getLatestArduinoState(); // TODO: Implement this method in the serial library

        //parsing a string like this into the state interface values f;TW;SL;EL;PT;RL;EE (all positions)
        //the state interface values are stored in the joint_velocity_state_ and joint_position_state_ vectors
        //TODO: Decide what velocity feedback return messages will look like

        if(serialReadResult[0] != 'f'){
            //probably better to log an error here
            return hardware_interface::return_type::ERROR;;
        }

        std::string temp;
        std::istringstream ss(serialReadResult);

        std::getline(ss, temp, ';'); //skip the f; part of the string

        //TODO: change this to a for loop with num interfaces
        while (std::getline(ss, temp, ';')){
            joint_position_state_.push_back(std::stod(temp));
        }

        //joint velocity state will remain at 0 for the time being

        return hardware_interface::return_type::OK;
    }

    hardware_interface::return_type ArmSystem::write(const rclcpp::Time & time, const rclcpp::Duration & period) {
        // read the joint_position_command_ vector to see updated target positions
        // Example of typical command to send "I;TW;SL;EL;PT;RL;EE!
        // Q1;Q2;Q3;Q4;Q5;Q6
        // send target position values to arduino over serial port

        std::ostringstream command_stream;
        command_stream << "I;";

        for (size_t i = 0; i < numInterfaces; ++i) {
            command_stream << std::fixed << std::setprecision(2) << joint_position_command_[i];
            if (i < numInterfaces - 1) {
                command_stream << ";";
            }
        }
        command_stream << "!";

        std::string command = command_stream.str();
        
        serialObject.publishToArduino(command);

        return hardware_interface::return_type::OK;
    }

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)