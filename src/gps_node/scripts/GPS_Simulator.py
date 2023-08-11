#!/usr/bin/env python
import rospy
from gps_node.msg import gps
import random

#Constants
BaseLat = 45.420593
BaseLon = -75.680621
MinCoordError = -1
MaxCoordError = 1

def executeNode():
    rate = rospy.Rate(2)
    gps_pub = rospy.Publisher("GPS", gps, queue_size=10)

    print("Started outputing simulated GPS coordinates...")

    while not rospy.is_shutdown():
        gps_data = gps()
        gps_data.fix = 1
        gps_data.satellites = 4
        gps_data.latitude = BaseLat + random.uniform(MinCoordError, MaxCoordError)
        gps_data.longitude = BaseLon + random.uniform(MinCoordError, MaxCoordError)
        
        gps_pub.publish(gps_data)

        rate.sleep()

if __name__ == "__main__":
    #need to init node before checking the rosparams
    rospy.init_node("gps_simulator", anonymous=True)

    try:
        executeNode()
    except rospy.ROSInterruptException:
        pass