#include "arm_controls/arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <control_toolbox/pid.hpp>

namespace arm_controls
{
    CallbackReturn ArmSystem::on_init(const hardware_interface::HardwareInfo & info){
        // Parent class' on_init fills the info object out with URDF details 
        // If URDF can't be read, return ERROR
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
            return CallbackReturn::ERROR;
        }

        //TODO: implement logic to check if URDF is providing all of the correct joints and interfaces

        num_joints = info_.joints.size();
        num_peripherals = info_.gpios.size();
 
        //References to the elements of these vectors will be passed to the controllers so that they can be updated/read
        //This allows the controller and the hardware interface to communicate with each other
        joint_position_state_.assign(num_joints, 0); 
        joint_velocity_state_.assign(num_joints, 0);
        joint_position_command_.assign(num_joints, 0);

        prev_position_command_ = "";
        
        //peripheral command vector order: stepper1 en, stepper2 en, stepper3 en, stepper4 en, laser en, stop
        peripheral_command_ = vector<double>(std::begin(DEFLT_PERIPHERAL_STATE), std::end(DEFLT_PERIPHERAL_STATE)); //this means that on init, all the steppers are enabled and the laser and emergency stop are disabled
        peripheral_state_ =  vector<double>(std::begin(DEFLT_PERIPHERAL_STATE), std::end(DEFLT_PERIPHERAL_STATE)); //this means that on init, all the steppers are enabled and the laser and emergency stop are disabled

        //PID Initialization
        for (int i = 0; i < LAST; i++){
            pids_.emplace_back(std::make_shared<control_toolbox::Pid>());
        }

        pids_[TOWER]->initPid(0.002342, 0, 0, 0, 0, true);
        pids_[SHOULDER]->initPid(0.0078556, 0, 0, 0, 0, true);
        pids_[ELBOW]->initPid(1.0, 0, 0, 0, 0, true);
        pids_[PITCH]->initPid(0.00096076, 0, 0, 0, 0, true);

        //Serial Intialization
        serialObject.connect_serial(0); 
        serialObject.publishToArduino(MANUAL_START_COMMAND); //this will set the arduino in IK mode
        
        return CallbackReturn::SUCCESS;
    }

    std::vector<hardware_interface::StateInterface> ArmSystem::export_state_interfaces() {
        std::vector<hardware_interface::StateInterface> state_interfaces;

        //Create the state interface objects and add them to the vector
        for (int i = 0; i < num_joints; i++){
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
            
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
        }

        //Create state interface objects from peripheral information and place them in the vector
        for (int i = 0; i < num_peripherals; i++){
            state_interfaces.emplace_back(hardware_interface::StateInterface(
                info_.gpios[i].name, "feedback", &peripheral_state_[i]));
        }

        return state_interfaces;
    }

    std::vector<hardware_interface::CommandInterface> ArmSystem::export_command_interfaces() {
        std::vector<hardware_interface::CommandInterface> command_interfaces;

        //Create command interface objects from the joint information and place them in the vector
        for (int i = 0; i < num_joints; i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
            
            if (i >= LAST){ // based on the XACRO file this should be q5 and q6 which are being used for velocity P right now
                command_interfaces.emplace_back(hardware_interface::CommandInterface(
                    info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &joint_position_command_[i]));
 
            }
        }

        //NOTE: The order of names in info_.joint and info_.gpio  is the same as the order in the xacro file

        //Create command interface objects from gpio information and place them in the vector
        for (int i = 0; i < num_peripherals; i++){
            command_interfaces.emplace_back(hardware_interface::CommandInterface(
                info_.gpios[i].name, "command", &peripheral_command_[i]));
        }

        return command_interfaces;
    }

    hardware_interface::return_type ArmSystem::read(const rclcpp::Time &time, const rclcpp::Duration &period) {
        //TODO: Serial library is performing most of the checking for us. We should move the error checking here to decouple the library and make it reusable. 
        
        //PROCESSING POSITION DATA        
        //Typical position feedback command: f;TW Position;SL Position;EL Position;PT Position;RL Velocity;EE Velocity;!
        std::string serialReadResult = serialObject.get_latest_position();

        std::istringstream ss(serialReadResult);
        std::string temp; // string that we read into when using the istringstream

        std::getline(ss, temp, ';'); //skip the first characters (i.e. f;) of the string

        for (size_t i = 0; i < num_joints; ++i) {
            //getline will load the  next part of the string up to the semicolon
            //putting this in an if statement will ensure that the code doesn't break if the string stream is in a failure state
            if (std::getline(ss, temp, ';') && temp != "!"){ 
                if (i < LAST){ // TOWER, SHOULDER, ELBOW, PITCH
                    double positionInRad = std::stod(temp) * PI / 180;
                    joint_position_state_[i] = positionInRad;
                } else { // ROLL, EE
                    joint_velocity_state_[i] = std::stod(temp); //ASSUMPTION: We are getting velocities back from the arduino between -1 and 1 so no further maniuplation should be needed 
                }
            }
        }

        //PROCESSING PERIPHERAL DATA
        //Typical gpio feedback command: g;S1;S2;S3;S4;L;ST;!
        ss.clear(); //clear the error flags
        ss.str(""); //clear the contents of the string stream

        serialReadResult = serialObject.get_peripheral_feedback();
        ss.str(serialReadResult);
               // RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "ser read res: %s", serialReadResult.c_str());

        std::getline(ss, temp, ';'); //skip the first characters (i.e. g;) of the string

        for (size_t i = 0; i < num_peripherals; ++i) {
            if (std::getline(ss, temp, ';') && temp != "!"){
                //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "thing: %d of %lf", i, std::stod(temp));
                peripheral_state_[i] = std::stod(temp);
            }
        }      

        //Joint velocity state will remain at 0 for the time-being
        //Typical velocity feedback command: v;TW;SL;EL;PT;RL;EE;!

        return hardware_interface::return_type::OK;
    }

    hardware_interface::return_type ArmSystem::write(const rclcpp::Time & time, const rclcpp::Duration & period) {
        // By default, the controllers should be sending positions for revolute joints in radians

        // PERIPHERAL COMMAND HANDLING
        // We keep track of time between function calls to ensure that these commands are not sent too frequenlty
        static rclcpp::Time last_time = time;

        if (time - last_time > peripheral_msg_period_) {
            last_time = time;
            // We don't use else if here because we want to be able to send consecutive commands if multiple buttons are changed at once
            if (peripheral_command_[0] != peripheral_state_[0]){
                serialObject.publishToArduino("stepper1;!"); //toggle stepper 1
            } if (peripheral_command_[1] != peripheral_state_[1]){
                serialObject.publishToArduino("stepper2;!"); //toggle stepper 2
            } if (peripheral_command_[2] != peripheral_state_[2]){
                serialObject.publishToArduino("stepper3;!"); //toggle stepper 3
            } if (peripheral_command_[3] != peripheral_state_[3]){
                serialObject.publishToArduino("stepper4;!"); //toggle stepper 4
            } if (peripheral_command_[4] != peripheral_state_[4]){
                serialObject.publishToArduino("laser;!"); //toggle laser
            } if (peripheral_command_[5] != peripheral_state_[5]){
                serialObject.publishToArduino("stop;!"); //toggle stop
            }
        }

        // JOINT COMMAND HANDLING 
        // By default, the controllers should be sending positions for revolute joints in radians
        // Example of typical position command to send: "S;TW Position;SL Position;EL Position;RL Velocity;EE Velocity;!
        // NOTE: Velocities are expected to be between -1 and 1 because thats what most of our current system accepts/provides as velocities (i.e spacemouse/arm_servo)
        std::ostringstream command_stream;
        command_stream << "S;";

        for (size_t i = 0; i < num_joints; ++i) {
            double valueToWrite;

            if (i < LAST){
                //valueToWrite = joint_position_command_[i] * 180 / PI;
                double error = joint_position_command_[i] - joint_position_state_[i];
                uint64_t dt = period.nanoseconds();

                valueToWrite = pids_[i]->computeCommand(error, dt);
            } else {
                valueToWrite = joint_velocity_command_[i];
            }

            valueToWrite = std::round(valueToWrite * 100.0) / 100.0; //bruh

            if (valueToWrite == -0.00) {
                valueToWrite = 0.00;
            }

            command_stream << std::fixed << std::setprecision(2) << valueToWrite << ";";
        }

        command_stream << "!";
        
        std::string command = command_stream.str();

        // print out cmd; beware though since these are not filtered, might be equal to prev cmd
        //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Write: %s", command.c_str());

        if (command != prev_position_command_) {
            RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Write: %s", command.c_str());
            //RCLCPP_INFO(rclcpp::get_logger("ArmSystem"), "Serial Write: %s", prev_position_command_.c_str());
            serialObject.publishToArduino(command);
            prev_position_command_ = command;
        }

        return hardware_interface::return_type::OK;
    }

} // namespace arm_controls

PLUGINLIB_EXPORT_CLASS(
       arm_controls::ArmSystem, hardware_interface::SystemInterface)