#include "v3_arm_controls/v3_arm_hardware.hpp"
#include "pluginlib/class_list_macros.hpp"
#include <algorithm>

namespace v3_arm_controls
{

// ---------------------------------------------------------------------------
// Lifecycle callback: initialize the hardware interface
// ---------------------------------------------------------------------------
CallbackReturn V3ArmHardware::on_init(const hardware_interface::HardwareInfo & info)
{
  // Call base class init to populate hardware info. Return ERROR if it fails.
  if (hardware_interface::SystemInterface::on_init(info) != CallbackReturn::SUCCESS) {
    return CallbackReturn::ERROR;
  }

  // Create a regular ROS 2 node (non-lifecycle)
  // The controller manager handles lifecycle externally.
  node_ = rclcpp::Node::make_shared("v3_arm_hardware_node");

  // Declare ROS parameters for topic names, with defaults.
  // Users can override these in a YAML file or via `ros2 param set`.
  node_->declare_parameter<std::string>("read_topic", read_topic_);
  node_->declare_parameter<std::string>("write_topic", write_topic_);

  // Retrieve parameter values (overwrite defaults if set externally)
  node_->get_parameter("read_topic", read_topic_);
  node_->get_parameter("write_topic", write_topic_);

  // Extract joint information from hardware_info
  size_t num_joints = info_.joints.size();
  if (num_joints == 0) {
    RCLCPP_ERROR(node_->get_logger(), "No joints defined in hardware info.");
    return CallbackReturn::ERROR;
  }

  // Reserve and store joint names
  joint_names_.reserve(num_joints);
  for (const auto & j : info_.joints) {
    joint_names_.push_back(j.name);
  }

  // Initialize internal state and command arrays for all joints
  joint_position_state_.assign(num_joints, 0.0);
  joint_velocity_state_.assign(num_joints, 0.0);
  joint_position_command_.assign(num_joints, 0.0);
  joint_velocity_command_.assign(num_joints, 0.0);

  // Subscribe to the joint state topic from CAN router / simulation
  joint_state_sub_ = node_->create_subscription<sensor_msgs::msg::JointState>(
    read_topic_, 10,
    [this](sensor_msgs::msg::JointState::UniquePtr msg)
    {
      // Copy the incoming message to a shared pointer with thread-safety
      std::lock_guard<std::mutex> lock(this->latest_msg_mutex_);
      this->latest_joint_state_msg_ = std::make_shared<sensor_msgs::msg::JointState>(*msg);
    });

  // Publisher to send joint commands to the CAN router
  joint_command_pub_ = node_->create_publisher<sensor_msgs::msg::JointState>(write_topic_, 10);

  // Log initialization details
  RCLCPP_INFO(node_->get_logger(),
              "V3ArmHardware initialized: read_topic='%s', write_topic='%s'",
              read_topic_.c_str(), write_topic_.c_str());

  return CallbackReturn::SUCCESS;
}

// ---------------------------------------------------------------------------
// Export state interfaces (positions and velocities)
// ---------------------------------------------------------------------------
std::vector<hardware_interface::StateInterface> V3ArmHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;

  // For each joint, provide handles for position and velocity
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_state_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_state_[i]));
  }

  return state_interfaces;
}

// ---------------------------------------------------------------------------
// Export command interfaces (positions and velocities)
// ---------------------------------------------------------------------------
std::vector<hardware_interface::CommandInterface> V3ArmHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;

  // For each joint, provide handles for position and velocity commands
  for (size_t i = 0; i < joint_names_.size(); ++i) {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_POSITION, &joint_position_command_[i]));
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      joint_names_[i], hardware_interface::HW_IF_VELOCITY, &joint_velocity_command_[i]));
  }

  return command_interfaces;
}

// ---------------------------------------------------------------------------
// Read function: update joint states from the latest ROS message
// ---------------------------------------------------------------------------
hardware_interface::return_type V3ArmHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  // Lock mutex to ensure thread-safety when accessing latest_joint_state_msg_
  std::lock_guard<std::mutex> lock(latest_msg_mutex_);

  // If no message has been received yet, keep previous joint states
  if (!latest_joint_state_msg_) {
    return hardware_interface::return_type::OK;
  }

  auto & msg = *latest_joint_state_msg_;

  // If the message contains joint names, match each name to update corresponding state
  if (!msg.name.empty()) {
    for (size_t i = 0; i < joint_names_.size(); ++i) {
      auto it = std::find(msg.name.begin(), msg.name.end(), joint_names_[i]);
      if (it != msg.name.end()) {
        size_t idx = std::distance(msg.name.begin(), it);
        // Update joint position if available
        if (idx < msg.position.size()) {
          joint_position_state_[i] = msg.position[idx];
        }
        // Update joint velocity if available
        if (idx < msg.velocity.size()) {
          joint_velocity_state_[i] = msg.velocity[idx];
        }
      }
    }
  } else {
    // If joint names are not present, assume the message ordering matches our arrays
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

}  // namespace v3_arm_controls
