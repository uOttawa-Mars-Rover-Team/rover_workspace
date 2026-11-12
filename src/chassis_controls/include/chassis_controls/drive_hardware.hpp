#ifndef CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
#define CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_

#include <math.h>

#include <array>
#include <memory>
#include <string>
#include <vector>

#include "rclcpp/clock.hpp"
#include "rclcpp/node.hpp"
#include "rclcpp/publisher.hpp"
#include <rclcpp/logger.hpp>
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "sensor_msgs/msg/joint_state.hpp"

#include "moteus.h"

namespace chassis_controls
{
  using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

  /**
   * ros2_control hardware interface for the drive system: four NEO v1.1 motors,
   * each driven by a moteus r4.11 in velocity control over CAN-FD.
   */
  class DriveSystem : public hardware_interface::SystemInterface
  {
  public:
    CallbackReturn on_init(const hardware_interface::HardwareComponentInterfaceParams &params) override;

    hardware_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State &previous_state) override;

    hardware_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State &previous_state) override;

    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

    hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) override;

    hardware_interface::return_type write(const rclcpp::Time &time, const rclcpp::Duration &period) override;

  private:
    inline double revolutions_to_radians(const double &revolutions) { return revolutions * (2 * M_PI); };
    inline double radians_to_revolutions(const double &radians) { return radians / (2 * M_PI); };

    static constexpr size_t wheel_count = 4;

    // Below this wheel speed [rad/s] a wheel counts as stopped (see write()).
    static constexpr double stopped_threshold_rads_per_s_ = 0.05;

    enum Wheels
    {
      FL,
      FR,
      RR,
      RL,
      LAST,
    };
    const std::array<std::string, wheel_count> wheel_names_ = {"FL", "FR", "RR", "RL"};

    // The right side motors are mounted mirrored, so their direction is flipped
    // to make a positive command drive every wheel forward.
    const std::array<double, wheel_count> wheel_signs_ = {1.0, -1.0, -1.0, 1.0};

    struct
    {
      std::array<int, wheel_count> ids;
      // Motor revolutions per wheel revolution.
      double gear_ratio;
      // Largest velocity ever sent to a moteus [motor rev/s].
      double max_velocity;
      // Torque limit sent with every velocity command [Nm].
      double max_torque;
      // Extra arguments for the moteus transport (e.g. "--socketcan-iface can0").
      // Empty auto-detects the adapter.
      std::vector<std::string> transport_args;
    } config_;

    /// Sends one frame per wheel, then updates the wheel states from the replies.
    void cycle(std::vector<mjbots::moteus::CanFdFrame> &frames);

    /// Publishes the commands that were just sent to the moteus controllers.
    void publish_command_echo(const std::array<double, wheel_count> &velocities, double torque);

    std::shared_ptr<mjbots::moteus::Transport> transport_;
    std::array<std::shared_ptr<mjbots::moteus::Controller>, wheel_count> controllers_;
    mjbots::moteus::PositionMode::Format position_format_;

    std::array<double, wheel_count> wheel_positions_ = {0.0, 0.0, 0.0, 0.0};
    std::array<double, wheel_count> wheel_velocities_ = {0.0, 0.0, 0.0, 0.0};
    std::array<double, wheel_count> wheel_command_velocities_ = {0.0, 0.0, 0.0, 0.0};

    bool zeroed_out_ = false;

    // Node used only to publish the command echo topic.
    rclcpp::Node::SharedPtr echo_node_;
    rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr command_echo_pub_;

    // Manually create a logger and a clock to log with rate limiting
    rclcpp::Logger logger_ = rclcpp::get_logger("DriveSystem");
    rclcpp::Clock clock_ = rclcpp::Clock{};
    static constexpr unsigned int log_period_ms_ = 1000;
  }; // class DriveSystem

} // namespace chassis_controls

#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
