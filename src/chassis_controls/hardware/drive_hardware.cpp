#include "include/chassis_controls/drive_hardware.hpp"
#include "ctre/phoenix/motorcontrol/ControlMode.h"
#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#include "ctre/phoenix/unmanaged/Unmanaged.h"
#include <control_toolbox/pid.hpp>
#include <hardware_interface/system_interface.hpp>
#include <memory>
#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <string>

namespace chassis_controls {

/**
 * @brief Initializes the DriveSystem lifecycle node.
 *
 * Parses the URDF, extractacting xacro arguments. Initializes all class
 * attributes, brings up Talon objects and PIDs.
 *
 * @param info data contained in xacro file (URDF + macros + args + ros2
 * control)
 * @return Success flag if no errors during initialization, failure flag if
 * executition fails.
 */
CallbackReturn
DriveSystem::on_init(const hardware_interface::HardwareInfo &info) {

  if (hardware_interface::SystemInterface::on_init(info) !=
      CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  wheel_position_.assign(4, 0);
  wheel_velocities_.assign(4, 0);
  wheel_velocity_command_.assign(4, 0);

  for (const auto &joint : info_.joints) {
    for (const auto &interface : joint.state_interfaces) {
      joint_interfaces[interface.name].push_back(joint.name);
    }
  }

  cfg_.wheel_circumference =
      std::stod(info_.hardware_parameters["wheel_diameter"]) * M_PI;
  cfg_.max_velocity =
      std::stod(info_.hardware_parameters["wheel_max_velocity"]);
  cfg_.enc_counts_per_rev =
      std::stoi(info_.hardware_parameters["wheel_enc_counts_per_rev"]);
  cfg_.controller_period =
      std::stod(info_.hardware_parameters["controller_period"]);

  talons_.reserve(4);
  talons_[FL] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(
      std::stoi(info_.hardware_parameters["FL_id"]));
  talons_[FR] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(
      std::stoi(info_.hardware_parameters["FR_id"]));
  talons_[RR] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(
      std::stoi(info_.hardware_parameters["RR_id"]));
  talons_[RL] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(
      std::stoi(info_.hardware_parameters["RL_id"]));

  pids_.reserve(4);
  pids_[RL] = std::make_shared<control_toolbox::Pid>();
  pids_[RR] = std::make_shared<control_toolbox::Pid>();

  return CallbackReturn::SUCCESS;
}

/**
 * @brief Configures the DriveSystem lifecycle node.
 *
 * Configures hardware by aligning motor and encoder phase with system,
 * configuring sensors, and zero-ing relative position encoders.
 *
 * @param previous_state UNCONFIGURED, hardware progresses to INACTIVE once this
 * method executes successfully.
 * @return Success flag if no errors during configuration, failure flag if
 * executition fails.
 */
hardware_interface::CallbackReturn
DriveSystem::on_activate(const rclcpp_lifecycle::State & /*previous_state*/) {
  talons_[FR]->SetInverted(true);

  int err;
  for (const auto &wheel : talons_) {
    err = (int)wheel->ConfigSelectedFeedbackSensor(
        ctre::phoenix::motorcontrol::FeedbackDevice::CTRE_MagEncoder_Relative,
        0, 100);
    wheel->SetSelectedSensorPosition(0.0);

    if (err) {
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  talons_[RL]->SetSensorPhase(true);

  pids_[RL]->initPid(1.0, 0.0, 0.0, 0.5, -0.5, true);
  pids_[RR]->initPid(1.0, 0.0, 0.0, 0.5, -0.5, true);

  return hardware_interface::CallbackReturn::SUCCESS;
};

/**
 * @brief Exports state interfaces: wheel position and velocity.
 *
 * StateInterfaces are created and ownership is transferred to caller (Joint
 * State Broadcaster)
 *
 * @returns std::vector<hardware_interface::StateInterface> Vector of size 2,
 * containing velocit and position state interfaces
 */
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

/**
 * @brief Exports command interface: wheel velocity.
 *
 * CommandInterface is created and ownership is transferred to caller
 * (diff_cont)
 *
 * @returns std::vector<hardware_interface::CommandInterface> Vector of size
 * 1, containing velocit command interface
 */
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

/**
 * @brief Read latest wheel positions and velocities over CAN.
 *
 * Converts encoder data in encoder counts, given a sample period of 100ms, to
 * position [rad] and velocity [rad/s] in units that agree with diff_cont.
 *
 * @returns OK flag if successful read, ERROR flag if read failed.
 */
hardware_interface::return_type DriveSystem::read(const rclcpp::Time &,
                                                  const rclcpp::Duration &) {

  for (size_t wheel = FL; wheel < LAST; wheel++) {
    switch (wheel) {
    case RL: {
      wheel_position_[wheel] =
          talons_[wheel]->GetSelectedSensorPosition() / cfg_.enc_counts_per_rev;
      wheel_velocities_[wheel] =
          talons_[wheel]->GetSelectedSensorVelocity() /
          (cfg_.controller_period * cfg_.enc_counts_per_rev);
    } break;

    case FR: {
      wheel_position_[wheel] = wheel_position_[RR];
      wheel_velocities_[wheel] = wheel_velocities_[RR];
    } break;

    case RR: {
      wheel_position_[wheel] =
          talons_[wheel]->GetSelectedSensorPosition() / cfg_.enc_counts_per_rev;
      wheel_velocities_[wheel] =
          talons_[wheel]->GetSelectedSensorVelocity() /
          (cfg_.controller_period * cfg_.enc_counts_per_rev);
    } break;

    case FL: {
      wheel_position_[wheel] = wheel_position_[RL];
      wheel_velocities_[wheel] = wheel_velocities_[RL];
    } break;
    }
  };

  return hardware_interface::return_type::OK;
}

/**
 * @brief Write commanded wheel velocities over CAN.
 *
 * Perform PID control on each wheel from commanded values and latest state.
 * Send PWM command to motors according to to latest value. Handles unit
 * conversion from rad/s to pwm as a % of free wheel velocity.
 *
 * @params dt duration since last write command.
 * @returns OK flag if successful write, ERROR flag if write failed.
 */
hardware_interface::return_type DriveSystem::write(const rclcpp::Time &,
                                                   const rclcpp::Duration &dt) {
  u_int64_t period = dt.nanoseconds();
  ctre::phoenix::unmanaged::Unmanaged::FeedEnable(period);

  for (size_t wheel = FL; wheel < LAST; wheel++) {
    double error = wheel_velocity_command_[wheel] - wheel_velocities_[wheel];

    switch (wheel) {
    case RL: {
      double command = pids_[wheel]->computeCommand(error, period);
      double pwm = command / cfg_.max_velocity;

      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput, pwm);
    } break;

    case FR: {
      talons_[wheel]->Set(
         ctre::phoenix::motorcontrol::TalonSRXControlMode::Follower,
         talons_[RR]->GetDeviceID());
    } break;

    case RR: {
      double command = pids_[wheel]->computeCommand(error, period);
      double pwm = command / cfg_.max_velocity;

      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput, pwm);
    } break;

    case FL: {
      talons_[wheel]->Set(
        ctre::phoenix::motorcontrol::TalonSRXControlMode::Follower,
        talons_[RL]->GetDeviceID());
    } break;
    }
  }
  return hardware_interface::return_type::OK;
}

}; // namespace chassis_controls

/**
 * Exports class via pluginlib so it may be used by diff_cont
 */
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem,
                       hardware_interface::SystemInterface)
