#ifndef CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
#define CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_

#include <math.h>

#include "rclcpp/clock.hpp"
#include <rclcpp/logger.hpp>
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"

#include "ctre/phoenix/motorcontrol/can/TalonSRX.h"

namespace chassis_controls
{
  using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

  class HARDWARE_INTERFACE_PUBLIC DriveSystem : public hardware_interface::SystemInterface
  {
  public:
    CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;

    hardware_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State &previous_state) override;

    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

    std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

    hardware_interface::return_type read(const rclcpp::Time &time, const rclcpp::Duration &period) override;

    hardware_interface::return_type write(const rclcpp::Time &time, const rclcpp::Duration &period) override;

  private:
    inline double revolutions_to_radians(const double &revolutions) { return revolutions * (2 * M_PIl); };
    inline double radians_to_revolutions(const double &radians) { return radians / (2 * M_PIl); };

    static constexpr size_t wheel_count = 4;
    static constexpr double talon_srx_update_period_ = 0.1;

    struct PIDGains
    {
      double Kp;
      double Ki;
      double Kd;
    };

    struct
    {
      unsigned int wheel_encoder_counts_per_revolution;
      std::array<PIDGains, wheel_count> pid_gains;
      double wheel_circumference;
    } config_;

    enum Wheels
    {
      FL,
      FR,
      RR,
      RL,
      LAST,
    };
    std::unordered_map<size_t, std::string> wheel_names_ = {
        {FL, "FL"},
        {FR, "FR"},
        {RR, "RR"},
        {RL, "RL"},
    };

    std::array<std::shared_ptr<ctre::phoenix::motorcontrol::can::TalonSRX>, wheel_count> talons_;

    std::array<double, wheel_count> wheel_positions_;
    std::array<double, wheel_count> wheel_velocities_;
    std::array<double, wheel_count> wheel_command_velocities_;

    // Manually create a logger and a clock to log with rate limiting
    rclcpp::Logger logger_ = rclcpp::get_logger("DriveSystem");
    rclcpp::Clock clock_ = rclcpp::Clock{};
    static constexpr unsigned int log_period_ms_ = 1000000;
  }; // class DriveSystem

} // namespace chassis_controls

#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_HPP_
