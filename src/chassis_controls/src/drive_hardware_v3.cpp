#include "chassis_controls/drive_hardware_v3.hpp"

#include <cmath>
#include <stdexcept>

#include "pluginlib/class_list_macros.hpp"

namespace chassis_controls
{

    double DriveSystemV3::rev_to_rad(double rev)
    {
        return rev * (2.0 * M_PI);
    }

    double DriveSystemV3::maybe_convert_position(double position) const
    {
        // If moteus publishes revolutions, convert to radians.
        if (config_.units == "rev")
        {
            return rev_to_rad(position);
        }
        return position; // assume rad
    }

    double DriveSystemV3::maybe_convert_velocity(double velocity) const
    {
        // If moteus publishes rev/s, convert to rad/s.
        if (config_.units == "rev")
        {
            return rev_to_rad(velocity);
        }
        return velocity; // assume rad/s
    }

    std::string DriveSystemV3::make_state_topic(int id) const
    {
        // e.g. "/moteus/state_1/state"
        return config_.state_prefix + "/state_" + std::to_string(id) + config_.state_suffix;
    }

    std::string DriveSystemV3::make_cmd_topic(int id) const
    {
        // e.g. "/moteus/state_1/command"
        return config_.cmd_prefix + "/state_" + std::to_string(id) + config_.cmd_suffix;
    }

    void DriveSystemV3::start_spin()
    {
        if (!node_)
        {
            throw std::runtime_error("start_spin called before node_ was created");
        }
        exec_.add_node(node_);
        spin_thread_ = std::thread([this]()
                                   { exec_.spin(); });
    }

    void DriveSystemV3::stop_spin()
    {
        exec_.cancel();
        if (spin_thread_.joinable())
        {
            spin_thread_.join();
        }
    }

    DriveSystemV3::~DriveSystemV3()
    {
        // Best-effort cleanup: avoid leaving a spinning thread around.
        try
        {
            stop_spin();
        }
        catch (...)
        {
            // swallow
        }
    }

    /**
     * @brief Initialize the topic-based (V3) DriveSystem ros2_control hardware interface.
     *
     * This implementation does NOT talk to CAN or motor drivers directly.
     * Instead, it communicates with the V3 CAN router using ROS 2 topics:
     *
     * - Subscribes to moteus_msgs/ControllerState for each wheel to receive state.
     * - Publishes moteus_msgs/PositionCommand for each wheel to send velocity commands.
     *
     * During initialization we:
     *  1) Read required hardware_parameters from the URDF (wheel IDs, topic patterns, units).
     *  2) Create an internal rclcpp::Node used for publishers/subscribers.
     *  3) Create one publisher + one subscriber per wheel.
     *  4) Start a background executor thread so subscriber callbacks are processed.
     *
     * @param info HardwareInfo provided by ros2_control (parsed from URDF).
     * @return SUCCESS if initialization completes; ERROR otherwise.
     */

    CallbackReturn DriveSystemV3::on_init(const hardware_interface::HardwareInfo &info)
    {
        RCLCPP_INFO(logger_, "Configuring V3 topic-based HW Interface...");

        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
        {
            return CallbackReturn::ERROR;
        }

        info_ = info;

        // Validate wheel_count vs joints
        if (info_.joints.size() != wheel_count)
        {
            RCLCPP_ERROR(
                logger_,
                "Expected %zu joints for drive wheels, but got %zu in URDF.",
                wheel_count, info_.joints.size());
            return CallbackReturn::ERROR;
        }

        // helper lambdas to read hardware_parameters
        auto require_key = [&](const std::string &k)
        {
            if (info_.hardware_parameters.find(k) == info_.hardware_parameters.end())
            {
                throw std::runtime_error("Missing hardware_parameter: " + k);
            }
        };

        try
        {
            // Required IDs
            require_key("FL_id");
            require_key("FR_id");
            require_key("RR_id");
            require_key("RL_id");

            config_.FL_id = std::stoi(info_.hardware_parameters.at("FL_id"));
            config_.FR_id = std::stoi(info_.hardware_parameters.at("FR_id"));
            config_.RR_id = std::stoi(info_.hardware_parameters.at("RR_id"));
            config_.RL_id = std::stoi(info_.hardware_parameters.at("RL_id"));

            motor_ids_[FL] = config_.FL_id;
            motor_ids_[FR] = config_.FR_id;
            motor_ids_[RR] = config_.RR_id;
            motor_ids_[RL] = config_.RL_id;

            // Optional topic components
            if (auto it = info_.hardware_parameters.find("state_prefix"); it != info_.hardware_parameters.end())
            {
                config_.state_prefix = it->second;
            }
            if (auto it = info_.hardware_parameters.find("state_suffix"); it != info_.hardware_parameters.end())
            {
                config_.state_suffix = it->second;
            }
            if (auto it = info_.hardware_parameters.find("cmd_prefix"); it != info_.hardware_parameters.end())
            {
                config_.cmd_prefix = it->second;
            }
            if (auto it = info_.hardware_parameters.find("cmd_suffix"); it != info_.hardware_parameters.end())
            {
                config_.cmd_suffix = it->second;
            }

            // Optional units
            if (auto it = info_.hardware_parameters.find("units"); it != info_.hardware_parameters.end())
            {
                config_.units = it->second;
                if (config_.units != "rad" && config_.units != "rev")
                {
                    throw std::runtime_error("Invalid units: " + config_.units + " (expected 'rad' or 'rev')");
                }
            }

            // Optional timeout
            if (auto it = info_.hardware_parameters.find("state_timeout_sec"); it != info_.hardware_parameters.end())
            {
                config_.state_timeout_sec = std::stod(it->second);
            }
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(logger_, "Invalid hardware_parameters: %s", e.what());
            return CallbackReturn::ERROR;
        }

        // init backing storage
        wheel_positions_.fill(0.0);
        wheel_velocities_.fill(0.0);
        wheel_command_velocities_.fill(0.0);
        have_state_.fill(false);

        // Create internal node for pub/sub callbacks
        node_ = std::make_shared<rclcpp::Node>("drive_hardware_v3");

        auto qos = rclcpp::QoS(rclcpp::KeepLast(1)).best_effort();

        // Create pubs/subs per wheel
        for (size_t w = FL; w < LAST; w++)
        {
            const int id = motor_ids_[w];
            const std::string state_topic = make_state_topic(id);
            const std::string cmd_topic = make_cmd_topic(id);

            RCLCPP_INFO(
                logger_, "Wheel %s (id=%d): sub=%s pub=%s",
                wheel_names_[w].c_str(), id, state_topic.c_str(), cmd_topic.c_str());

            state_subs_[w] = node_->create_subscription<ControllerState>(
                state_topic, qos,
                [this, w](const ControllerState::SharedPtr msg)
                {
                    std::lock_guard<std::mutex> lk(state_mtx_);
                    wheel_positions_[w] = maybe_convert_position(static_cast<double>(msg->position));
                    wheel_velocities_[w] = maybe_convert_velocity(static_cast<double>(msg->velocity));
                    have_state_[w] = true;
                    last_state_time_[w] = node_->now();
                });

            cmd_pubs_[w] = node_->create_publisher<PositionCommand>(cmd_topic, qos);
        }

        // Start spinning so subscriptions work
        start_spin();

        return CallbackReturn::SUCCESS;
    }

    /**
     * @brief Activate the hardware interface.
     *
     * For safety, we publish a zero-velocity command once on activation.
     * (This helps ensure the rover does not move unexpectedly when controllers start.)
     */
    hardware_interface::CallbackReturn
    DriveSystemV3::on_activate(const rclcpp_lifecycle::State &)
    {
        RCLCPP_INFO(logger_, "Activating DriveSystemV3...");

        // Safe initial command: publish 0 velocity once
        for (size_t w = FL; w < LAST; w++)
        {
            PositionCommand cmd;
            cmd.velocity = {0.0f};
            cmd_pubs_[w]->publish(cmd);
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
    DriveSystemV3::export_state_interfaces()
    {
        std::vector<hardware_interface::StateInterface> state_interfaces;
        state_interfaces.reserve(info_.joints.size() * 2);

        for (std::size_t i = 0; i < info_.joints.size(); i++)
        {
            state_interfaces.emplace_back(
                info_.joints[i].name, hardware_interface::HW_IF_POSITION, &wheel_positions_[i]);
            state_interfaces.emplace_back(
                info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &wheel_velocities_[i]);
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
    DriveSystemV3::export_command_interfaces()
    {
        std::vector<hardware_interface::CommandInterface> command_interfaces;
        command_interfaces.reserve(info_.joints.size());

        for (std::size_t i = 0; i < info_.joints.size(); i++)
        {
            command_interfaces.emplace_back(
                info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &wheel_command_velocities_[i]);
        }

        return command_interfaces;
    }

    /**
     * @brief Update ros2_control state from the latest topic data.
     *
     * Subscriber callbacks continuously update wheel_positions_/wheel_velocities_.
     * read() should be fast and non-blocking, so we only:
     *  - Optionally warn if no state has been received yet
     *  - Optionally warn if the last state message is stale
     *
     * @return OK always (state is best-effort via topics).
     */
    hardware_interface::return_type
    DriveSystemV3::read(const rclcpp::Time &, const rclcpp::Duration &)
    {
        if (!node_)
        {
            return hardware_interface::return_type::OK;
        }

        const auto now = node_->now();

        std::lock_guard<std::mutex> lk(state_mtx_);
        for (size_t w = FL; w < LAST; w++)
        {
            if (!have_state_[w])
            {
                RCLCPP_WARN_THROTTLE(
                    logger_, clock_, log_period_ms_,
                    "No ControllerState received yet for wheel %s",
                    wheel_names_[w].c_str());
                continue;
            }

            const double age = (now - last_state_time_[w]).seconds();
            if (age > config_.state_timeout_sec)
            {
                RCLCPP_WARN_THROTTLE(
                    logger_, clock_, log_period_ms_,
                    "ControllerState for wheel %s is stale: %.3fs old (timeout=%.3fs)",
                    wheel_names_[w].c_str(), age, config_.state_timeout_sec);
            }
        }

        return hardware_interface::return_type::OK;
    }

    /**
     * @brief Publish velocity commands to the V3 CAN router.
     *
     * The controller writes target wheel velocities into wheel_command_velocities_.
     * write() forwards each wheel command by publishing PositionCommand with:
     *   velocity = [target_rad_per_s]
     *
     * @return OK if publishing succeeds (best-effort QoS).
     */
    hardware_interface::return_type
    DriveSystemV3::write(const rclcpp::Time &, const rclcpp::Duration &)
    {
        for (size_t w = FL; w < LAST; w++)
        {
            PositionCommand cmd;
            cmd.velocity = {static_cast<float>(wheel_command_velocities_[w])};

            cmd_pubs_[w]->publish(cmd);

            RCLCPP_INFO_THROTTLE(
                logger_, clock_, log_period_ms_,
                "Command wheel %s: %.3f rad/s",
                wheel_names_[w].c_str(), wheel_command_velocities_[w]);
        }

        return hardware_interface::return_type::OK;
    }

} // namespace chassis_controls


PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystemV3, hardware_interface::SystemInterface)
