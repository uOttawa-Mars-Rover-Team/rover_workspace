#ifndef CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
#define CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_

#include "control_toolbox/pid.hpp"
#include "ctre/phoenix/motorcontrol/can/TalonSRX.h"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include <cstddef>
#include <memory>
#include <rclcpp/logger.hpp>

#define Phoenix_No_WPI

namespace chassis_controls {
using CallbackReturn =
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

class HARDWARE_INTERFACE_PUBLIC DriveSystem
    : public hardware_interface::SystemInterface {

public:
  CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;

  hardware_interface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State &previous_state) override;

  std::vector<hardware_interface::StateInterface>
  export_state_interfaces() override;

  std::vector<hardware_interface::CommandInterface>
  export_command_interfaces() override;

  hardware_interface::return_type read(const rclcpp::Time &time,
                                       const rclcpp::Duration &period) override;
  hardware_interface::return_type write(const rclcpp::Time & /*time*/,
                                        const rclcpp::Duration &dt) override;


  // Helper methods for converting velocity to pwm and back
  double velocity_to_pwm(double velocity, size_t wheel);
  double pwm_to_velocity(double pwm, size_t wheel);
  double get_x_intercept(size_t wheel);

protected:
  enum Wheels {
    FL,
    FR,
    RR,
    RL,
    LAST,
  };

  struct Config {
    int enc_counts_per_rev;
    double wheel_circumference;
    double max_velocity;
    double controller_period;
    control_toolbox::Pid::Gains pid_gains_l;
    control_toolbox::Pid::Gains pid_gains_r;
    std::vector<double> wheel_m;
    std::vector<double> wheel_b;
  };

  std::vector<double> wheel_velocity_command_;
  std::vector<double> wheel_position_;
  std::vector<double> wheel_velocities_;

  bool testing_;
  double tested_pwm_;

  std::unordered_map<std::string, std::vector<std::string>> joint_interfaces = {
      {"position", {}}, {"velocity", {}}};

  Config cfg_;
  std::vector<std::shared_ptr<ctre::phoenix::motorcontrol::can::TalonSRX>>
      talons_;
  std::vector<std::shared_ptr<control_toolbox::Pid>> pids_;


private:
  rclcpp::Logger logger_ = rclcpp::get_logger("test logger");
}; // class drive_system
} // namespace chassis_controls
#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
