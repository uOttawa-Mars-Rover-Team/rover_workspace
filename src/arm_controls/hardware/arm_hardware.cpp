#include "v3_arm_controls/v3_arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <algorithm>

namespace v3_arm_controls
{

CallbackReturn V3ArmHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Create a node to handle topic comms. Use a non-lifecycle node here for simplicity;
  // the ros2_control SystemInterface / controller manager lifecycle handles lifecycle externally.
  node_ = rclcpp::Node::make_shared("v3_arm_hardware_node");

  // Read parameter overrides from the node (allow external param setting)
  // Note: callers can set these params via a YAML file or ros2 param set before spinning.
  node_->declare_parameter<std::string>("read_topic", read_topic_);
  node_->declare_parameter<std::string>("write_topic", write_topic_);
  node_->get_parameter("read_topic", read_topic_);
  node_->get_parameter("write_topic", write_topic_);

  // Extract joint names and allocate arrays
  size_t num_joints = info_.joints.size();
  if (num_joints == 0) {
    RCLCPP_ERROR(node_->get_logger(), "No joints defined in hardware info.");
    return CallbackReturn::ERROR;
  }

  joint_names_.reserve(num_joints);
  for (const auto & j : info_.joints) {
    joint_names_.push_back(j.name);
  }

  joint_position_state_.assign(num_joints, 0.0);
  joint_velocity_state_.assign(num_joints, 0.0);
  joint_position_command_.assign(num_joints, 0.0);
  joint_velocity_command_.assign(num_joints, 0.0);

  // ROS comms: subscribe to state topic and publish commands
  joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    read_topic_, 10,
    [this](sensor_msgs::msg::JointState::UniquePtr msg)
    {
      std::lock_guard<std::mutex> lk(this->latest_msg_mutex_);
      this->latest_joint_state_msg_ = std::make_shared<sensor_msgs::msg::JointState>(*msg);
    });

  joint_command_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(write_topic_, 10);

  RCLCPP_INFO(node_->get_logger(), "V3ArmHardware initialized: read_topic='%s' write_topic='%s'",
              read_topic_.c_str(), write_topic_.c_str());

  return CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> V3ArmHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
  }
  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> V3ArmHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_command_[i]));
  }
  return command_interfaces;
}

hardware_interface::return_type V3ArmHardware::read(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Copy the latest joint_state message (if any) into our state arrays
  std::lock_guard<std::mutex> lk(latest_msg_mutex_);
  if (!latest_joint_state_msg_) {
    // No message received yet: don't fail, just keep previous state
    return hardware_interface::return_type::OK;
  }

  auto & msg = *latest_joint_state_msg_;

  // Match names to our joints. If message contains matching names, update values.
  // If msg.name is empty but arrays are present, assume ordering matches.
  if (!msg.name.empty()) {
    // for each joint in our list, find in msg.name
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
    // no names -> assume ordering
    size_t min_pos = std::min(msg.position.size(), joint_position_state_.size());
    for (size_t i = 0; i < min_pos; ++i) joint_position_state_[i] = msg.position[i];

    size_t min_vel = std::min(msg.velocity.size(), joint_velocity_state_.size());
    for (size_t i = 0; i < min_vel; ++i) joint_velocity_state_[i] = msg.velocity[i];
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type V3ArmHardware::write(const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Build a JointState message from our command arrays and publish
  sensor_msgs::msg::JointState cmd_msg;
  cmd_msg.header.stamp = node_->now();
  cmd_msg.name = joint_names_;
  cmd_msg.position = joint_position_command_;
  cmd_msg.velocity = joint_velocity_command_;

  // publish (non-blocking)
  if (joint_command_pub_) {
    joint_command_pub_->publish(cmd_msg);
  }

  return hardware_interface::return_type::OK;
}

} // namespace v3_arm_controls

PLUGINLIB_EXPORT_CLASS(v3_arm_controls::V3ArmHardware, hardware_interface::SystemInterface)
