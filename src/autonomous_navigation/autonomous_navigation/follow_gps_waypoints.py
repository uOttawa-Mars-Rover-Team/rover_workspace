from functools import partial
import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import GeoPose
from general_interfaces.action import FollowGpsWaypointsAction
from robot_localization.srv import FromLL


class FollowGpsWaypoints(Node):
    def __init__(self):
        super().__init__("FollowGpsWaypoints")
        #initialize action server and navigator
        self.follow_gps_waypoints_ = ActionServer(self, FollowGpsWaypointsAction, "follow_gps_waypoints", execute_callback=self.nav_callback)
        self.navigator = BasicNavigator("basic_navigator")
        


    def convert_and_navigate(self, client, geoPose:GeoPose): 
        #extracts the geopoint from the geopose message
        geopoint = geoPose.position
        #write some more logic to add the metadata for the posestamped header
        #write some more logic to extract the oreintation from geopoint 

        #make the request for the FromLL service
        request = FromLL.Request()
        request.ll_point = geopoint
        future = client.call_async(request)
        future.add_done_callback(partial(self.go_to_pose_callback))

    def go_to_pose_callback(self, future):
        #may just do smoething else instead of add_done_callback to contain the conversion inside the function and then navigate


        #convert from point to posestamped, this needs orientation to become pose, then metadata to become posestamped
        point = future.result()


        #go put the converted one in
        self.navigator.goToPose()
        #logic goes here do something with self.navigator.isTaskComplete()

    def nav_callback(self, goal_handle):
        """
        iterates through the waypoints and navigate to them
        """
        number_of_loops = goal_handle.request.number_of_loops
        goal_index = goal_handle.request.goal_index    
        geo_poses = goal_handle.request.geo_poses
        client = self.create_client(FromLL, "FromLL")

        for i in range(number_of_loops):
            count = 0
            for pose in geo_poses[goal_index:]:
                #this converts and navigates, 
                self.convert_and_navigate(client, pose)
  
                #send feedback
                self.get_logger.info("Currently on waypoint #" + count);
                goal_handle.publish_feedback(count)
                count += 1
                pass
        
        #set goal as complete once the navigation is done
        goal_handle.succeed();    

        #send result
        result = FollowGpsWaypoints.Result()
        result.missed_waypoints = []
        result.error_code = 0
        result.error_msg = "test"
        return result

def main(args = None):
    rclpy.init(args = args)
    node = FollowGpsWaypoints()
    rclpy.spin(node)
    rclpy.shutdown()