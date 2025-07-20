#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from sensor_msgs.msg import NavSatFix
from geometry_msgs.msg import Point, PoseStamped
from nav2_msgs.action import NavigateToPose
from action_msgs.msg import GoalStatus

from robot_localization.srv import FromLL

class GpsWaypointFollower(Node):
    def __init__(self):
        super().__init__('gps_waypoint_follower')
        self.declare_parameter('goal_topic', '/gps_goal')
        self.goal_active = False
        self.goal_handle = None
        
        goal_topic = self.get_parameter('goal_topic').value
        self.goal_sub = self.create_subscription(NavSatFix, goal_topic, self.goal_callback, 10)
        self.from_ll_client = self.create_client(FromLL, '/fromLL')
        while not self.from_ll_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('FromLL service not available, waiting again...')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def goal_callback(self, msg):
        """Callback for when a new GPS goal is received."""
        if self.goal_active:
            self.get_logger().warn('A goal is already active. New goal rejected.')
            return

        self.get_logger().info(f'Received new GPS goal: Lat={msg.latitude}, Lon={msg.longitude}')
        
        # --- MODIFIED: We no longer wait here. We send the request and attach a callback. ---
        self.convert_ll_to_map(msg.latitude, msg.longitude)
        # The goal_callback now finishes immediately, freeing up the thread.

    def convert_ll_to_map(self, latitude, longitude):
        """Sends an async request to convert lat/lon and attaches a callback."""
        request = FromLL.Request()
        request.ll_point.latitude = latitude
        request.ll_point.longitude = longitude
        request.ll_point.altitude = 0.0

        # --- MODIFIED: No more spin_until_future_complete ---
        # Instead, send the request and add a "done" callback to handle the response
        future = self.from_ll_client.call_async(request)
        future.add_done_callback(self.service_done_callback)

    def service_done_callback(self, future):
        """
        --- NEW: This function is called ONLY when the /from_ll service responds. ---
        This is where we process the result and send the goal to Nav2.
        """
        try:
            response = future.result()
            map_point = response.map_point
            self.get_logger().info(f'Successfully converted to map coordinates: x={map_point.x}, y={map_point.y}')

            # Now that we have the map point, we can proceed to send the Nav2 goal.
            self.goal_active = True
            self.send_nav2_goal(map_point)

        except Exception as e:
            self.get_logger().error(f'Service call failed with exception: {e}')
            # Make sure to reset the state if the conversion fails
            self.goal_active = False

    # The rest of the functions for Nav2 actions remain the same
    def send_nav2_goal(self, map_point):
        # ... (this function is unchanged)
        goal_msg = NavigateToPose.Goal()
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = 'map'
        pose.pose.position.x = map_point.x
        pose.pose.position.y = map_point.y
        pose.pose.position.z = 0.0
        pose.pose.orientation.w = 1.0
        goal_msg.pose = pose
        self.get_logger().info('Sending goal to Nav2...')
        self._action_client.wait_for_server()
        send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        send_goal_future.add_done_callback(self.goal_response_callback)

    def feedback_callback(self, feedback_msg):
        # ... (unchanged)
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Navigating... Distance remaining: {feedback.distance_remaining:.2f} meters')

    def goal_response_callback(self, future):
        # ... (unchanged)
        self.goal_handle = future.result()
        if not self.goal_handle.accepted:
            self.get_logger().error('Goal was rejected by the server.')
            self.goal_active = False
            return
        self.get_logger().info('Goal accepted! Robot is on its way.')
        get_result_future = self.goal_handle.get_result_async()
        get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        # ... (unchanged)
        result = future.result().result
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('Goal reached successfully!')
        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error('Goal was aborted by the server.')
        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn('Goal was canceled.')
        else:
            self.get_logger().error('Unknown goal status.')
        self.get_logger().info('Resetting state. Ready for new goal.')
        self.goal_active = False
        self.goal_handle = None

# ... (main function is unchanged)
def main(args=None):
    rclpy.init(args=args)
    node = GpsWaypointFollower()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
