#include "chassis_controls/drive_hardware_open_loop.hpp"
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
     * @brief Initializes the DriveSystemOpenLoop lifecycle node.
     *
     * Parses the URDF, extractacting xacro arguments. Initializes all class
     * attributes, brings up Talon objects and PIDs.
     *
     * @param info data contained in xacro file (URDF + macros + args + ros2
     * control)
     * @return Success flag if no errors during initialization, failure flag if
     * executition fails.
     */
    CallbackReturn DriveSystemOpenLoop::on_init(const hardware_interface::HardwareInfo &info)
    {
        RCLCPP_INFO(logger_, "\n\n\n\nOPEN LOOP DRIVE HARDWARE INTERFACE\n\n\n\n");
        RCLCPP_INFO(logger_, "Configuring Hardware Interface...");
        if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS)
        {
            return CallbackReturn::ERROR;
        }

        info_ = info;

        // Read configured values
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

        config_.max_wheel_rad_per_sec = std::stod(info_.hardware_parameters["max_wheel_rad_per_sec"]);
        if (config_.max_wheel_rad_per_sec <= 0)
        {
            RCLCPP_ERROR(logger_, "Invalid max_wheel_rad_per_sec!");
            return CallbackReturn::ERROR;
        }
        else
        {
            RCLCPP_INFO(logger_, "max_wheel_rad_per_sec is %f.", config_.max_wheel_rad_per_sec);
        }

        return CallbackReturn::SUCCESS;
    }

    /**
     * @brief Configures the DriveSystemOpenLoop lifecycle node.
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
    DriveSystemOpenLoop::on_activate(const rclcpp_lifecycle::State & /*previous_state*/)
    {
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

            if (err)
            {
                RCLCPP_ERROR(logger_, "Failed when setting up wheel %s!", wheel_names_[wheel].c_str());
                return CallbackReturn::ERROR;
            }
        }

        talons_[FR]->SetInverted(true);
        talons_[RR]->SetInverted(true);

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
    DriveSystemOpenLoop::export_state_interfaces()
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
    DriveSystemOpenLoop::export_command_interfaces()
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
    hardware_interface::return_type DriveSystemOpenLoop::read(const rclcpp::Time & /*time*/, const rclcpp::Duration &period)
    {
        // For open-loop control, we will use kinematic odometry.
        // We assume the wheels have achieved their commanded velocity.
        // We read nothing from the hardware and simply update the state
        // interfaces with the last commanded values.
        for (size_t wheel = FL; wheel < LAST; wheel++)
        {
            // The current velocity is the last commanded velocity
            wheel_velocities_[wheel] = wheel_command_velocities_[wheel];

            // Update position by integrating the velocity
            wheel_positions_[wheel] += wheel_velocities_[wheel] * period.seconds();

            // Logging (optional, can be removed or simplified)
            const std::string wheel_name = wheel_names_[wheel];
            RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "%s wheel open-loop velocity: %f rad/s.", wheel_name.c_str(), wheel_velocities_[wheel]);
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
     * @params period duration since last write command.
     * @returns OK flag if successful write, ERROR flag if write failed.
     */
    hardware_interface::return_type DriveSystemOpenLoop::write(const rclcpp::Time & /*time*/, const rclcpp::Duration &period)
    {
        // Feed the watchdog
        u_int64_t period_ns = period.nanoseconds();
        ctre::phoenix::unmanaged::Unmanaged::FeedEnable(period_ns);

        // The "zeroing out" logic is no longer needed for open-loop PercentOutput control.
        // When the commanded velocity is 0, the percent output will also be 0, which
        // is the desired behavior (motors are not actively fighting any forces).

        for (size_t wheel = FL; wheel < LAST; wheel++)
        {
            // Get the commanded velocity in rad/s from the controller
            const double wheel_cmd_rads_per_s = wheel_command_velocities_[wheel];

            // Convert the rad/s command to a percent output (-1.0 to 1.0)
            // by dividing by the configured maximum wheel speed.
            double percent_output = wheel_cmd_rads_per_s / config_.max_wheel_rad_per_sec;

            // Clamp the output to the valid range [-1, 1] as a safety measure
            percent_output = std::clamp(percent_output, -1.0, 1.0);

            // Command the Talon in PercentOutput mode
            talons_[wheel]->Set(
                ctre::phoenix::motorcontrol::TalonSRXControlMode::PercentOutput, percent_output);

            RCLCPP_INFO_THROTTLE(logger_, clock_, log_period_ms_, "Commanding %f%% on wheel %s for %f rad/s.\n", percent_output * 100, wheel_names_[wheel].c_str(), wheel_cmd_rads_per_s);
        }

        return hardware_interface::return_type::OK;
    }

}; // namespace chassis_controls

/**
 * Exports class via pluginlib so it may be used by diff_cont
 */
#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(chassis_controls::DriveSystemOpenLoop, hardware_interface::SystemInterface)
