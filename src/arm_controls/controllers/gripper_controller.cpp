#include "arm_controls/gripper_controller.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace arm_controls
{
    controller_interface::CallbackReturn GripperController::on_init(){
        try
        {
            auto_declare<std::vector<std::string>>("joints", std::vector<std::string>());
        }
        catch (const std::exception & e)
        {
            RCLCPP_ERROR(rclcpp::get_logger("GripperController"), "Exception thrown during init stage with message: %s \n", e.what());
            return controller_interface::CallbackReturn::ERROR;
        }
        return controller_interface::CallbackReturn::SUCCESS;  
    } 
    
    controller_interface::InterfaceConfiguration GripperController::command_interface_configuration() const {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;

        for (std::string joint : joints_) {
            config.names.push_back(joint + INTERFACE_TYPE);
        }

        return config;
    }

    controller_interface::InterfaceConfiguration GripperController::state_interface_configuration() const {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
      
        for (std::string joint : joints_) {
            config.names.push_back(joint + INTERFACE_TYPE);
        }
      
        return config;
    }
    
    controller_interface::CallbackReturn GripperController::on_configure(const rclcpp_lifecycle::State & previous_state){
        try
        {
            joints_ = get_node()->get_parameter("joints").as_string_array();

            // register subscriber
            subscription_command_ = get_node()->create_subscription<CmdType>(
            "gripper_controller/gripper_velocities", rclcpp::SystemDefaultsQoS(),
            [this](const CmdType::SharedPtr msg) { output_cmd_ptr_ = msg; });
        }
        catch (...)
        {
            return LifecycleNodeInterface::CallbackReturn::ERROR;
        }
        return LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    controller_interface::return_type GripperController::update(const rclcpp::Time & time, const rclcpp::Duration & period){
        // set outputs
        if (!output_cmd_ptr_)
        {
            // no command received yet
            return controller_interface::return_type::OK;
        }

        command_interfaces_[0].set_value(output_cmd_ptr_->roll_velocity);
        command_interfaces_[1].set_value(output_cmd_ptr_->ee_velocity);

        return controller_interface::return_type::OK;
    }
}

PLUGINLIB_EXPORT_CLASS(arm_controls::GripperController, controller_interface::ControllerInterface)