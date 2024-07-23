import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
from std_msgs.msg import String
import threading

class soilCollection(Node):
    def __init__(self):
        super().__init__("MCU_interface_node")
        #Publisher Setup:
        self.soilCollectionPub = self.create_publisher(String, "soil_collection", 10)
        self.vacuumTubeControlPub = self.create_publisher(String, "vacuum_tube_control", 10)
        self.weatherStationPub = self.create_publisher(String, "weather_station", 10)
        self.soilTestingPub = self.create_publisher(String, "soil_testing", 10)
        #Subscribers Setup:
        #self.soilTestingSub = self.create_subscription(String, "soil_data", 10)
        #self.weatherStationSub = self.create_subscription(String, "weather_data", 10)

    def collectCache(self):
        msg = String()
        msg.data = "1"
        self.soilCollectionPub.publish(msg)
    def collectSoilData(self):
        msg = String()
        msg.data = "2"
        self.soilCollectionPub.publish(msg)

    def moveVacDown(self):
        msg = String()
        msg.data = "3"
        self.vacuumTubeControlPub.publish(msg)
    def moveVacUp(self):
        msg = String()
        msg.data = "4"
        self.vacuumTubeControlPub.publish(msg)
    def stopVacMove(self):
        msg = String()
        msg.data = "5"
        self.vacuumTubeControlPub.publish(msg)
    def toggleVac(self):
        msg = String()
        msg.data = "6"
        self.vacuumTubeControlPub.publish(msg)

    def collectWeatherData(self):
        msg = String()
        msg.data = "7"
        self.weatherStationPub.publish(msg)
        
    def initiate(args=None):
    	rclpy.init(args=args)
    	soilCollectionNode = soilCollection()
    	thread = threading.Thread(target = rclpy.spin, args=[soilCollectionNode])
    	thread.start()
    	return soilCollectionNode
    	
    	#soilCollection.destroy_node()
    	#rclpy.shutdown()
    	#thread.join()


