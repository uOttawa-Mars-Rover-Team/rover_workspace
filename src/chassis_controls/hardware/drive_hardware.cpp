#include "hardware_interface/system_interface.hpp"
#include <rclcpp/logger.hpp>
#include <rclcpp_lifecycle/state.hpp>
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

  read_rate_ = 30;
  update_rate_ = 50;

  counts_per_rotation_ = 4096;
  talon_period_ = 0.1;
  gear_ratio_ = 1.0 / 25;
  wheel_circumference_ = 1.436;

  // assign controllers by CANid
  talons_.assign(4, 0);
  talons_[FL] = new ctre::phoenix::motorcontrol::can::TalonSRX(20);
  talons_[FR] = new ctre::phoenix::motorcontrol::can::TalonSRX(10);
  talons_[RR] = new ctre::phoenix::motorcontrol::can::TalonSRX(40);
  talons_[RL] = new ctre::phoenix::motorcontrol::can::TalonSRX(30);

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
  talons_[FR]->SetInverted(true);

  int err;
  for (size_t wheel = FL; wheel < LAST; wheel++) {
    err = (int)talons_[wheel]->ConfigSelectedFeedbackSensor(
        ctre::phoenix::motorcontrol::FeedbackDevice::CTRE_MagEncoder_Relative,
        0, 100);

    talons_[wheel]->SetSelectedSensorPosition(0.0);
    /*talons_[wheel]->Config_kI(0,0.0);
    talons_[wheel]->Config_kP(0,0.0);
    talons_[wheel]->Config_kF(0,4096);
    talons_[wheel]->Config_kD(0,0.0);*/
    if (err) {
      return hardware_interface::CallbackReturn::ERROR;
    }
  }
  talons_[FL]->SetSensorPhase(true);

  return hardware_interface::CallbackReturn::SUCCESS;
};

hardware_interface::return_type DriveSystem::read(const rclcpp::Time &,
                                                  const rclcpp::Duration &) {

  for (size_t wheel = FL; wheel < LAST; wheel++) {
    wheel_position_[wheel] =
        talons_[wheel]->GetSelectedSensorPosition() / counts_per_rotation_;
    wheel_velocities_[wheel] = gear_ratio_ *
                               talons_[wheel]->GetSelectedSensorVelocity() *
                               talon_period_ / 1.17;
  };

  return hardware_interface::return_type::OK;
}
hardware_interface::return_type DriveSystem::write(const rclcpp::Time &,
                                                   const rclcpp::Duration &) {

  ctre::phoenix::unmanaged::Unmanaged::FeedEnable(update_rate_ * 1.15);

  for (size_t wheel = FL; wheel < LAST; wheel++) {
    talons_[wheel]->Set(
        ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput, wheel_velocity_command_[wheel]/1000);
        //0.1*counts_per_rotation_ * wheel_velocity_command_[wheel] / (gear_ratio_* wheel_circumference_));
  }

  return hardware_interface::return_type::OK;
}
}; // namespace chassis_controls

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem,
                       hardware_interface::SystemInterface)
