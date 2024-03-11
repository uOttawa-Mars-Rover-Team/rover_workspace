#include "hardware_interface/system_interface.hpp"
#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <string>
#include <sys/types.h>
#define Phoenix_No_WPI
#include "ctre/phoenix/motorcontrol/ControlMode.h"
#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#include "ctre/phoenix/unmanaged/Unmanaged.h"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "include/chassis_controls/drive_hardware.hpp"

namespace chassis_controls {
CallbackReturn
DriveSystem::on_init(const hardware_interface::HardwareInfo &info) {

  // parse URDF
  if (hardware_interface::SystemInterface::on_init(info) !=
      CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // interfaces:
  wheel_position_.assign(4, 0);
  wheel_velocities_.assign(4, 0);
  wheel_velocity_command_.assign(4, 0);

  for (const auto &joint : info_.joints) {
    for (const auto &interface : joint.state_interfaces) {
      joint_interfaces[interface.name].push_back(joint.name);
    }
  }

  cfg_.loop_rate = 30;
  cfg_.enc_counts_per_rev = 1024;
  cfg_.gear_ratio = 1.0 / 25;
  cfg_.wheel_circumference = 0.203005 * 2 * M_PI;

  // assign controllers by CANid
  talons_.assign(4, 0);
  talons_[FL] = new ctre::phoenix::motorcontrol::can::TalonSRX(20);
  talons_[FR] = new ctre::phoenix::motorcontrol::can::TalonSRX(10);
  talons_[RR] = new ctre::phoenix::motorcontrol::can::TalonSRX(40);
  talons_[RL] = new ctre::phoenix::motorcontrol::can::TalonSRX(30);
  // bring up PID
  pid_.initPid(5.0, 0.0, 0.0, 0.3, -0.3, true);

  return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface>
DriveSystem::export_state_interfaces() {
  std::vector<hardware_interface::StateInterface> state_interfaces;

  size_t ind = 0;
  for (const auto &joint_name : joint_interfaces["position"]) {
    state_interfaces.emplace_back(joint_name, "position",
                                  &wheel_position_[ind++]);
  }

  ind = 0;
  for (const auto &joint_name : joint_interfaces["velocity"]) {
    state_interfaces.emplace_back(joint_name, "velocity",
                                  &wheel_velocities_[ind++]);
  }
  return state_interfaces;
}
std::vector<hardware_interface::CommandInterface>
DriveSystem::export_command_interfaces() {
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  size_t ind = 0;
  for (const auto &joint_name : joint_interfaces["velocity"]) {
    command_interfaces.emplace_back(joint_name, "velocity",
                                    &wheel_velocity_command_[ind++]);
  }
  return command_interfaces;
}

hardware_interface::CallbackReturn
DriveSystem::on_activate(const rclcpp_lifecycle::State & /*previous_state*/) {

  // invert this talon so +ve is fwd
  talons_[FR]->SetInverted(true);

  int err;
  for (size_t wheel = FL; wheel < LAST; wheel++) {

    // configure each encoder, returns non-zero if erro
    err = (int)talons_[wheel]->ConfigSelectedFeedbackSensor(
        ctre::phoenix::motorcontrol::FeedbackDevice::CTRE_MagEncoder_Relative,
        0, 100);

    // zero each position encoder
    talons_[wheel]->SetSelectedSensorPosition(0.0);

    if (err) {
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  // invert this encoder so +ve is fwd
  talons_[FL]->SetSensorPhase(true);

  return hardware_interface::CallbackReturn::SUCCESS;
};

hardware_interface::return_type DriveSystem::read(const rclcpp::Time &,
                                                  const rclcpp::Duration &) {

  // update our state interface for each wheel
  for (size_t wheel = FL; wheel < LAST; wheel++) {

    // convert counts to rad
    wheel_position_[wheel] =
        talons_[wheel]->GetSelectedSensorPosition() / cfg_.enc_counts_per_rev;

    // converts counts/100ms to rad/s
    wheel_velocities_[wheel] = talons_[wheel]->GetSelectedSensorVelocity() *
                               (10.0 / cfg_.enc_counts_per_rev);
  };

  return hardware_interface::return_type::OK;
}
hardware_interface::return_type DriveSystem::write(const rclcpp::Time &,
                                                   const rclcpp::Duration &dt) {

  ctre::phoenix::unmanaged::Unmanaged::FeedEnable(cfg_.loop_rate * 1.15);

  double command = 0.0;
  for (size_t wheel = FL; wheel < LAST; wheel++) {
    if (wheel == 999) {
      command = pid_.computeCommand(wheel_velocity_command_[wheel] -
                                        wheel_velocities_[wheel],
                                    (u_int64_t)dt.nanoseconds());
      RCLCPP_INFO(rclcpp::get_logger("DriveSystem"), "Error: %.3f",
                  wheel_velocity_command_[wheel] - wheel_velocities_[wheel]);
      RCLCPP_INFO(rclcpp::get_logger("DriveSystem"), "Cmd: %.3f",
                  pid_.getCurrentCmd());
      RCLCPP_INFO(rclcpp::get_logger("DriveSystem"), "Dur: %d",
                  (int)dt.nanoseconds());
      RCLCPP_INFO(rclcpp::get_logger("DriveSystem"), "K_p: %.3f",
                  pid_.getGains().p_gain_);
      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput,
          command / 20);
    } else {
      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput,
          wheel_velocity_command_[wheel] * (0.8/11.9));
    }
  }

  return hardware_interface::return_type::OK;
}
}; // namespace chassis_controls

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem,
                       hardware_interface::SystemInterface)
