#ifndef CHASSIS_CONTROLS__DRIVE_HARDWARE_V3_HPP_
#define CHASSIS_CONTROLS__DRIVE_HARDWARE_V3_HPP_

#include <array>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>
#include <vector>

#include "rclcpp/clock.hpp"
#include "rclcpp/logger.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp/executors/single_threaded_executor.hpp"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"

#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"

#include "moteus_msgs/msg/controller_state.hpp"
#include "moteus_msgs/msg/position_command.hpp"

namespace chassis_controls
{
    using CallbackReturn =
        rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

    class DriveSystemV3 : public hardware_interface::SystemInterface
    {
    public:
        DriveSystemV3() = default;
        ~DriveSystemV3() override;

        CallbackReturn on_init(const hardware_interface::HardwareInfo &info) override;

        hardware_interface::CallbackReturn on_activate(
            const rclcpp_lifecycle::State &previous_state) override;



        std::vector<hardware_interface::StateInterface> export_state_interfaces() override;
        std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

        hardware_interface::return_type read(
            const rclcpp::Time &time, const rclcpp::Duration &period) override;

        hardware_interface::return_type write(
            const rclcpp::Time &time, const rclcpp::Duration &period) override;

    private:
        static constexpr size_t wheel_count = 4;

        enum Wheels : size_t
        {
            FL = 0,
            FR = 1,
            RR = 2,
            RL = 3,
            LAST = 4
        };

 
        struct Config
        {
            int FL_id = -1;
            int FR_id = -1;
            int RR_id = -1;
            int RL_id = -1;

            std::string state_prefix = "/moteus";
            std::string state_suffix = "/state";
            std::string cmd_prefix = "/moteus";
            std::string cmd_suffix = "/command";

            std::string units = "rad";

            double state_timeout_sec = 0.5;
        } config_;

        std::array<int, wheel_count> motor_ids_{};

        std::unordered_map<size_t, std::string> wheel_names_ = {
            {FL, "FL"},
            {FR, "FR"},
            {RR, "RR"},
            {RL, "RL"},
        };

        // --- ros2_control backing storage ---
        std::array<double, wheel_count> wheel_positions_;
        std::array<double, wheel_count> wheel_velocities_;
        std::array<double, wheel_count> wheel_command_velocities_;

        // --- ROS comms ---
        rclcpp::Node::SharedPtr node_;
        rclcpp::executors::SingleThreadedExecutor exec_;
        std::thread spin_thread_;

        using ControllerState = moteus_msgs::msg::ControllerState;
        using PositionCommand = moteus_msgs::msg::PositionCommand;

        std::array<rclcpp::Subscription<ControllerState>::SharedPtr, wheel_count> state_subs_;
        std::array<rclcpp::Publisher<PositionCommand>::SharedPtr, wheel_count> cmd_pubs_;

        // state cache protection
        std::mutex state_mtx_;
        std::array<bool, wheel_count> have_state_{};
        std::array<rclcpp::Time, wheel_count> last_state_time_;

        // logger / clock
        rclcpp::Logger logger_ = rclcpp::get_logger("DriveSystemV3");
        rclcpp::Clock clock_ = rclcpp::Clock{};
        static constexpr unsigned int log_period_ms_ = 1000;

    private:
        // helpers
        void start_spin();
        void stop_spin();

        std::string make_state_topic(int id) const;
        std::string make_cmd_topic(int id) const;

        double maybe_convert_position(double position) const;
        double maybe_convert_velocity(double velocity) const;

        static double rev_to_rad(double rev);
    }; // class DriveSystemV3

} // namespace chassis_controls

#endif // CHASSIS_CONTROLS__DRIVE_HARDWARE_V3_HPP_
