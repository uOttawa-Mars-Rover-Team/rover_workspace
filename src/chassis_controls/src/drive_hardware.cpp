#include "chassis_controls/drive_hardware.hpp"
#include "ctre/phoenix/motorcontrol/ControlMode.h"
#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#include "ctre/phoenix/unmanaged/Unmanaged.h"
#include <hardware_interface/system_interface.hpp>
#include <memory>
#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <string>
#include <math.h>
#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace chassis_controls
{

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
  CallbackReturn DriveSystem::on_init(const hardware_interface::HardwareComponentInterfaceParams &params)
  {
    RCLCPP_INFO(logger_, "Configuring Hardware Interface...");
    if (hardware_interface::SystemInterface::on_init(params) != CallbackReturn::SUCCESS)
    {
      return CallbackReturn::ERROR;
    }

    info_ = params.hardware_info;

    // Read configured values
    // -- PID gains
    config_.pid_gains[FL].Kp = std::stod(info_.hardware_parameters["Kp_FL"]);
    config_.pid_gains[FL].Ki = std::stod(info_.hardware_parameters["Ki_FL"]);
    config_.pid_gains[FL].Kd = std::stod(info_.hardware_parameters["Kd_FL"]);
    config_.pid_gains[FR].Kp = std::stod(info_.hardware_parameters["Kp_FR"]);
    config_.pid_gains[FR].Ki = std::stod(info_.hardware_parameters["Ki_FR"]);
    config_.pid_gains[FR].Kd = std::stod(info_.hardware_parameters["Kd_FR"]);
    config_.pid_gains[RR].Kp = std::stod(info_.hardware_parameters["Kp_RR"]);
    config_.pid_gains[RR].Ki = std::stod(info_.hardware_parameters["Ki_RR"]);
    config_.pid_gains[RR].Kd = std::stod(info_.hardware_parameters["Kd_RR"]);
    config_.pid_gains[RL].Kp = std::stod(info_.hardware_parameters["Kp_RL"]);
    config_.pid_gains[RL].Ki = std::stod(info_.hardware_parameters["Ki_RL"]);
    config_.pid_gains[RL].Kd = std::stod(info_.hardware_parameters["Kd_RL"]);
    // -- Wheel diameter and circumference
    const double wheel_diameter = std::stod(info_.hardware_parameters["wheel_diameter"]);
    config_.wheel_circumference = wheel_diameter * M_PI;
    if (wheel_diameter <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid wheel_diameter!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "wheel_diameter is %f.", wheel_diameter);
    }
    // -- Wheel encoder counts per revolution
    config_.wheel_encoder_counts_per_revolution = std::stoi(info_.hardware_parameters["wheel_encoder_counts_per_revolution"]);
    if (config_.wheel_encoder_counts_per_revolution <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid wheel_encoder_counts_per_revolution!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "wheel_encoder_counts_per_revolution is %d.", config_.wheel_encoder_counts_per_revolution);
    }
    // -- Talons
    const int FL_id = std::stoi(info_.hardware_parameters["FL_id"]);
    if (FL_id <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid FL_id!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "FL_id is %d.", FL_id);
      talons_[FL] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(FL_id);
    }
    const int FR_id = std::stoi(info_.hardware_parameters["FR_id"]);
    if (FR_id <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid FR_id!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "FR_id is %d.", FR_id);
      talons_[FR] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(FR_id);
    }
    const int RR_id = std::stoi(info_.hardware_parameters["RR_id"]);
    if (RR_id <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid RR_id!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "RR_id is %d.", RR_id);
      talons_[RR] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(RR_id);
    }
    const int RL_id = std::stoi(info_.hardware_parameters["RL_id"]);
    if (RL_id <= 0)
    {
      RCLCPP_ERROR(logger_, "Invalid RL_id!");
      return CallbackReturn::ERROR;
    }
    else
    {
      RCLCPP_INFO(logger_, "RL_id is %d.", RL_id);
      talons_[RL] = std::make_shared<ctre::phoenix::motorcontrol::can::TalonSRX>(RL_id);
    }

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
  DriveSystem::on_activate(const rclcpp_lifecycle::State & /*previous_state*/)
  {
    int PIDLoopIdx = 0;
    int timeoutMs = 100;

    // Send some initial data over CAN to the motor controllers to allow it
    // to detect the CAN bus and prevent errors
    talons_[FL]->ConfigSelectedFeedbackSensor(
          ctre::phoenix::motorcontrol::FeedbackDevice::CTRE_MagEncoder_Relative,
          0,
          timeoutMs);

    int err;
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      err = 0;
      err |= (int)talons_[wheel]->ConfigFactoryDefault();
      // Nominal output (default output (?)) should be 0
      err |= (int)talons_[wheel]->ConfigNominalOutputForward(0, timeoutMs);
      err |= (int)talons_[wheel]->ConfigNominalOutputReverse(0, timeoutMs);
      // Set peak output to its maximum value
      err |= (int)talons_[wheel]->ConfigPeakOutputForward(1, timeoutMs);
      err |= (int)talons_[wheel]->ConfigPeakOutputReverse(-1, timeoutMs);
      err |= (int)talons_[wheel]->ConfigSelectedFeedbackSensor(
          ctre::phoenix::motorcontrol::FeedbackDevice::CTRE_MagEncoder_Relative,
          0,
          timeoutMs);
      // Configure PID gains on the Talons
      err |= (int)talons_[wheel]->Config_kF(PIDLoopIdx, 0.0, timeoutMs);
      err |= (int)talons_[wheel]->Config_kP(PIDLoopIdx, config_.pid_gains[wheel].Kp, timeoutMs);
      err |= (int)talons_[wheel]->Config_kI(PIDLoopIdx, config_.pid_gains[wheel].Ki, timeoutMs);
      err |= (int)talons_[wheel]->Config_kD(PIDLoopIdx, config_.pid_gains[wheel].Kd, timeoutMs);

      if (err)
      {
        RCLCPP_ERROR(logger_, "Failed when setting up wheel %s!", wheel_names_[wheel].c_str());
        return CallbackReturn::ERROR;
      }
    }

    talons_[FR]->SetInverted(true);
    talons_[RR]->SetInverted(true);

    talons_[FR]->SetSensorPhase(true);
    talons_[FL]->SetSensorPhase(true);
    talons_[RL]->SetSensorPhase(true);
    talons_[RR]->SetSensorPhase(true);

    return hardware_interface::CallbackReturn::SUCCESS;
  };

  /**
   * @brief Exports state interfaces: wheel position and velocity.
   *
   * StateInterfaces are created and ownership is transferred to caller (Joint
   * State Broadcaster)
   *
   * @returns std::vector<hardware_interface::StateInterface> Vector of size 2,
   * containing velocity and position state interfaces
   */
  std::vector<hardware_interface::StateInterface>
  DriveSystem::export_state_interfaces()
  {
    std::vector<hardware_interface::StateInterface> state_interfaces;

    for (std::size_t i = 0; i < info_.joints.size(); i++)
    {
      state_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_POSITION, &wheel_positions_[i]);
      state_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &wheel_velocities_[i]);
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
  DriveSystem::export_command_interfaces()
  {
    std::vector<hardware_interface::CommandInterface> command_interfaces;

    for (std::size_t i = 0; i < info_.joints.size(); i++)
    {
      command_interfaces.emplace_back(info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &wheel_command_velocities_[i]);
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
  hardware_interface::return_type DriveSystem::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*dt*/)
  {
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      // Position
      const double wheel_encoder_counts = talons_[wheel]->GetSelectedSensorPosition();
      wheel_positions_[wheel] = revolutions_to_radians(
          wheel_encoder_counts / config_.wheel_encoder_counts_per_revolution);

      // Velocity
      // GetSelectedSensorVelocity() is reported in encoder counts / 100ms. Convert this value to encoder counts / second
      const double wheel_encoder_counts_per_s = talons_[wheel]->GetSelectedSensorVelocity() / talon_srx_update_period_;
      const double wheel_revolutions_per_s = wheel_encoder_counts_per_s / config_.wheel_encoder_counts_per_revolution;
      const double wheel_rads_per_s = revolutions_to_radians(wheel_revolutions_per_s);
      wheel_velocities_[wheel] = wheel_rads_per_s;

      // Logging
      const std::string wheel_name = wheel_names_[wheel];
      RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "%s wheel velocity: %f m/s (%f rad/s).", wheel_name.c_str(), wheel_revolutions_per_s * config_.wheel_circumference, wheel_rads_per_s);
      RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "%s wheel current consumption: %f.", wheel_name.c_str(), talons_[wheel]->GetStatorCurrent());
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
  hardware_interface::return_type DriveSystem::write(const rclcpp::Time & /*time*/, const rclcpp::Duration &dt)
  {
    // Enable the Talon actuators (?) for more time
    u_int64_t period = dt.nanoseconds();
    ctre::phoenix::unmanaged::Unmanaged::FeedEnable(period);

    // Zeroing out: Because this drive code operates in closed loop mode, it
    // can cause the rover to draw a lot of current without actually moving. For example, if the rover
    // is on the decline of a hill, (if positioned correctly) it would roll down the hill if the drive
    // code wasn't running (similar to a car in Neutral (N) on a hill). However, if the rover is on the
    // hill's decline and the drive code
    // IS running and the target (commanded) velocity is 0, the motors will be powered to provide enough torque to
    // counteract the force rolling the rover down the hill; the closed loop drive code will draw power
    // to keep the wheels not spinning to match the 0 target velocity.
    //
    // This effect works similarly when the rover is mid-turn and is suddenly commanded 0. When it's
    // turning on the spot, it starts to draw a lot of current to counteract the force of friction. This
    // power draw would build up to the point where it would be sufficient to
    // allow for the wheels to counteract the force of friction enough and spin fast enough (since there is
    // some skidding) to make the rover
    // spin in place. However, if the rover was commanded to turn in place but then it was suddenly commanded
    // 0, it would start to draw current and the wheels would slowly start to turn, but when commanded 0,
    // the closed loop
    // system would keep drawing the same amount of current as before it was commanded 0 to keep the wheels from
    // spinning any further (0 velocity). This is because right before the drive system was commanded 0,
    // the motors were drawing a moderate amount of current to try to overcome  inertia/static-friction.
    // This current draw wasn't enough to actually turn the wheels properly, but it is a decent amount.
    // If suddenly commanded 0, it would keep drawing that current amount to keep the wheels/motors from going
    // back to their "rest position", where no effort is being made against inertia/static-friction.
    //
    // To prevent this excessive current draw, we can "zero out" the system when it's at 0 velocity and is being
    // commanded 0 velocity, allowing for 1 "write cycle" of
    // PWM control (at 0 PWM). Since the PWM system is non-closed-loop, it allows for the wheels/motors to
    // ease up and reach their rest position, after which the closed loop control system can take over.
    //
    // If we're commanding 0 velocity and our actual velocity is actually 0 but
    // we haven't actually zeroed out so far (i.e. the zeroed_out flag is false),
    // then command 0% PWM and set the zeroed_out flag to true to indicate we've
    // zeroed out.
    static bool zeroed_out = false;
    bool wheels_are_stopped = true;
    bool commanding_all_zero = true;
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      wheels_are_stopped = wheels_are_stopped && wheel_velocities_[wheel] == 0;
      commanding_all_zero = commanding_all_zero && wheel_command_velocities_[wheel] == 0;
    }
    if (!zeroed_out && wheels_are_stopped && commanding_all_zero)
    {
      for (size_t wheel = FL; wheel < LAST; wheel++)
      {
        talons_[wheel]->Set(
            ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput, 0);
      }
      zeroed_out = true;
      RCLCPP_INFO(logger_, "ZEROING OUT!!!\n");
      return hardware_interface::return_type::OK;
    }
    // Once we start moving again, turn off the zeroed_out flag to indicate that we're open to zeroing
    // out again as soon as we stop (0 commanded and actual velocity)
    if (!commanding_all_zero)
    {
      zeroed_out = false;
    }

    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      const double wheel_cmd_rads_per_s = wheel_command_velocities_[wheel];
      const double wheel_cmd_revolutions_per_s = radians_to_revolutions(wheel_cmd_rads_per_s);
      const double wheel_cmd_encoder_counts_per_s = wheel_cmd_revolutions_per_s * config_.wheel_encoder_counts_per_revolution;
      const double wheel_cmd_encoder_counts_per_update_period = wheel_cmd_encoder_counts_per_s * talon_srx_update_period_;
      talons_[wheel]->Set(
          ctre::phoenix::motorcontrol::TalonSRXControlMode::Velocity, wheel_cmd_encoder_counts_per_update_period);

      RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "Asking to command: %f m/s (%f rad/s) on wheel %s.\n", wheel_cmd_revolutions_per_s * config_.wheel_circumference, wheel_cmd_rads_per_s, wheel_names_[wheel].c_str());
    }

    return hardware_interface::return_type::OK;
  }

}; // namespace chassis_controls

/**
 * Exports class via pluginlib so it may be used by diff_cont
 */
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem, hardware_interface::SystemInterface)
