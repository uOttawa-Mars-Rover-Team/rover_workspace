#include "include/chassis_controls/drive_hardware.hpp"
#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"

namespace chassis_controls {
CallbackReturn
DriveSystem::on_init(const hardware_interface::HardwareInfo &info) {

  // parse URDF
  if (hardware_interface::SystemInterface::on_init(info) !=
      CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // assign controllers by CANid
  front_right_ = new ctre::phoenix::motorcontrol::can::TalonSRX(10);
  front_left_ = new ctre::phoenix::motorcontrol::can::TalonSRX(20);
  rear_right_ = new ctre::phoenix::motorcontrol::can::TalonSRX(40);
  rear_left_ = new ctre::phoenix::motorcontrol::can::TalonSRX(30);

  // inverted motor
  front_right_->SetInverted(true);

  // bring up sensors
  front_left_->ConfigSelectedFeedbackSensor(
      FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
  front_right_->ConfigSelectedFeedbackSensor(
      FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
  rear_right_->ConfigSelectedFeedbackSensor(
      FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
  rear_left_->ConfigSelectedFeedbackSensor(
      FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);

  // interfaces:
  wheel_position_.assign(4, 0);
  wheel_velocities_.assign(4, 0);
  wheel_velocity_command_.assign(4, 0);

  for (const auto &joint : info_.joints) {
    for (const auto &interface : joint.state_interfaces) {
      joint_interfaces[interface.name].push_back(joint.name);
    }
  }

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
hardware_interface::return_type DriveSystem::read(const rclcpp::Time &,
                                                  const rclcpp::Duration &) {
  for (size_t i = 0; i < wheel_velocity_command_.size(); i++){
      wheel_velocities_[i] = wheel_velocity_command_[i];
  }
  return hardware_interface::return_type::OK;
}
hardware_interface::return_type DriveSystem::write(const rclcpp::Time &,
                                                   const rclcpp::Duration &) {
  return hardware_interface::return_type::OK;
}
}; // namespace chassis_controls

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem,
                       hardware_interface::SystemInterface)
