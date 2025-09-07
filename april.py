#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from tf2_ros import Buffer, TransformListener
from rclpy.duration import Duration


def yaw_from_quat(q):
    # Planar yaw from quaternion (x,y,z,w)
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def quat_from_yaw(yaw):
    half = 0.5 * yaw
    from geometry_msgs.msg import Quaternion

    return Quaternion(x=0.0, y=0.0, z=math.sin(half), w=math.cos(half))


class AprilTagFollower(Node):
    def __init__(self):
        super().__init__("april_tag_follower_goal_pub")
        self.declare_parameter("target_frame", "base")
        self.declare_parameter("global_frame", "map")
        self.declare_parameter("follow_distance", 0.0)
        self.declare_parameter("goal_topic", "goal_update")
        self.declare_parameter("publish_rate", 8.0)

        self.target_frame = (
            self.get_parameter("target_frame").get_parameter_value().string_value
        )
        self.global_frame = (
            self.get_parameter("global_frame").get_parameter_value().string_value
        )
        self.follow_distance = (
            self.get_parameter("follow_distance").get_parameter_value().double_value
        )
        goal_topic = self.get_parameter("goal_topic").get_parameter_value().string_value
        rate = self.get_parameter("publish_rate").get_parameter_value().double_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.pub = self.create_publisher(PoseStamped, goal_topic, 10)
        self.timer = self.create_timer(1.0 / max(rate, 0.1), self.tick)

        self.last_goal = None
        self.alpha = 0.3  # low-pass smoothing

    def tick(self):
        now = rclpy.time.Time()
        try:
            # lookup tag in the global frame
            tf = self.tf_buffer.lookup_transform(
                self.global_frame, self.target_frame, now, timeout=Duration(seconds=0.1)
            )
        except Exception as e:
            self.get_logger().info(f"TF lookup failed: {e}")
            return

        tx = tf.transform.translation.x
        ty = tf.transform.translation.y
        q = tf.transform.rotation
        tag_yaw = yaw_from_quat(q)

        # Goal is behind the tag along its -x axis by follow_distance
        gx = tx - self.follow_distance * math.cos(tag_yaw)
        gy = ty - self.follow_distance * math.sin(tag_yaw)

        # Face the tag
        goal_yaw = math.atan2(ty - gy, tx - gx)

        # Optional smoothing to reduce jitter
        if self.last_goal is not None:
            gx = self.alpha * gx + (1.0 - self.alpha) * self.last_goal[0]
            gy = self.alpha * gy + (1.0 - self.alpha) * self.last_goal[1]
            goal_yaw = self.alpha * goal_yaw + (1.0 - self.alpha) * self.last_goal[2]

        goal = PoseStamped()
        goal.header.stamp = self.get_clock().now().to_msg()
        goal.header.frame_id = self.global_frame
        goal.pose.position.x = gx
        goal.pose.position.y = gy
        goal.pose.orientation = quat_from_yaw(goal_yaw)

        self.pub.publish(goal)
        self.last_goal = (gx, gy, goal_yaw)


def main():
    rclpy.init()
    node = AprilTagFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
