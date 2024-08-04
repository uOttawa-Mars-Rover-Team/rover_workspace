#include "arm_controls/gpio_controller.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace arm_controls
{
    controller_interface::CallbackReturn GPIOController::on_init(){
        try
        {
            auto_declare<std::vector<std::string>>("outputs", std::vector<std::string>());
        }
        catch (const std::exception & e)
        {
            RCLCPP_ERROR(rclcpp::get_logger("GPIOController"), "Exception thrown during init stage with message: %s \n", e.what());
            return controller_interface::CallbackReturn::ERROR;
        }
        return controller_interface::CallbackReturn::SUCCESS;  
    } 
    
    controller_interface::InterfaceConfiguration GPIOController::command_interface_configuration() const {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
        config.names = outputs_;

        return config;
    }

    controller_interface::CallbackReturn GPIOController::on_configure(const rclcpp_lifecycle::State & previous_state){
        try
        {
            outputs_ = get_node()->get_parameter("outputs").as_string_array();

            // register subscriber
            subscription_command_ = get_node()->create_subscription<CmdType>(
            "/peripheral_enables", rclcpp::SystemDefaultsQoS(),
            [this](const CmdType::SharedPtr msg) { output_cmd_ptr_ = msg; });
        }
        catch (...)
        {
            return LifecycleNodeInterface::CallbackReturn::ERROR;
        }
        return LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    controller_interface::return_type GPIOController::update(const rclcpp::Time & time, const rclcpp::Duration & period){
        // set outputs
        if (!output_cmd_ptr_)
        {
            // no command received yet
            return controller_interface::return_type::OK;
        }

        command_interfaces_[0].set_value(output_cmd_ptr_->stepper1_en);
        command_interfaces_[1].set_value(output_cmd_ptr_->stepper2_en);
        command_interfaces_[2].set_value(output_cmd_ptr_->stepper3_en);
        command_interfaces_[3].set_value(output_cmd_ptr_->stepper4_en);
        command_interfaces_[4].set_value(output_cmd_ptr_->laser_en);
        command_interfaces_[5].set_value(output_cmd_ptr_->stop);

        return controller_interface::return_type::OK;
    }
}

PLUGINLIB_EXPORT_CLASS(
       arm_controls::GPIOController, controller_interface::ControllerInterface)