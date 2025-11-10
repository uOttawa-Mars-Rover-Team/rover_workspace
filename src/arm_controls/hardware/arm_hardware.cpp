#include "v3_arm_controls/v3_arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <algorithm>

namespace v3_arm_controls
{

// ------------------------------------------------------------
// on_init(): Called once when the hardware interface is created
// ------------------------------------------------------------
CallbackReturn V3ArmHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  // Let the base SystemInterface handle its own initialization logic.
  // If that fails, return an error immediately.
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Create a standard ROS 2 node for publishing/subscribing topics.
  // We use a non-lifecycle node here, since lifecycle behavior is managed
  // externally by the controller manager.
  node_ = rclcpp::Node::make_shared("v3_arm_hardware_node");

  // Declare ROS 2 parameters for the topic names, allowing overrides from YAML
  // or the command line. Then read them into the member variables.
  node_->declare_parameter<std::string>("read_topic", read_topic_);
  node_->declare_parameter<std::string>("write_topic", write_topic_);
  node_->get_parameter("read_topic", read_topic_);
  node_->get_parameter("write_topic", write_topic_);

  // Determine how many joints are defined in the hardware info file (URDF / YAML).
  size_t num_joints = info_.joints.size();
  if (num_joints == 0) {
    RCLCPP_ERROR(node_->get_logger(), "No joints defined in hardware info.");
    return CallbackReturn::ERROR;
  }

  // Save joint names for later use when exporting interfaces.
  joint_names_.reserve(num_joints);
  for (const auto & j : info_.joints) {
    joint_names_.push_back(j.name);
  }

  // Initialize all joint state and command arrays to 0.0.
  // These arrays hold live values for each joint’s position and velocity.
  joint_position_state_.assign(num_joints, 0.0);
  joint_velocity_state_.assign(num_joints, 0.0);
  joint_position_command_.assign(num_joints, 0.0);
  joint_velocity_command_.assign(num_joints, 0.0);

  // Create a subscriber for the joint state topic.
  // Whenever a new message is received, store it in latest_joint_state_msg_.
  // A mutex protects access because read() may be called from another thread.
  joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    read_topic_, 10,
    [this](sensor_msgs::msg::JointState::UniquePtr msg)
    {
      std::lock_guard<std::mutex> lock(this->latest_msg_mutex_);
      this->latest_joint_state_msg_ = std::make_shared<sensor_msgs::msg::JointState>(*msg);
    });

  // Create a publisher for the command topic.
  // The write() method will publish desired joint commands here.
  joint_command_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(write_topic_, 10);

  // Log initialization success and the active topics.
  RCLCPP_INFO(node_->get_logger(),
              "V3ArmHardware initialized: read_topic='%s', write_topic='%s'",
              read_topic_.c_str(), write_topic_.c_str());

  return CallbackReturn::SUCCESS;
}

// ---------------------------------------------------------------------------
// export_state_interfaces(): Expose the joint state variables (read-only)
// ---------------------------------------------------------------------------
std::vector<hardware_interface::StateInterface> V3ArmHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  // Each joint exposes a position and velocity state interface.
  // These are used by controllers to read the robot’s current state.
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
  }

  return state_interfaces;
}

// ---------------------------------------------------------------------------
// export_command_interfaces(): Expose the joint command variables (writable)
// ---------------------------------------------------------------------------
std::vector<hardware_interface::CommandInterface> V3ArmHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  // Each joint exposes a position and velocity command interface.
  // Controllers write desired values into these, and write() will send them to hardware.
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_command_[i]));
  }

  return command_interfaces;
}

}  // namespace v3_arm_controls
