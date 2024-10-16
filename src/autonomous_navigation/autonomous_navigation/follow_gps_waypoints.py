import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator
from general_interfaces.action import FollowGpsWaypointsAction


class FollowGpsWaypoints(Node):
    def __init__(self):
        super().__init__("FollowGpsWaypoints")
        #initialize action server and navigator
        self.follow_gps_waypoints_ = ActionServer(self, FollowGpsWaypointsAction, "follow_gps_waypoints", execute_callback=self.nav_callback)
        self.navigator = BasicNavigator("basic_navigator")

    def nav_callback(self, goal_handle):
        """
        iterates through the waypoints and navigate to them
        """
        number_of_loops = goal_handle.request.number_of_loops
        goal_index = goal_handle.request.goal_index    
        geo_poses = goal_handle.request.geo_poses
        
        for i in range(number_of_loops):
            for pose in geo_poses[goal_index:]:
                #logic goes here 
                pass
        
        #set goal as complete once the navigation is done
        goal_handle.succeed();
        
        #send result
        result = FollowGpsWaypoints.Result()
        result.missed_waypoints = []
        result.error_code = 0
        result.error_msg = "test"


    
    def conversion(self, currentGps, currentPose):
        
        pass




        

def main(args = None):
    rclpy.init(args = args)
    node = FollowGpsWaypoints()
    rclpy.spin(node)
    rclpy.shutdown()