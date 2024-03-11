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
#include "control_toolbox/pid.hpp"

#define Phoenix_No_WPI

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

  hardware_interface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State &previous_state) override;

  hardware_interface::return_type read(const rclcpp::Time &time,
                                       const rclcpp::Duration &period) override;
  hardware_interface::return_type
  write(const rclcpp::Time & /*time*/,
        const rclcpp::Duration & dt) override;

protected:
  std::vector<double> wheel_velocity_command_;
  std::vector<double> wheel_position_;
  std::vector<double> wheel_velocities_;

  control_toolbox::Pid pid_;

  double read_rate_, update_rate_;

  std::unordered_map<std::string, std::vector<std::string>> joint_interfaces = {
      {"position", {}}, {"velocity", {}}};

  std::vector<ctre::phoenix::motorcontrol::can::TalonSRX *> talons_;

  enum Wheels {
    FL,
    FR,
    RR,
    RL,
    LAST,
  };

  double counts_per_rotation_;
  double gear_ratio_;
  double talon_period_;
  double wheel_circumference_;

}; // class drive_system
} // namespace chassis_controls
#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
