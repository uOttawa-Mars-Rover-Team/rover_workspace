#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <string>
#include <iomanip> // For std::setprecision

#include <thread>

namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Parent class on init fills the info object out with URDF details 
        // If URDF can't be read, return ERROR
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }

        //This vector is updated is used by the coontrollers to read the state after exporting
        joint_position_state_.assign(numInterfaces, 0); 
        joint_velocity_state_.assign(numInterfaces, 0);
        
        joint_position_command_.assign(numInterfaces, 0);

        serialObject.connect_serial(0); 
        serialObject.publishToArduino("I;!"); //this will set the arduino in IK mode
        
        //TODO: implement logic to check if URDF is providing all of the correct joints and interfaces

        //TODO: Initialize PID Objects here (call initPID)
                
        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> ArmSystem::export_state_interfaces() {
        std::vector<hardware_interface::StateInterface> state_interfaces;

        // TODO: Export state interfaces for GPIO

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
        cout <<"export commands"<< endl;
        
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        // TOOD: Export command interfaces for GPIO

        // create command interface objects and place them in the vector
        for (auto i = 0u; i < info_.joints.size(); i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
        }

        return command_interfaces;
    }

    hardware_interface::return_type ArmSystem::read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        //parsing a string like this into the state interface values f;TW;SL;EL;PT;RL;EE;!
        //the state interface values are stored in the joint_velocity_state_ and joint_position_state_ vectors
        //TODO: Add filtering for velocity feedback and write it to the state interface for velocity 
        
        std::string serialReadResult = serialObject.get_latest_position();
        //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Read: %s", serialReadResult.c_str());
        
        std::istringstream ss(serialReadResult);
        std::string temp; // string that we read into when using the istringstream

        std::getline(ss, temp, ';'); //skip the f; part of the string

        for (size_t i = 0; i < numInterfaces; ++i) {
            //getline will load the  next part of the string up to the semicolon
            //putting this in an if statement will ensure that the code doesn't break if the string stream is in a failure state
            if (std::getline(ss, temp, ';') && temp != "!"){ 
                // Arduino sends the position in degrees, but the controller needs it in radians
                double positionInRad = std::stod(temp) * PI / 180;

                joint_position_state_[i] = positionInRad;
            }
        }

        //Joint velocity state will remain at 0 for the time being

        return hardware_interface::return_type::OK;
    }

    hardware_interface::return_type ArmSystem::write(const rclcpp::Time & time, const rclcpp::Duration & period) {
        // Example of typical command to send "S;40;20;-20;0;0;200;!
        // By default, the controllers should be sending positions for revolute joints in degrees
        // TODO: Use PID here to adjust the position that we are sending
        std::ostringstream command_stream;
        command_stream << "S;";

        for (size_t i = 0; i < numInterfaces; ++i) {
            double positionInDegrees = joint_position_command_[i] * 180 / PI;
            command_stream << std::fixed << std:: setprecision(2)<<positionInDegrees;
            
            if (i < numInterfaces - 1) {
                command_stream << ";";
            }
        }
        command_stream << ";!";

        std::string command = command_stream.str();
        //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Write: %s", command.c_str());
        
        serialObject.publishToArduino(command);

        return hardware_interface::return_type::OK;
    }

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)