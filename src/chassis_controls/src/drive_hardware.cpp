#include "chassis_controls/drive_hardware.hpp"
#include <algorithm>
#include <cmath>
#include <hardware_interface/system_interface.hpp>
#include <limits>
#include <memory>
#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp_lifecycle/state.hpp>
#include <sstream>
#include <stdexcept>
#include <string>
#include "hardware_interface/types/hardware_interface_type_values.hpp"

namespace chassis_controls
{
  using namespace mjbots;

  /**
   * @brief Initializes the DriveSystem lifecycle node.
   *
   * Parses the URDF, extracting the xacro arguments: moteus CAN ids, gear
   * ratio and the velocity/torque limits.
   *
   * @param params data contained in xacro file (URDF + macros + args + ros2
   * control)
   * @return Success flag if no errors during initialization, failure flag if
   * execution fails.
   */
  CallbackReturn DriveSystem::on_init(const hardware_interface::HardwareComponentInterfaceParams &params)
  {
    RCLCPP_INFO(logger_, "Configuring Hardware Interface...");
    if (hardware_interface::SystemInterface::on_init(params) != CallbackReturn::SUCCESS)
    {
      return CallbackReturn::ERROR;
    }

    info_ = params.hardware_info;

    if (info_.joints.size() != wheel_count)
    {
      RCLCPP_ERROR(logger_, "Expected %zu joints, got %zu!", wheel_count, info_.joints.size());
      return CallbackReturn::ERROR;
    }

    try
    {
      // -- moteus CAN ids
      for (size_t wheel = FL; wheel < LAST; wheel++)
      {
        const std::string param = wheel_names_[wheel] + "_id";
        const int id = std::stoi(info_.hardware_parameters.at(param));
        if (id < 1 || id > 126)
        {
          RCLCPP_ERROR(logger_, "Invalid %s (%d), moteus ids are 1-126!", param.c_str(), id);
          return CallbackReturn::ERROR;
        }
        RCLCPP_INFO(logger_, "%s is %d.", param.c_str(), id);
        config_.ids[wheel] = id;
      }

      // -- Gear ratio and limits
      config_.gear_ratio = std::stod(info_.hardware_parameters.at("gear_ratio"));
      config_.max_velocity = std::stod(info_.hardware_parameters.at("max_velocity"));
      config_.max_torque = std::stod(info_.hardware_parameters.at("max_torque"));

      // -- Transport arguments (optional, whitespace separated). "auto" lets
      // the moteus library detect the CAN-FD adapter.
      const auto transport_args = info_.hardware_parameters.find("transport_args");
      if (transport_args != info_.hardware_parameters.end() && transport_args->second != "auto")
      {
        std::istringstream stream(transport_args->second);
        std::string arg;
        while (stream >> arg)
        {
          config_.transport_args.push_back(arg);
        }
      }
    }
    catch (const std::exception &e)
    {
      RCLCPP_ERROR(logger_, "Missing or invalid hardware parameter: %s", e.what());
      return CallbackReturn::ERROR;
    }

    if (config_.gear_ratio <= 0 || config_.max_velocity <= 0 || config_.max_torque <= 0)
    {
      RCLCPP_ERROR(logger_, "gear_ratio, max_velocity and max_torque must all be positive!");
      return CallbackReturn::ERROR;
    }
    RCLCPP_INFO(logger_, "gear_ratio is %f, max_velocity is %f rev/s, max_torque is %f Nm.",
                config_.gear_ratio, config_.max_velocity, config_.max_torque);

    // Velocity control: position is left as NaN and the torque limit is sent
    // with every command, so it has to be enabled in the command format.
    position_format_.maximum_torque = moteus::kFloat;

    echo_node_ = std::make_shared<rclcpp::Node>("moteus_drive_command_echo");
    command_echo_pub_ = echo_node_->create_publisher<sensor_msgs::msg::JointState>("/moteus_cmd_echo", 10);

    return CallbackReturn::SUCCESS;
  }

  /**
   * @brief Activates the DriveSystem lifecycle node.
   *
   * Opens the CAN-FD transport (fdcanusb or socketcan) and sends a stop to
   * every moteus, which clears any latched fault and reads the initial state.
   *
   * @return Success flag if the transport could be opened, failure flag
   * otherwise.
   */
  hardware_interface::CallbackReturn
  DriveSystem::on_activate(const rclcpp_lifecycle::State & /*previous_state*/)
  {
    try
    {
      transport_ = moteus::Controller::MakeSingletonTransport(config_.transport_args);
    }
    catch (const std::exception &e)
    {
      RCLCPP_ERROR(logger_, "Could not open a moteus transport: %s", e.what());
      return CallbackReturn::ERROR;
    }

    std::vector<moteus::CanFdFrame> frames;
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      moteus::Controller::Options options;
      options.id = config_.ids[wheel];
      options.transport = transport_;
      controllers_[wheel] = std::make_shared<moteus::Controller>(options);
      frames.push_back(controllers_[wheel]->MakeStop());
    }

    try
    {
      cycle(frames);
    }
    catch (const std::exception &e)
    {
      RCLCPP_ERROR(logger_, "Failed to talk to the moteus controllers: %s", e.what());
      return CallbackReturn::ERROR;
    }

    wheel_command_velocities_.fill(0.0);
    zeroed_out_ = false;

    return hardware_interface::CallbackReturn::SUCCESS;
  };

  /**
   * @brief Deactivates the DriveSystem lifecycle node, stopping every motor.
   */
  hardware_interface::CallbackReturn
  DriveSystem::on_deactivate(const rclcpp_lifecycle::State & /*previous_state*/)
  {
    std::vector<moteus::CanFdFrame> frames;
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      frames.push_back(controllers_[wheel]->MakeStop());
    }

    try
    {
      cycle(frames);
    }
    catch (const std::exception &e)
    {
      RCLCPP_ERROR(logger_, "Failed to stop the moteus controllers: %s", e.what());
      return CallbackReturn::ERROR;
    }

    return hardware_interface::CallbackReturn::SUCCESS;
  }

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
   * @brief Sends one frame per wheel and updates wheel states from the replies.
   *
   * Every moteus command carries a query, so each reply holds the latest
   * position [motor rev] and velocity [motor rev/s]. These are converted to
   * wheel position [rad] and velocity [rad/s], in units that agree with
   * diff_cont.
   */
  void DriveSystem::cycle(std::vector<moteus::CanFdFrame> &frames)
  {
    std::vector<moteus::CanFdFrame> replies;
    transport_->BlockingCycle(frames.data(), frames.size(), &replies);

    std::array<bool, wheel_count> replied = {false, false, false, false};
    for (const auto &frame : replies)
    {
      for (size_t wheel = FL; wheel < LAST; wheel++)
      {
        if (frame.source != config_.ids[wheel])
        {
          continue;
        }
        replied[wheel] = true;

        const auto result = moteus::Query::Parse(frame.data, frame.size);
        if (std::isfinite(result.position))
        {
          wheel_positions_[wheel] = revolutions_to_radians(
              wheel_signs_[wheel] * result.position / config_.gear_ratio);
        }
        if (std::isfinite(result.velocity))
        {
          wheel_velocities_[wheel] = revolutions_to_radians(
              wheel_signs_[wheel] * result.velocity / config_.gear_ratio);
        }

        if (result.mode == moteus::Mode::kFault || result.mode == moteus::Mode::kPositionTimeout)
        {
          RCLCPP_ERROR_THROTTLE(logger_, clock_, log_period_ms_,
                                "%s moteus is in mode %d with fault %d. It is cleared the next time the rover is stopped.",
                                wheel_names_[wheel].c_str(), static_cast<int>(result.mode), static_cast<int>(result.fault));
        }
        RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "%s wheel velocity: %f rad/s, motor torque: %f Nm.",
                             wheel_names_[wheel].c_str(), wheel_velocities_[wheel], result.torque);
      }
    }

    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      if (!replied[wheel])
      {
        RCLCPP_WARN_THROTTLE(logger_, clock_, log_period_ms_, "No reply from %s moteus (id %d).",
                             wheel_names_[wheel].c_str(), config_.ids[wheel]);
      }
    }
  }

  /**
   * @brief Publishes the commands just sent to the moteus controllers.
   *
   * Published on /moteus_cmd_echo as a JointState, one entry per wheel joint:
   * position is NaN (velocity control), velocity is the commanded motor
   * velocity [rev/s] and effort is the torque limit [Nm].
   */
  void DriveSystem::publish_command_echo(const std::array<double, wheel_count> &velocities, double torque)
  {
    sensor_msgs::msg::JointState msg;
    msg.header.stamp = echo_node_->now();
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      msg.name.push_back(info_.joints[wheel].name);
      msg.position.push_back(std::numeric_limits<double>::quiet_NaN());
      msg.velocity.push_back(velocities[wheel]);
      msg.effort.push_back(torque);
    }
    command_echo_pub_->publish(msg);
  }

  /**
   * @brief Wheel states are refreshed from the replies to each write().
   *
   * A moteus answers every command with its latest position and velocity, so
   * no separate query is sent here.
   *
   * @returns OK flag.
   */
  hardware_interface::return_type DriveSystem::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*dt*/)
  {
    return hardware_interface::return_type::OK;
  }

  /**
   * @brief Write commanded wheel velocities over CAN.
   *
   * Converts the commanded wheel velocity [rad/s] to motor velocity [rev/s],
   * limits it to max_velocity and sends it as a moteus velocity command with
   * the max_torque limit. The velocity loop itself runs on the moteus.
   *
   * @returns OK flag if successful write, ERROR flag if write failed.
   */
  hardware_interface::return_type DriveSystem::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*dt*/)
  {
    // Zeroing out: a closed loop velocity command of 0 makes the motors hold
    // their position, so any torque that built up while stopping (on a slope,
    // or when a turn on the spot is cut short) keeps being applied and draws
    // current without the rover moving.
    //
    // To prevent this, when the rover is commanded 0 and has come to a stop,
    // one stop command is sent. This unpowers the motors for one write cycle
    // so they can ease back to rest, after which velocity control takes over
    // again. A stop also clears a latched moteus fault or watchdog timeout.
    bool wheels_are_stopped = true;
    bool commanding_all_zero = true;
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      wheels_are_stopped = wheels_are_stopped && std::abs(wheel_velocities_[wheel]) < stopped_threshold_rads_per_s_;
      commanding_all_zero = commanding_all_zero && wheel_command_velocities_[wheel] == 0;
    }
    // Once we start moving again, we're open to zeroing out again as soon as
    // we stop (0 commanded and actual velocity)
    if (!commanding_all_zero)
    {
      zeroed_out_ = false;
    }
    const bool zero_out = !zeroed_out_ && wheels_are_stopped && commanding_all_zero;

    std::vector<moteus::CanFdFrame> frames;
    std::array<double, wheel_count> sent_velocities = {0.0, 0.0, 0.0, 0.0};
    for (size_t wheel = FL; wheel < LAST; wheel++)
    {
      if (zero_out)
      {
        frames.push_back(controllers_[wheel]->MakeStop());
        continue;
      }

      const double wheel_cmd_rads_per_s = wheel_command_velocities_[wheel];
      const double motor_cmd_revolutions_per_s =
          wheel_signs_[wheel] * radians_to_revolutions(wheel_cmd_rads_per_s) * config_.gear_ratio;

      moteus::PositionMode::Command command;
      command.position = std::numeric_limits<double>::quiet_NaN();
      command.velocity = std::clamp(motor_cmd_revolutions_per_s, -config_.max_velocity, config_.max_velocity);
      command.maximum_torque = config_.max_torque;
      frames.push_back(controllers_[wheel]->MakePosition(command, &position_format_));
      sent_velocities[wheel] = command.velocity;

      RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "Asking to command: %f rad/s (%f motor rev/s) on wheel %s.\n",
                           wheel_cmd_rads_per_s, command.velocity, wheel_names_[wheel].c_str());
    }

    try
    {
      cycle(frames);
    }
    catch (const std::exception &e)
    {
      RCLCPP_ERROR_THROTTLE(logger_, clock_, log_period_ms_, "Failed to write to the moteus controllers: %s", e.what());
      return hardware_interface::return_type::ERROR;
    }

    if (zero_out)
    {
      zeroed_out_ = true;
      RCLCPP_INFO(logger_, "ZEROING OUT!!!\n");
    }
    publish_command_echo(sent_velocities, zero_out ? 0.0 : config_.max_torque);

    return hardware_interface::return_type::OK;
  }

}; // namespace chassis_controls

/**
 * Exports class via pluginlib so it may be used by diff_cont
 */
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystem, hardware_interface::SystemInterface)
