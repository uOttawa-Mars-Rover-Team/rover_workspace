#ifndef PERIPHERAL_CONTROLLER_HPP_
#define PERIPHERAL_CONTROLLER_HPP_

#include <memory>
#include <string>
#include <vector>

#include "controller_interface/controller_interface.hpp"
#include "general_interfaces/msg/arm_gpio.hpp"

namespace arm_controls {
    using CmdType = general_interfaces::msg::ArmGpio; //change this to a custom message that the spacemouse node will also use

    class PeripheralController : public controller_interface::ControllerInterface {
        public:
            /*
            Defines aliases for making shared pointers of this class.
            Defines a static function that returns a shared pointer of this class
            */
            RCLCPP_SHARED_PTR_DEFINITIONS(PeripheralController);

            CallbackReturn on_init() override;
            controller_interface::InterfaceConfiguration command_interface_configuration() const override;
            controller_interface::InterfaceConfiguration state_interface_configuration() const override;
            CallbackReturn on_configure(const rclcpp_lifecycle::State & previous_state) override;
            controller_interface::return_type update(const rclcpp::Time & time, const rclcpp::Duration & period) override;

        private:
            std::vector<std::string> peripherals_; //Stores the input parameters that we put into the YAML file for this controller 

        protected:
            // internal commands
            std::shared_ptr<CmdType> output_cmd_ptr_; //The data we read on the subscriber callback should be stored here

            // subscriber
            rclcpp::Subscription<CmdType>::SharedPtr subscription_command_;
    };
}  // namespace ros2_control_demo_example_10

#endif  // PERIPHERAL_CONTROLLER_HPP_