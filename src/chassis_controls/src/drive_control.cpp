#include "ctre/phoenix/motorcontrol/FeedbackDevice.h"
#define Phoenix_No_WPI // remove WPI dependencies
#include "ctre/Phoenix.h" // IWYU pragma: keep
#include "ctre/phoenix/unmanaged/Unmanaged.h" 
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp" // IWYU pragma: keep
#include <geometry_msgs/msg/twist.hpp>
#include "general_interfaces/msg/motor_data.hpp" // IWYU pragma: keep

using namespace std::chrono_literals;
using namespace ctre::phoenix;
using namespace ctre::phoenix::platform;
using namespace ctre::phoenix::motorcontrol;
using namespace ctre::phoenix::motorcontrol::can;




class DriveNode : public rclcpp::Node {

public:
  float linear;
  float yaw;

  //bring up drive motors
  TalonSRX FR{10};
  TalonSRX FL{20};
  TalonSRX RL{30};
  TalonSRX RR{40};
  

  DriveNode() : Node("drive") {
    subscription_ = this->create_subscription<geometry_msgs::msg::Twist>("cmd_vel", 10, std::bind(&DriveNode::topic_callback, this, std::placeholders::_1));
    publisher_ = this->create_publisher<general_interfaces::msg::MotorData>("MotorData", 10);
    
    FR.SetInverted(true);
    FL.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
    FR.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
    RR.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
    RL.ConfigSelectedFeedbackSensor(FeedbackDevice::CTRE_MagEncoder_Relative, 0, 100);
  };

  void setSafety(const float &safety){
      this->safety_ = safety;
  }

  float getSafety() const {
      return safety_;
  }

  void drive (const float linear, const float yaw) {

      ctre::phoenix::unmanaged::Unmanaged::FeedEnable(50);
      float fl_vel = linear + 0.3*yaw;
      float rr_vel = linear - 0.3*yaw;

      FR.Set(TalonSRXControlMode::Follower, 40);
      FL.Set(TalonSRXControlMode::PercentOutput, fl_vel);
      RR.Set(TalonSRXControlMode::PercentOutput, rr_vel);
      RL.Set(TalonSRXControlMode::Follower, 20);




  }

  int publish(){
      auto message = general_interfaces::msg::MotorData();
      message.velocity_feedback = RR.GetSelectedSensorVelocity();
      message.positon_feedback  = RR.GetSelectedSensorPosition();     
      message.output_current    = RR.GetStatorCurrent();
      message.output_voltage    = RR.GetMotorOutputVoltage();
      Faults faults;
      int err = (int) RR.GetFaults(faults);
      message.faults_bitfield = faults.ToBitfield();
      message.sticky_faults = "Right Side";
      publisher_->publish(message);

      message = general_interfaces::msg::MotorData();
      message.velocity_feedback = FL.GetSelectedSensorVelocity();
      message.positon_feedback = FL.GetSelectedSensorVelocity();
      message.velocity_feedback = FL.GetSelectedSensorVelocity();
      message.velocity_feedback = FL.GetSelectedSensorVelocity();
      err = (int) FL.GetFaults(faults);
      message.faults_bitfield = faults.ToBitfield();
      message.sticky_faults = "Left Side";
      publisher_->publish(message);
      return err;
  }

private:

  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr subscription_;
  rclcpp::Publisher<general_interfaces::msg::MotorData>::SharedPtr publisher_;
  float safety_;

  void topic_callback(const geometry_msgs::msg::Twist msg){
      linear = msg.linear.x;
      yaw = msg.angular.z;
  }
};

int main(int argc, char * argv[]){

    rclcpp::init(argc, argv);
    rclcpp::executors::SingleThreadedExecutor executor;

    auto drivenode = std::make_shared<DriveNode>();
    RCLCPP_INFO(drivenode->get_logger(), "Initialized drive node");


    drivenode->setSafety(0.3);

    while (rclcpp::ok()){
      executor.spin_node_once(drivenode);


      drivenode->drive(drivenode->getSafety()*drivenode->linear, drivenode->yaw);

    }

    RCLCPP_INFO(drivenode->get_logger(), "Shutting down drivenode...");

    rclcpp::shutdown();

    return 0;
}
