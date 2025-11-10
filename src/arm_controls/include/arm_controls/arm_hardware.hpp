#ifndef V3_ARM_CONTROLS__V3_ARM_HARDWARE_HPP_
#define V3_ARM_CONTROLS__V3_ARM_HARDWARE_HPP_

// --- Standard library includes ---
#include <string>   // For std::string (topic names, joint names, etc.)
#include <vector>   // For dynamic arrays to hold joint data
#include <mutex>    // For thread-safe access to shared data (latest joint state)

// --- ROS 2 core includes ---
#include "rclcpp/rclcpp.hpp"  // Core ROS 2 C++ API for creating nodes, publishers, subscribers
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
// Lifecycle interface provides standardized callbacks like on_init(), on_configure(), etc.

// --- ROS 2 Control framework includes ---
#include "hardware_interface/system_interface.hpp"
// Base class that defines the SystemInterface API; we subclass this to represent the hardware

#include "hardware_interface/types/hardware_interface_return_values.hpp"
// Provides standard return codes (OK, ERROR, etc.) for hardware interface functions

#include "hardware_interface/hardware_info.hpp"
// Describes the hardware configuration loaded from the robot’s .yaml/.urdf description

#include "hardware_interface/handle.hpp"
// Represents command and state interfaces (position, velocity, effort, etc.)

// --- ROS 2 message type for joint states ---
#include "sensor_msgs/msg/joint_state.hpp"
// Standard ROS 2 message with joint names, positions, velocities, and efforts

namespace v3_arm_controls
{

// Convenience alias: used for lifecycle callback return values
// (e.g., CallbackReturn::SUCCESS or CallbackReturn::ERROR)
using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn;

/**
 * @brief A ROS 2 Control SystemInterface implementation for the V3 robotic arm.
 *
 * This class acts as the bridge between the ROS 2 control framework (controllers)
 * and the physical or simulated robot hardware. It exposes the robot’s joint states
 * and accepts control commands through standardized interfaces.
 *
 * In this design, instead of directly communicating with low-level hardware,
 * the interface publishes and subscribes to ROS topics:
 *   - It subscribes to a topic providing joint state updates (`read_topic_`)
 *   - It publishes joint command messages to another topic (`write_topic_`)
 *
 * These topics can be connected to an external communication layer (e.g., CAN, serial,
 * or another ROS node that talks to the actual arm).
 */
class V3ArmHardware : public hardware_interface::SystemInterface
{
public:
  // Default constructor and destructor
  V3ArmHardware() = default;
  ~V3ArmHardware() override = default;

  /**
   * @brief Called when the hardware interface is first initialized.
   *
   * Loads hardware info (from URDF/YAML), creates a ROS 2 node for communication,
   * sets up publishers/subscribers, and allocates memory for joint data.
   */
  CallbackReturn on_init(const hardware_interface::HardwareInfo & info) override;

  /**
   * @brief Exposes the current state of each joint to the ROS 2 control manager.
   *
   * Each joint typically provides at least position and velocity state interfaces.
   * Controllers read these to know the current status of the robot.
   */
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

  /**
   * @brief Exposes the command interfaces for each joint.
   *
   * Controllers use these interfaces to send commands (like target positions or velocities)
   * to the robot, which are then transmitted in write().
   */
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override;

  /**
   * @brief Reads the latest sensor data from the hardware (or subscribed topic).
   *
   * Called periodically by the controller manager. It should update the internal
   * joint state arrays with the latest values.
   *
   * @param time   Current ROS time
   * @param period Time elapsed since last read()
   */
  hardware_interface::return_type read(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

  /**
   * @brief Writes the latest commands to the hardware (or publishes them as ROS messages).
   *
   * Called periodically after controllers have updated the command interfaces.
   * This function should take the current joint command arrays and send them to the robot.
   *
   * @param time   Current ROS time
   * @param period Time elapsed since last write()
   */
  hardware_interface::return_type write(
    const rclcpp::Time & time, const rclcpp::Duration & period) override;

private:
  // ---------------------------------------------------------------------------
  // Configuration
  // ---------------------------------------------------------------------------

  /**
   * @brief ROS topic name for reading joint states (sensor data).
   *
   * Defaults to "can_router/joint_states", but can be overridden by ROS parameters
   * at runtime or via YAML configuration.
   */
  std::string read_topic_ = "can_router/joint_states";

  /**
   * @brief ROS topic name for publishing joint commands.
   *
   * Defaults to "can_router/joint_commands". Controllers write commands here.
   */
  std::string write_topic_ = "can_router/joint_commands";

  // ---------------------------------------------------------------------------
  // Joint data storage
  // ---------------------------------------------------------------------------

  /**
   * @brief Current measured positions of each joint (populated in read()).
   */
  std::vector<double> joint_position_state_;

  /**
   * @brief Current measured velocities of each joint (populated in read()).
   */
  std::vector<double> joint_velocity_state_;

  /**
   * @brief Commanded target positions for each joint (populated by controllers).
   */
  std::vector<double> joint_position_command_;

  /**
   * @brief Commanded target velocities for each joint (populated by controllers).
   */
  std::vector<double> joint_velocity_command_;

  /**
   * @brief Names of all joints, extracted from the hardware info provided by ROS 2 Control.
   *
   * Used to match joint names with those in incoming JointState messages.
   */
  std::vector<std::string> joint_names_;

  // ---------------------------------------------------------------------------
  // ROS 2 Communication Handles
  // ---------------------------------------------------------------------------

  /**
   * @brief Shared pointer to a regular ROS 2 node used for topic-based communication.
   *
   * The node is used to:
   *  - Subscribe to the read topic (`joint_state_sub_`)
   *  - Publish to the write topic (`joint_command_pub_`)
   *
   * Note: The ROS 2 Control framework manages the lifecycle externally,
   * so this node does not need to be a LifecycleNode.
   */
  rclcpp::Node::SharedPtr node_ = nullptr;

  /**
   * @brief Subscription handle for receiving joint state messages.
   *
   * Messages are of type `sensor_msgs::msg::JointState`.
   * When new data arrives, it updates `latest_joint_state_msg_`.
   */
  rclcpp::Subscription<sensor_msgs::msg::JointState>::SharedPtr joint_state_sub_;

  /**
   * @brief Publisher handle for sending joint command messages.
   *
   * Also uses `sensor_msgs::msg::JointState`, containing command positions and velocities.
   */
  rclcpp::Publisher<sensor_msgs::msg::JointState>::SharedPtr joint_command_pub_;

  // ---------------------------------------------------------------------------
  // Thread-safe message storage
  // ---------------------------------------------------------------------------

  /**
   * @brief Pointer to the most recent JointState message received from the subscription.
   *
   * This is shared across threads: one thread handles message reception (subscriber callback),
   * while another periodically reads from it in `read()`.
   */
  sensor_msgs::msg::JointState::SharedPtr latest_joint_state_msg_;

  /**
   * @brief Mutex to protect access to `latest_joint_state_msg_`.
   *
   * Ensures that read() and the subscriber callback never access it simultaneously.
   */
  std::mutex latest_msg_mutex_;
};

}  // namespace v3_arm_controls

#endif  // V3_ARM_CONTROLS__V3_ARM_HARDWARE_HPP_
