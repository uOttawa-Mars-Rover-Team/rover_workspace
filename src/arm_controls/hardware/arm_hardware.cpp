#include "v3_arm_controls/v3_arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <algorithm>

namespace v3_arm_controls
{

// -----------------------------------------------------------
// on_init()
// -----------------------------------------------------------
// This method is called once when the hardware interface is
// first initialized by the controller manager.
//
// Responsibilities:
// 1. Validate hardware info (from URDF / config)
// 2. Create a ROS 2 node for communication
// 3. Declare & read parameters (topics)
// 4. Initialize joint data structures
// 5. Set up ROS 2 subscribers & publishers
// -----------------------------------------------------------
CallbackReturn V3ArmHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  // --- Step 1: Call parent initialization logic ---
  // hardware_interface::SystemInterface::on_init() handles
  // parsing of URDF and storing the 'info_' structure.
  // If that fails, abort initialization.
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // --- Step 2: Create a ROS 2 node ---
  // The node is used for topic-based communication.
  // (Non-lifecycle node; lifecycle handled externally by ros2_control)
  node_ = rclcpp::Node::make_shared("v3_arm_hardware_node");

  // --- Step 3: Declare and read topic parameters ---
  // These parameters can be overridden in a YAML file or via 'ros2 param set'.
  // Defaults come from the class member variables (read_topic_ / write_topic_).
  node_->declare_parameter<std::string>("read_topic", read_topic_);
  node_->declare_parameter<std::string>("write_topic", write_topic_);
  node_->get_parameter("read_topic", read_topic_);
  node_->get_parameter("write_topic", write_topic_);

  // --- Step 4: Extract joint names from hardware info ---
  // The 'info_' object comes from the URDF hardware configuration.
  // It defines all joints that this hardware interface manages.
  size_t num_joints = info_.joints.size();
  if (num_joints == 0) {
    RCLCPP_ERROR(node_->get_logger(), "No joints defined in hardware info.");
    return CallbackReturn::ERROR;
  }

  // Store joint names for later lookup
  joint_names_.reserve(num_joints);
  for (const auto & j : info_.joints) {
    joint_names_.push_back(j.name);
  }

  // --- Step 5: Initialize state and command arrays ---
  // These arrays hold the position/velocity values for each joint,
  // both for current states (read from sensors) and commands (to send out).
  joint_position_state_.assign(num_joints, 0.0);
  joint_velocity_state_.assign(num_joints, 0.0);
  joint_position_command_.assign(num_joints, 0.0);
  joint_velocity_command_.assign(num_joints, 0.0);

  // --- Step 6: Set up ROS 2 communications ---
  // Subscribe to a topic publishing joint states from sensors/firmware.
  // Messages are stored safely under a mutex for later reading.
  joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    read_topic_, 10,
    [this](sensor_msgs::msg::JointState::UniquePtr msg)
    {
      // Thread-safe copy of the most recent message
      std::lock_guard<std::mutex> lock(this->latest_msg_mutex_);
      this->latest_joint_state_msg_ = std::make_shared<sensor_msgs::msg::JointState>(*msg);
    });

  // Publisher to send joint command messages (e.g., desired positions)
  joint_command_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(write_topic_, 10);

  // --- Step 7: Report success ---
  RCLCPP_INFO(node_->get_logger(), 
              "V3ArmHardware initialized: read_topic='%s', write_topic='%s'",
              read_topic_.c_str(), write_topic_.c_str());

  return CallbackReturn::SUCCESS;
}

}  // namespace v3_arm_controls

// Plugin registration will be added in a later commit
