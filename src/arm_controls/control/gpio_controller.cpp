#include "arm_controls/gpio_controller.hpp"
#include "pluginlib/class_list_macros.hpp"

namespace arm_controls
{
    controller_interface::CallbackReturn GPIOController::on_init(){
        
    } 
    
    controller_interface::InterfaceConfiguration GPIOController::command_interface_configuration() const {

    }

    controller_interface::InterfaceConfiguration GPIOController::state_interface_configuration() const {

    }

    controller_interface::CallbackReturn GPIOController::on_configure(const rclcpp_lifecycle::State & previous_state){

    }

    controller_interface::CallbackReturn GPIOController::on_activate(const rclcpp_lifecycle::State & previous_state){

    }

    controller_interface::return_type GPIOController::update(const rclcpp::Time & time, const rclcpp::Duration & period){

    }

    controller_interface::CallbackReturn GPIOController::on_deactivate(const rclcpp_lifecycle::State & previous_state){

    }
}

PLUGINLIB_EXPORT_CLASS(
       arm_controls::GPIOController, controller_interface::ControllerInterface)