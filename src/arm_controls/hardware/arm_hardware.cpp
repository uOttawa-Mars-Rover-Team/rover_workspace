#include "v3_arm_controls/v3_arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <algorithm>

namespace v3_arm_controls
{

// ---------------------------------------------------------------------------
// Lifecycle initialization of the hardware interface
// This function is called once when the controller manager loads the hardware
// ---------------------------------------------------------------------------
CallbackReturn V3ArmHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  // Call base class on_init() to populate info_ from URDF / config
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Create a dedicated ROS node for topic communication
  // Using a regular node since the controller manager handles the lifecycle externally
  node_ = rclcpp::Node::make_shared("v3_arm_hardware_node");

  // Declare ROS parameters for topic names; allows them to be overridden externally
  node_->declare_parameter<std::string>("read_topic", read_topic_);
  node_->declare_parameter<std::string>("write_topic", write_topic_);
  node_->get_parameter("read_topic", read_topic_);
  node_->get_parameter("write_topic", write_topic_);

  // Verify that joints are defined in the hardware info
  size_t num_joints = info_.joints.size();
  if (num_joints == 0) {
    RCLCPP_ERROR(node_->get_logger(), "No joints defined in hardware info.");
    return CallbackReturn::ERROR;
  }

  // Store joint names for later use in read/write
  joint_names_.reserve(num_joints);
  for (const auto & j : info_.joints) {
    joint_names_.push_back(j.name);
  }

  // Allocate state and command arrays
  joint_position_state_.assign(num_joints, 0.0);
  joint_velocity_state_.assign(num_joints, 0.0);
  joint_position_command_.assign(num_joints, 0.0);
  joint_velocity_command_.assign(num_joints, 0.0);

  // -------------------------------------------------------------------------
  // ROS subscriptions and publishers
  // -------------------------------------------------------------------------
  // Subscribe to joint state topic published by CAN router
  // Incoming messages are stored in latest_joint_state_msg_ for read() to consume
  joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    read_topic_, 10,
    [this](sensor_msgs::msg::JointState::UniquePtr msg)
    {
      std::lock_guard<std::mutex> lock(this->latest_msg_mutex_);
      this->latest_joint_state_msg_ = std::make_shared<sensor_msgs::msg::JointState>(*msg);
    });

  // Publisher for joint commands to be sent over the CAN router
  joint_command_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(write_topic_, 10);

  RCLCPP_INFO(node_->get_logger(),
              "V3ArmHardware initialized: read_topic='%s', write_topic='%s'",
              read_topic_.c_str(), write_topic_.c_str());

  return CallbackReturn::SUCCESS;
}

// ---------------------------------------------------------------------------
// Expose joint state interfaces to ROS 2 controllers
// Controllers will read these arrays via hardware_interface::StateInterface
// ---------------------------------------------------------------------------
std::vector<hardware_interface::StateInterface> V3ArmHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  for (size_t i = 0; i < joint_names_.size(); ++i) {
    // Each joint exposes position and velocity
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
  }

  return state_interfaces;
}

// ---------------------------------------------------------------------------
// Expose joint command interfaces to ROS 2 controllers
// Controllers will write to these arrays via hardware_interface::CommandInterface
// ---------------------------------------------------------------------------
std::vector<hardware_interface::CommandInterface> V3ArmHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  for (size_t i = 0; i < joint_names_.size(); ++i) {
    // Each joint accepts position and velocity commands
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_command_[i]));
  }

  return command_interfaces;
}

// ---------------------------------------------------------------------------
// Read joint states from latest message
// Called periodically by the controller manager
// ---------------------------------------------------------------------------
hardware_interface::return_type V3ArmHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  std::lock_guard<std::mutex> lock(latest_msg_mutex_);

  // If no message has been received yet, retain previous joint states
  if (!latest_joint_state_msg_) {
    return hardware_interface::return_type::OK;
  }

  auto & msg = *latest_joint_state_msg_;

  if (!msg.name.empty()) {
    // Match joint names in the message to our internal joint arrays
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      auto it = std::find(msg.name.begin(), msg.name.end(), joint_names_[i]);
      if (it != msg.name.end()) {
        size_t idx = std::distance(msg.name.begin(), it);
        if (idx < msg.position.size()) {
          joint_position_state_[i] = msg.position[idx];
        }
        if (idx < msg.velocity.size()) {
          joint_velocity_state_[i] = msg.velocity[idx];
        }
      }
    }
  } else {
    // If names are empty, assume order of message arrays matches internal arrays
    size_t min_pos = std::min(msg.position.size(), joint_position_state_.size());
    for (size_t i = 0; i < min_pos; ++i) {
      joint_position_state_[i] = msg.position[i];
    }

    size_t min_vel = std::min(msg.velocity.size(), joint_velocity_state_.size());
    for (size_t i = 0; i < min_vel; ++i) {
      joint_velocity_state_[i] = msg.velocity[i];
    }
  }

  return hardware_interface::return_type::OK;
}

// ---------------------------------------------------------------------------
// Write joint commands to ROS topic
// Called periodically by the controller manager
// ---------------------------------------------------------------------------
hardware_interface::return_type V3ArmHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Construct a JointState message from the command arrays
  sensor_msgs::msg::JointState cmd_msg;
  cmd_msg.header.stamp = node_->now();  // timestamp the message
  cmd_msg.name = joint_names_;           // joint names
  cmd_msg.position = joint_position_command_; // commanded positions
  cmd_msg.velocity = joint_velocity_command_; // commanded velocities

  // Publish non-blocking (will be sent over CAN router)
  if (joint_command_pub_) {
    joint_command_pub_->publish(cmd_msg);
  }

  return hardware_interface::return_type::OK;
}

}  // namespace v3_arm_controls
