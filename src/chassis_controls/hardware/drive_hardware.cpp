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

  testing_ = std::stoi(info_.hardware_parameters["testing"]);
  tested_pwm_ = std::stod(info_.hardware_parameters["tested_pwm"]);

  if (!testing_) {
    tested_pwm_ = 0.0;
  }

  RCLCPP_INFO(logger_, "!!! Testing at: %f%% PWM. !!!", tested_pwm_);

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
  cfg_.wheel_m = {0.27291033895945316, 0.2730788189594534, 0.28206923374321247,
                  0.27404910467374133};
  cfg_.wheel_b = {-1.295702995675999, -1.3075589956760272, -1.5866751633510998,
                  -1.528822567105082};

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
  pids_[FL] = std::make_shared<control_toolbox::Pid>();
  pids_[FR] = std::make_shared<control_toolbox::Pid>();

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

  pids_[RL]->initPid(0.002342, 3.4953e-6, 0.42913, 0.5, -0.5, true);
  pids_[FL]->initPid(0.0078556, 2.349e-5, 0.65679, 0.5, -0.5, true);
  pids_[FR]->initPid(1.0, 0.0, 0.0, 0.5, -0.5, true);
  pids_[RR]->initPid(0.00096076, 7.7315e-7, 0.29847, 0.5, -0.5, true);

  // talons_[RL]->SetSensorPhase(true);

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
    wheel_position_[wheel] =
        talons_[wheel]->GetSelectedSensorPosition() / cfg_.enc_counts_per_rev;
    wheel_velocities_[wheel] =
        talons_[wheel]->GetSelectedSensorVelocity() /
        (cfg_.controller_period * cfg_.enc_counts_per_rev);

    RCLCPP_INFO(logger_, "!!! Wheel feedback: %zu !!!", wheel);
    RCLCPP_INFO(logger_, "!!! Wheel velocity: %f !!!",
                wheel_velocities_[wheel]);
    RCLCPP_INFO(logger_, "!!! Wheel current consumption: %f !!!",
                talons_[wheel]->GetOutputCurrent());
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
    double velocity_command = pids_[wheel]->computeCommand(error, period);
    double pwm_command = velocity_to_pwm(velocity_command, wheel);
    double pwm_magnitude = abs(pwm_command);
    double clamped_pwm_magnitude =
        std::clamp(pwm_magnitude, get_x_intercept(wheel), 100.0);

    double pwm_output = 0;
    if (pwm_command >= 0) {
      pwm_output = clamped_pwm_magnitude;
    } else {
      pwm_output = clamped_pwm_magnitude * -1;
    }

    if (testing_) {
      pwm_output = tested_pwm_ / 100;
    }

    if (wheel != FR) {
      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput,
          pwm_output);
    } else {
      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::Follower, 10);
    }
  }

  return hardware_interface::return_type::OK;
}

double DriveSystem::pwm_to_velocity(double pwm, size_t wheel) {
  double slope = cfg_.wheel_m[wheel];
  double y_intercept = cfg_.wheel_b[wheel];
  double velocity = pwm * slope + y_intercept;
  return velocity;
}

double DriveSystem::velocity_to_pwm(double velocity, size_t wheel) {
  double slope = cfg_.wheel_m[wheel];
  double y_intercept = cfg_.wheel_b[wheel];
  double pwm = (velocity - y_intercept) / slope;
  return pwm;
}

double DriveSystem::get_x_intercept(size_t wheel) {
  double slope = cfg_.wheel_m[wheel];
  double y_intercept = cfg_.wheel_b[wheel];
  double x_intercept = -1 * y_intercept / slope;
  return x_intercept;
}

}; // namespace chassis_controls

/**
 * Exports class via pluginlib so it may be used by diff_cont
 */
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem,
                       hardware_interface::SystemInterface)
