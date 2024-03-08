#ifndef CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
#define CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_

#include "ctre/phoenix/motorcontrol/can/TalonSRX.h"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include <rclcpp/duration.hpp>
#include <unordered_map>

#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#define Phoenix_No_WPI
#include "ctre/Phoenix.h"
#include "ctre/phoenix/unmanaged/Unmanaged.h"

namespace chassis_controls {
using CallbackReturn =
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class HARDWARE_INTERFACE_PUBLIC DriveSystem
    : public hardware_interface::SystemInterface {
public:

  CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;

  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override;
  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override;

  hardware_interface::return_type read(const rclcpp::Time &time,
                                       const rclcpp::Duration &period) override;
  hardware_interface::return_type
  write(const rclcpp::Time & /*time*/,
        const rclcpp::Duration & /*period*/) override;

protected:
  std::vector<double> wheel_velocity_command_;
  std::vector<double> wheel_position_;
  std::vector<double> wheel_velocities_;

  std::unordered_map<std::string, std::vector<std::string>> joint_interfaces = {
      {"position", {}}, {"velocity", {}}};

  ctre::phoenix::motorcontrol::can::TalonSRX * front_right_;
  ctre::phoenix::motorcontrol::can::TalonSRX * front_left_;
  ctre::phoenix::motorcontrol::can::TalonSRX * rear_left_;
  ctre::phoenix::motorcontrol::can::TalonSRX * rear_right_;

}; // class drive_system
} // namespace chassis_controls
#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
