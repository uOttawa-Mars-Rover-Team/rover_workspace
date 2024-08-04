#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Parent class' on_init fills the info object out with URDF details 
        // If URDF can't be read, return ERROR
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }

        //TODO: implement logic to check if URDF is providing all of the correct joints and interfaces

        //References to the elements of these vectors will be passed to the controllers so that they can be updated/read
        //This allows the controller and the hardware interface to communicate with each other
        joint_position_state_.assign(NUM_JOINTS, 0); 
        joint_velocity_state_.assign(NUM_JOINTS, 0);
        joint_position_command_.assign(NUM_JOINTS, 0);
        //gpio command vector order: stepper1 en, stepper2 en, stepper3 en, stepper4 en, laser en
        gpio_command_ = {true, true, true, true, false}; //this means that on init we enable all of the steppers and disable the laser

        prev_gpio_command_ = gpio_command_;
        prev_position_command_ = "";

        //TODO: Initialize PID Objects here (call initPID)

        serialObject.connect_serial(0); 
        serialObject.publishToArduino(IK_START_COMMAND); //this will set the arduino in IK mode
        
        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> ArmSystem::export_state_interfaces() {
        std::vector<hardware_interface::StateInterface> state_interfaces;

        //Create the state interface objects and add them to the vector
        for (int i = 0; i < info_.joints.size(); i++){
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
            
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
        }

        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> ArmSystem::export_command_interfaces() {
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        //Create command interface objects from the joint information and place them in the vector
        for (int i = 0; i < info_.joints.size(); i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
        }

        //NOTE: The order of names in info_.joint and info_.gpio  is the same as the order in the xacro file

        //Create command interface objects from gpio information and place them in the vector
        for (int i = 0; i < info_.gpios.size(); i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.gpios[i].name, GPIO_ENABLE, &gpio_command_[i]));
        }

        return command_interfaces;
    }

    hardware_interface::return_type ArmSystem::read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        //Typical position feedback command: f;TW;SL;EL;PT;RL;EE;!
        //Typical velocity feedback command: v;TW;SL;EL;PT;RL;EE;!
        //TODO: Serial library is performing most of the checking for us. We should move the error checking here to decouple the library. 
        
        std::string serialReadResult = serialObject.get_latest_position();
        //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Read: %s", serialReadResult.c_str());
        
        std::istringstream ss(serialReadResult);
        std::string temp; // string that we read into when using the istringstream

        std::getline(ss, temp, ';'); //skip the first characters (i.e. f;) of the string

        for (size_t i = 0; i < NUM_JOINTS; ++i) {
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
        // By default, the controllers should be sending positions for revolute joints in radians
        
        // GPIO COMMAND HANDLING
        // We don't use else if here because we want to be able to send consecutive commands if multiple buttons are changed at once
        if (gpio_command_[0] != prev_gpio_command_[0]){
            serialObject.publishToArduino("stepper1;!"); //toggle stepper 1
        } if (gpio_command_[1] != prev_gpio_command_[1]){
            serialObject.publishToArduino("stepper2;!"); //toggle stepper 2
        } if (gpio_command_[2] != prev_gpio_command_[2]){
            serialObject.publishToArduino("stepper3;!"); //toggle stepper 3
        } if (gpio_command_[3] != prev_gpio_command_[3]){
            serialObject.publishToArduino("stepper4;!"); //toggle stepper 4
        } if (gpio_command_[4] != prev_gpio_command_[4]){
            serialObject.publishToArduino("laser;!"); //toggle laser
        }

        // POSITION COMMAND HANDLING 
        // Example of typical position command to send: "S;40;20;-20;0;0;200;!
        std::ostringstream command_stream;
        command_stream << "S;";

        for (size_t i = 0; i < NUM_JOINTS; ++i) {
            double positionInDegrees = joint_position_command_[i] * 180 / PI;
            command_stream << std::fixed << std:: setprecision(2)<<positionInDegrees;
            // TODO: Use PID here to adjust the position that we are sending
            if (i < NUM_JOINTS - 1) {
                command_stream << ";";
            }
        }
        command_stream << ";!";

        std::string command = command_stream.str();
        //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Write: %s", command.c_str());

        //std::time_t now = std::chrono::system_clock::to_time_t(std::chrono::system_clock::now());
        //std::cout << "Current time: " << std::ctime(&now);
        //std::cout << "write" << endl;

        if (command != prev_position_command_) {
            serialObject.publishToArduino(command);
            prev_position_command_ = command;
        }

        return hardware_interface::return_type::OK;
    }

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)