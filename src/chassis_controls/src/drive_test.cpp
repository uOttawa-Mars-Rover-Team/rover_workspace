#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#define Phoenix_No_WPI    // remove WPI dependencies
#include "ctre/Phoenix.h" // IWYU pragma: keep
#include "ctre/phoenix/unmanaged/Unmanaged.h"
#include <memory>
#include <string>
#include <iostream>
#include "rclcpp/rclcpp.hpp" // IWYU pragma: keep
#include <geometry_msgs/msg/twist.hpp>
#include "general_interfaces/msg/motor_data.hpp" // IWYU pragma: keep
#include <chrono>
using namespace std::chrono_literals;
using namespace ctre::phoenix;
using namespace ctre::phoenix::platform;
using namespace ctre::phoenix::motorcontrol;
using namespace ctre::phoenix::motorcontrol::can;

class DriveTestNode : public rclcpp::Node
{

public:
    // bring up drive motors
    TalonSRX FR{40};
    TalonSRX FL{20};
    TalonSRX RL{30};
    TalonSRX RR{10};
    int enc_counts_per_rev = 4096;
    int base_time = 1000000;
    int reset_mu_s = 1 * base_time;
    std::chrono::steady_clock::time_point last_checked_time;
    double last_encoder_position = 0;

    DriveTestNode(const float kF = 0.0, const float kP = 0.0, const float kI = 0.0, const float kD = 0.0) : Node("drive")
    {
        int kPIDLoopIdx = 0;
        int kTimeoutMs = 100;

        FR.ConfigFactoryDefault();
        FR.ConfigNominalOutputForward(0, kTimeoutMs);
        FR.ConfigNominalOutputReverse(0, kTimeoutMs);
        FR.ConfigPeakOutputForward(1, kTimeoutMs);
        FR.ConfigPeakOutputReverse(-1, kTimeoutMs);
        FR.Config_kF(kPIDLoopIdx, kF, kTimeoutMs);
        FR.Config_kP(kPIDLoopIdx, kP, kTimeoutMs);
        FR.Config_kI(kPIDLoopIdx, kI, kTimeoutMs);
        FR.Config_kD(kPIDLoopIdx, kD, kTimeoutMs);

        FL.ConfigFactoryDefault();
        FL.ConfigNominalOutputForward(0, kTimeoutMs);
        FL.ConfigNominalOutputReverse(0, kTimeoutMs);
        FL.ConfigPeakOutputForward(1, kTimeoutMs);
        FL.ConfigPeakOutputReverse(-1, kTimeoutMs);
        FL.Config_kF(kPIDLoopIdx, kF, kTimeoutMs);
        FL.Config_kP(kPIDLoopIdx, kP, kTimeoutMs);
        FL.Config_kI(kPIDLoopIdx, kI, kTimeoutMs);
        FL.Config_kD(kPIDLoopIdx, kD, kTimeoutMs);

        RR.ConfigFactoryDefault();
        RR.ConfigNominalOutputForward(0, kTimeoutMs);
        RR.ConfigNominalOutputReverse(0, kTimeoutMs);
        RR.ConfigPeakOutputForward(1, kTimeoutMs);
        RR.ConfigPeakOutputReverse(-1, kTimeoutMs);
        RR.Config_kF(kPIDLoopIdx, kF, kTimeoutMs);
        RR.Config_kP(kPIDLoopIdx, kP, kTimeoutMs);
        RR.Config_kI(kPIDLoopIdx, kI, kTimeoutMs);
        RR.Config_kD(kPIDLoopIdx, kD, kTimeoutMs);

        RL.ConfigFactoryDefault();
        RL.ConfigNominalOutputForward(0, kTimeoutMs);
        RL.ConfigNominalOutputReverse(0, kTimeoutMs);
        RL.ConfigPeakOutputForward(1, kTimeoutMs);
        RL.ConfigPeakOutputReverse(-1, kTimeoutMs);
        RL.Config_kF(kPIDLoopIdx, kF, kTimeoutMs);
        RL.Config_kP(kPIDLoopIdx, kP, kTimeoutMs);
        RL.Config_kI(kPIDLoopIdx, kI, kTimeoutMs);
        RL.Config_kD(kPIDLoopIdx, kD, kTimeoutMs);

        FR.SetInverted(true);
        RR.SetInverted(true);

        FL.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
        FR.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
        RR.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
        RL.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);

        FL.SetSelectedSensorPosition(0.0);
        FR.SetSelectedSensorPosition(0.0);
        RR.SetSelectedSensorPosition(0.0);
        RL.SetSelectedSensorPosition(0.0);

        FR.SetSensorPhase(true);
        FL.SetSensorPhase(true);
        RL.SetSensorPhase(true);
        RR.SetSensorPhase(true);
    };

    void drive(const std::string wheel_name = "RR", const float command = 0.1, const bool use_vel = false)
    {
        ctre::phoenix::unmanaged::Unmanaged::FeedEnable(10000);
        TalonSRXControlMode control_mode;
        if (!use_vel)
        {
            control_mode = TalonSRXControlMode::PercentOutput;
        }
        else
        {
            control_mode = TalonSRXControlMode::Velocity;
        }


        if (wheel_name == "FR")
        {
            FR.Set(control_mode, command);
        }
        else if (wheel_name == "FL")
        {
            FL.Set(control_mode, command);
        }
        else if (wheel_name == "RL")
        {
            RL.Set(control_mode, command);
        }
        else if (wheel_name == "RR")
        {
            RR.Set(control_mode, command);
        }
        else if (wheel_name == "ALL"){
            RR.Set(control_mode, command);
            RL.Set(control_mode, command);
            FR.Set(control_mode, command);
            FL.Set(control_mode, command);
        }
        else
        {
            RCLCPP_INFO(this->get_logger(), "Invalid wheel_name: %s", wheel_name.c_str());
            return;
        }
        
        std::chrono::steady_clock::time_point now = std::chrono::steady_clock::now();
        int64_t time_diff_mu_s = std::chrono::duration_cast<std::chrono::microseconds>(now - last_checked_time).count();
        if (time_diff_mu_s > reset_mu_s)
        {
            last_checked_time = now;
            RCLCPP_INFO(this->get_logger(), "RR Rotation/s: %f", RR.GetSelectedSensorVelocity());
            RCLCPP_INFO(this->get_logger(), "RL Rotation/s: %f", RL.GetSelectedSensorVelocity());
            RCLCPP_INFO(this->get_logger(), "FR Rotation/s: %f", FR.GetSelectedSensorVelocity());
            RCLCPP_INFO(this->get_logger(), "FL Rotation/s: %f", FL.GetSelectedSensorVelocity());
            RCLCPP_INFO(this->get_logger(), "\n");
        }
    }
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    // rclcpp::executors::SingleThreadedExecutor executor;

    std::shared_ptr<DriveTestNode> drivetestnode;
    if (argc == 8)
    {
        drivetestnode = std::make_shared<DriveTestNode>(std::stof(argv[4]), std::stof(argv[5]), std::stof(argv[6]), std::stof(argv[7]));
        RCLCPP_INFO(drivetestnode->get_logger(), "Initializing drive test node with k values...");
    }
    else
    {
        drivetestnode = std::make_shared<DriveTestNode>();
    }
    RCLCPP_INFO(drivetestnode->get_logger(), "Initialized drive test node");

    // Print args
    int i = 0;
    while (i < argc)
    {
        std::cout << "Argument " << i + 1 << ": " << argv[i]
                  << std::endl;
        i++;
    }

    while (rclcpp::ok())
    {
        // executor.spin_node_once(drivetestnode);
        if (argc == 3)
        {
            drivetestnode->drive(argv[1], std::stof(argv[2]));
        }
        else if (argc == 4 || argc == 8)
        {
            drivetestnode->drive(argv[1], std::stof(argv[2]), std::stoi(argv[3]));
        }
        else
        {
            drivetestnode->drive();
        }
    }

    RCLCPP_INFO(drivetestnode->get_logger(), "Shutting down drivetestnode...");

    rclcpp::shutdown();

    return 0;
}
