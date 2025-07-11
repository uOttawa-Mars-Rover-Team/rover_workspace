import importlib  # To dynamically import message type

import rclpy
from rcl_interfaces.msg import ParameterDescriptor, ParameterType
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import (  # qos_profile_action_status_default # Uncomment if needed
    DurabilityPolicy,
    HistoryPolicy,
    LivelinessPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_parameter_events,
    qos_profile_parameters,
    qos_profile_sensor_data,
    qos_profile_services_default,
    qos_profile_system_default,
)

# To dynamically get topic type
from ros2topic.api import get_topic_names_and_types  # Requires ros2cli packages


class QosRelayNode(Node):
    def __init__(self):
        super().__init__("qos_relay_node")

        self.initialized_successfully = False
        self.abort_startup = False

        self.publisher_ = None
        self.subscription_ = None
        self.msg_type = None
        self.initialization_timer = None
        self.discovery_start_time = None

        # --- Declare Parameters ---
        self.declare_parameter(
            "input_topic",
            "",
            ParameterDescriptor(
                name="input_topic",
                type=ParameterType.PARAMETER_STRING,
                description="Name of the input topic to subscribe to.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_topic",
            "",
            ParameterDescriptor(
                name="output_topic",
                type=ParameterType.PARAMETER_STRING,
                description="Name of the output topic to publish to.",
                read_only=True,
            ),
        )

        self.declare_parameter(
            "discovery_timeout_sec",
            30.0,
            ParameterDescriptor(
                name="discovery_timeout_sec",
                type=ParameterType.PARAMETER_DOUBLE,
                description="Timeout for discovering input topic type (0.0 for indefinite).",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "discovery_retry_period_sec",
            1.0,
            ParameterDescriptor(
                name="discovery_retry_period_sec",
                type=ParameterType.PARAMETER_DOUBLE,
                description="Period between retries for topic type discovery.",
                read_only=True,
            ),
        )

        # New parameter for predefined QoS profile
        valid_qos_profiles = [
            "",
            "custom",
            "sensor_data",
            "system_default",
            "services_default",
            "parameters",
            "parameter_events",
        ]
        self.declare_parameter(
            "qos_profile_name",
            "",
            ParameterDescriptor(
                name="qos_profile_name",
                type=ParameterType.PARAMETER_STRING,
                description=(
                    'Name of a predefined QoS profile for the output topic (e.g., "sensor_data", "system_default"). '
                    'If empty or "custom", individual QoS parameters below will be used.'
                ),
                additional_constraints=f"Must be one of: {', '.join(valid_qos_profiles)}",
                read_only=True,
            ),
        )

        # Individual Output QoS settings (used if qos_profile_name is empty or "custom")
        self.declare_parameter(
            "output_qos_reliability",
            "reliable",
            ParameterDescriptor(
                name="output_qos_reliability",
                type=ParameterType.PARAMETER_STRING,
                description="QoS Reliability if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_durability",
            "volatile",
            ParameterDescriptor(
                name="output_qos_durability",
                type=ParameterType.PARAMETER_STRING,
                description="QoS Durability if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_history",
            "keep_last",
            ParameterDescriptor(
                name="output_qos_history",
                type=ParameterType.PARAMETER_STRING,
                description="QoS History if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_depth",
            10,
            ParameterDescriptor(
                name="output_qos_depth",
                type=ParameterType.PARAMETER_INTEGER,
                description="QoS Depth if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_liveliness",
            "automatic",
            ParameterDescriptor(
                name="output_qos_liveliness",
                type=ParameterType.PARAMETER_STRING,
                description="QoS Liveliness if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_deadline_ms",
            -1,
            ParameterDescriptor(
                name="output_qos_deadline_ms",
                type=ParameterType.PARAMETER_INTEGER,
                description="QoS Deadline (ms) if not using a predefined profile.",
                read_only=True,
            ),
        )
        self.declare_parameter(
            "output_qos_lifespan_ms",
            -1,
            ParameterDescriptor(
                name="output_qos_lifespan_ms",
                type=ParameterType.PARAMETER_INTEGER,
                description="QoS Lifespan (ms) if not using a predefined profile.",
                read_only=True,
            ),
        )

        # --- Get Parameters ---
        self.input_topic_name = (
            self.get_parameter("input_topic").get_parameter_value().string_value
        )
        # Make the topic absolute to make matching easier down the line
        if len(self.input_topic_name) > 0 and self.input_topic_name[0] != "/":
            current_namespace = self.get_namespace()
            self.input_topic_name = current_namespace + self.input_topic_name
        self.output_topic_name = (
            self.get_parameter("output_topic").get_parameter_value().string_value
        )
        self.discovery_timeout = (
            self.get_parameter("discovery_timeout_sec")
            .get_parameter_value()
            .double_value
        )
        self.discovery_retry_period = (
            self.get_parameter("discovery_retry_period_sec")
            .get_parameter_value()
            .double_value
        )

        self.qos_profile_name_val = (
            self.get_parameter("qos_profile_name").get_parameter_value().string_value
        )

        # Store individual QoS params regardless, _attempt_initialization will decide to use them
        self.qos_reliability_str = (
            self.get_parameter("output_qos_reliability")
            .get_parameter_value()
            .string_value
        )
        self.qos_durability_str = (
            self.get_parameter("output_qos_durability")
            .get_parameter_value()
            .string_value
        )
        self.qos_history_str = (
            self.get_parameter("output_qos_history").get_parameter_value().string_value
        )
        self.qos_depth_val = (
            self.get_parameter("output_qos_depth").get_parameter_value().integer_value
        )
        self.qos_liveliness_str = (
            self.get_parameter("output_qos_liveliness")
            .get_parameter_value()
            .string_value
        )
        self.qos_deadline_ms_val = (
            self.get_parameter("output_qos_deadline_ms")
            .get_parameter_value()
            .integer_value
        )
        self.qos_lifespan_ms_val = (
            self.get_parameter("output_qos_lifespan_ms")
            .get_parameter_value()
            .integer_value
        )

        if not self.input_topic_name or not self.output_topic_name:
            self.get_logger().error(
                "Critical Parameters 'input_topic' and 'output_topic' must be set."
            )
            self.abort_startup = True
            return

        self.get_logger().info(
            f"Attempting to discover type for input topic '{self.input_topic_name}'. "
            f"Timeout: {self.discovery_timeout}s, Retry period: {self.discovery_retry_period}s."
        )
        self.discovery_start_time = self.get_clock().now()
        self._attempt_initialization()  # Call once immediately

        if not self.initialized_successfully and not self.abort_startup:
            self.initialization_timer = self.create_timer(
                self.discovery_retry_period, self._attempt_initialization
            )

    def _attempt_initialization(self):
        if self.initialized_successfully or self.abort_startup:
            if self.initialization_timer:
                self.initialization_timer.cancel()
            return

        if self.discovery_timeout > 0.0:
            elapsed_time = (
                self.get_clock().now() - self.discovery_start_time
            ).nanoseconds / 1e9
            if elapsed_time > self.discovery_timeout:
                self.get_logger().error(
                    f"Timeout ({self.discovery_timeout}s) reached for topic '{self.input_topic_name}' type discovery."
                )
                self.abort_startup = True
                self.destroy_node()
                return

        if self.msg_type is None:
            self.msg_type = self._get_message_type(self.input_topic_name)

        if self.msg_type is not None:
            if self.initialization_timer:
                self.initialization_timer.cancel()
                self.initialization_timer = None

            self.get_logger().info(
                f"Msg type '{self.msg_type.__name__}' for '{self.input_topic_name}' found. Finalizing setup."
            )

            output_qos_profile = None
            use_predefined_profile = (
                self.qos_profile_name_val
                and self.qos_profile_name_val.lower() != "custom"
            )

            if use_predefined_profile:
                self.get_logger().info(
                    f"Using predefined QoS profile: '{self.qos_profile_name_val}'."
                )
                output_qos_profile = self._get_predefined_qos_profile(
                    self.qos_profile_name_val
                )
                if output_qos_profile is None:
                    self.get_logger().error(
                        f"Invalid 'qos_profile_name': '{self.qos_profile_name_val}'. Cannot proceed."
                    )
                    self.abort_startup = True
                    self.destroy_node()
                    return
                self.get_logger().info(
                    "Individual QoS parameters (output_qos_*) will be ignored."
                )
            else:
                self.get_logger().info(
                    "Using individual QoS parameters to construct profile."
                )
                output_qos_profile = self._create_qos_profile(
                    self.qos_reliability_str,
                    self.qos_durability_str,
                    self.qos_history_str,
                    self.qos_depth_val,
                    self.qos_liveliness_str,
                    self.qos_deadline_ms_val,
                    self.qos_lifespan_ms_val,
                )
                if output_qos_profile is None:
                    self.get_logger().error(
                        "Failed to create QoS profile from individual parameters."
                    )
                    self.abort_startup = True
                    self.destroy_node()
                    return

            # At this point, output_qos_profile should be valid or node should be aborting
            if output_qos_profile is None:  # Should have been caught above
                self.get_logger().error("QoS profile is unexpectedly None. Aborting.")
                self.abort_startup = True
                self.destroy_node()
                return

            try:
                self.publisher_ = self.create_publisher(
                    self.msg_type, self.output_topic_name, output_qos_profile
                )
                self.get_logger().info(
                    f"Publisher for '{self.output_topic_name}' created with chosen QoS."
                )

                subscriber_qos = QoSProfile(
                    reliability=ReliabilityPolicy.RELIABLE,
                    history=HistoryPolicy.KEEP_LAST,
                    depth=10,
                )
                self.subscription = self.create_subscription(
                    self.msg_type,
                    self.input_topic_name,
                    self.listener_callback,
                    subscriber_qos,
                )
                self.get_logger().info(f"Subscribed to '{self.input_topic_name}'.")
                self.initialized_successfully = True
                self.get_logger().info(
                    "QoS Relay Node initialization complete and operational."
                )

            except Exception as e:
                self.get_logger().error(f"Failed to create publisher/subscriber: {e}")
                self.abort_startup = True
                self.destroy_node()
        else:
            self.get_logger().info(
                f"Input topic '{self.input_topic_name}' type not yet found. Retrying..."
            )

    def _get_predefined_qos_profile(self, profile_name_str):
        profile_name_lower = profile_name_str.lower()
        profiles = {
            "sensor_data": qos_profile_sensor_data,
            "system_default": qos_profile_system_default,
            "services_default": qos_profile_services_default,
            "parameters": qos_profile_parameters,
            "parameter_events": qos_profile_parameter_events,
            # "action_status_default": qos_profile_action_status_default, # Uncomment if needed
        }
        if profile_name_lower in profiles:
            return profiles[profile_name_lower]
        else:
            self.get_logger().warn(
                f"Unknown predefined QoS profile name: '{profile_name_str}'"
            )
            return None

    def _get_message_type(self, topic_name):
        # ... (This method remains unchanged from the previous version)
        try:
            topic_names_and_types = get_topic_names_and_types(
                node=self, include_hidden_topics=False
            )
            for t_name, t_types_list in topic_names_and_types:
                if t_name == topic_name:
                    if not t_types_list:
                        self.get_logger().warn(
                            f"Topic '{topic_name}' found but no types reported for it."
                        )
                        return None
                    msg_type_str = t_types_list[0]  # Expect only one type
                    self.get_logger().debug(
                        f"Found raw message type for '{topic_name}': {msg_type_str}"
                    )
                    try:
                        module_parts = msg_type_str.split("/")
                        module_name = ".".join(module_parts[:-1])  # e.g., std_msgs.msg
                        class_name = module_parts[-1]  # e.g., String
                        module = importlib.import_module(module_name)
                        return getattr(module, class_name)
                    except Exception as e:
                        self.get_logger().error(
                            f"Could not import message type '{msg_type_str}': {e}"
                        )
                        return None
            self.get_logger().debug(
                f"Topic '{topic_name}' not found among active topics."
            )
            return None
        except Exception as e:
            self.get_logger().error(
                f"Error during topic type discovery for '{topic_name}': {e}"
            )
            return None

    def _create_qos_profile(
        self,
        reliability_str,
        durability_str,
        history_str,
        depth,
        liveliness_str,
        deadline_ms,
        lifespan_ms,
    ):
        # ... (This method remains unchanged from the previous version)
        reliability_map = {
            "reliable": ReliabilityPolicy.RELIABLE,
            "best_effort": ReliabilityPolicy.BEST_EFFORT,
        }
        durability_map = {
            "volatile": DurabilityPolicy.VOLATILE,
            "transient_local": DurabilityPolicy.TRANSIENT_LOCAL,
        }
        history_map = {
            "keep_last": HistoryPolicy.KEEP_LAST,
            "keep_all": HistoryPolicy.KEEP_ALL,
        }
        liveliness_map = {
            "automatic": LivelinessPolicy.AUTOMATIC,
            "manual_by_topic": LivelinessPolicy.MANUAL_BY_TOPIC,
        }

        try:
            reliability = reliability_map[reliability_str.lower()]
            durability = durability_map[durability_str.lower()]
            history = history_map[history_str.lower()]
            liveliness = liveliness_map[liveliness_str.lower()]
        except KeyError as e:
            self.get_logger().error(
                f"Invalid QoS string parameter value: {e}. Check your parameters."
            )
            return None

        if depth <= 0 and history == HistoryPolicy.KEEP_LAST:
            self.get_logger().warn(
                "'depth' for 'keep_last' history must be > 0. Using 1."
            )
            depth = 1
        elif history == HistoryPolicy.KEEP_ALL:
            depth = 0  # rclpy uses 0 as system default for KEEP_ALL depth

        qos_profile = QoSProfile(
            reliability=reliability,
            durability=durability,
            history=history,
            depth=depth,
            liveliness=liveliness,
        )

        if deadline_ms > 0:
            qos_profile.deadline = Duration(
                seconds=deadline_ms // 1000,
                nanoseconds=(deadline_ms % 1000) * 1_000_000,
            )
        if lifespan_ms > 0:
            qos_profile.lifespan = Duration(
                seconds=lifespan_ms // 1000,
                nanoseconds=(lifespan_ms % 1000) * 1_000_000,
            )
        return qos_profile

    def listener_callback(self, msg):
        # ... (This method remains unchanged from the previous version)
        if self.publisher_ and self.initialized_successfully:
            # self.get_logger().debug(f'Relaying message: "{msg}"', throttle_duration_sec=1.0)
            self.publisher_.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = QosRelayNode()
        if node.abort_startup:
            node.get_logger().error(
                "Node aborted startup due to critical error or missing parameters."
            )
        else:
            node.get_logger().info(
                "QoS Relay Node spinning. Waiting for initialization if not yet complete..."
            )
            rclpy.spin(node)
    except KeyboardInterrupt:
        if node:
            node.get_logger().info("KeyboardInterrupt, shutting down.")
    except Exception as e:
        if node:
            node.get_logger().fatal(f"Unhandled exception in main: {e}", exc_info=True)
        else:
            print(f"Unhandled exception before/during node creation: {e}")
    finally:
        if node:
            current_status = "shutdown"
            if (
                hasattr(node, "initialized_successfully")
                and node.initialized_successfully
            ):
                current_status = "shutdown (was initialized)"
            elif hasattr(node, "abort_startup") and node.abort_startup:
                current_status = "shutdown (aborted startup)"
            else:  # Not initialized, not explicitly aborted (e.g. timeout in spin, or early exit)
                current_status = "shutdown (initialization may not have completed)"
            node.get_logger().info(f"Node {current_status}.")
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    print("QoS Relay Node process finished.")


if __name__ == "__main__":
    main()
