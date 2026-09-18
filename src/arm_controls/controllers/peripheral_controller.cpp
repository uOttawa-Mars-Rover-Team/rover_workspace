#include "arm_controls/peripheral_controller.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace arm_controls
{
    controller_interface::CallbackReturn PeripheralController::on_init(){
        try
        {
            auto_declare<std::vector<std::string>>("peripherals", std::vector<std::string>());
        }
        catch (const std::exception & e)
        {
            RCLCPP_ERROR(rclcpp::get_logger("PeripheralController"), "Exception thrown during init stage with message: %s \n", e.what());
            return controller_interface::CallbackReturn::ERROR;
        }
        return controller_interface::CallbackReturn::SUCCESS;  
    } 
    
    controller_interface::InterfaceConfiguration PeripheralController::command_interface_configuration() const {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;

        for (std::string peripheral : peripherals_) {
            config.names.push_back(peripheral + "/command");
        }

        return config;
    }

    controller_interface::InterfaceConfiguration PeripheralController::state_interface_configuration() const {
        controller_interface::InterfaceConfiguration config;
        config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
      
        for (std::string peripheral : peripherals_) {
            config.names.push_back(peripheral + "/feedback");
        }
      
        return config;
    }
    
    controller_interface::CallbackReturn PeripheralController::on_configure(const rclcpp_lifecycle::State & previous_state){
        try
        {
            peripherals_ = get_node()->get_parameter("peripherals").as_string_array();

            // register subscriber
            subscription_command_ = get_node()->create_subscription<CmdType>(
            "peripheral_controller/peripheral_enables", rclcpp::SystemDefaultsQoS(),
            [this](const CmdType::SharedPtr msg) { output_cmd_ptr_ = msg; });
        }
        catch (...)
        {
            return LifecycleNodeInterface::CallbackReturn::ERROR;
        }
        return LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    controller_interface::return_type PeripheralController::update(const rclcpp::Time & time, const rclcpp::Duration & period){
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
        command_interfaces_[5].set_value(output_cmd_ptr_->emergency_stop_en);

        return controller_interface::return_type::OK;
    }
}

PLUGINLIB_EXPORT_CLASS(arm_controls::PeripheralController, controller_interface::ControllerInterface)