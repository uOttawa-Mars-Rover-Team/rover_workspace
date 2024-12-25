import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped, Point, Pose, Quaternion
from geographic_msgs.msg import GeoPose, GeoPoint
from general_interfaces.action import FollowGpsWaypointsAction
from std_msgs.msg import Header, UInt32
from robot_localization.srv import FromLL
import time


'''
this is what I used to test in command line:

ros2 action send_goal /follow_gps_waypoints general_interfaces/action/FollowGpsWaypointsAction \
"{
  number_of_loops: 1,
  goal_index: 0,
  gps_poses: [
    {position: {latitude: 37.7749, longitude: -122.4194, altitude: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}},
    {position: {latitude: 34.0522, longitude: -118.2437, altitude: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}
  ]
}"




'''


class FollowGpsWaypoints(Node):
    def __init__(self):
        super().__init__("FollowGpsWaypoints")
        #initialize action server and navigator
        self.follow_gps_waypoints_ = ActionServer(self, FollowGpsWaypointsAction, "follow_gps_waypoints", execute_callback=self.nav_callback)
        self.navigator = BasicNavigator("basic_navigator")
        


    def convert_and_navigate(self, client, geoPose:GeoPose, count): 
        #extracts the geopoint from the geopose message
        point: GeoPoint = geoPose.position
        orientation: Quaternion = geoPose.orientation
        seq = count
        #write some more logic to add the metadata for the posestamped header
        
        #make the request for the FromLL service
        request = FromLL.Request()
        request.ll_point = point
        future = client.call_async(request)
        future.add_done_callback(lambda future: self.go_to_pose_callback(future, orientation, seq))

    def go_to_pose_callback(self, future, orientation: Quaternion, seq):
        #convert from point to posestamped, this needs orientation to become pose, then metadata to become posestamped
        point: Point = future.result()
        orientation: Quaternion = orientation

        #initialize the pose message type
        pose: Pose = Pose()
        pose.position = point
        pose.orientation = orientation
        
        # initializing the header
        header: Header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.seq = seq
        header.frame_id = "map"

        #make the poseStamped message
        #initialize the poseStamped
        pose_stamped: PoseStamped = PoseStamped()
        pose_stamped.pose = pose
        pose_stamped.header = header

        #go put the converted one in
        self.navigator.goToPose(pose_stamped)
        #logic goes here do something with self.navigator.isTaskComplete()

    def nav_callback(self, goal_handle):
        """
        iterates through the waypoints and navigate to them
        """
        number_of_loops = goal_handle.request.number_of_loops
        goal_index = goal_handle.request.goal_index    
        geo_poses = goal_handle.request.gps_poses
        client = self.create_client(FromLL, "FromLL")

        for i in range(number_of_loops):
            count = 0
            for pose in geo_poses[goal_index:]:
                #this converts and navigates, 
                self.convert_and_navigate(client, pose, count)
  
                #send feedback
                self.get_logger().info("Currently on waypoint #" + str(count));

                feedback = FollowGpsWaypointsAction.Feedback()  
                feedback.current_waypoint = count 
                goal_handle.publish_feedback(feedback)
                count += 1
        
        #set goal as complete once the navigation is done
        goal_handle.succeed();    

        #send result
        result = FollowGpsWaypointsAction.Result()
        result.missed_waypoints = []
        result.error_code = 0
        result.error_msg = "test"
        return result

def main(args = None):
    rclpy.init(args = args)
    node = FollowGpsWaypoints()
    rclpy.spin(node)
    rclpy.shutdown()