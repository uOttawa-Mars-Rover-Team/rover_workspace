#!/usr/bin/env python
import rospy
from gps_node.msg import gps
import time

class GPSWaypointRecorder:

    def __init__(self):
        self.mostRecentGPSMsg = gps

    def gpsMsgHandler(self, msg):
        self.mostRecentGPSMsg = msg

    def executeNode(self):
        # rate = rospy.Rate(2)
        gps_sub = rospy.Subscriber("GPS", gps, queue_size=10, callback=self.gpsMsgHandler)

        print("Started listening for GPS messages...")

        filename = time.strftime("GPSWaypointRecording_%d-%m-%Y_%H:%M:%S.csv")

        print("Saving waypoints in '" + filename + "'")

        print("\nHit enter to record a waypoint. Optionally, you may also enter a message to be stored with the waypoint. Enter 'q' to quit.")
        with open(filename, "w") as file:
            file.write("Timestamp, Latitude, Longitude, Message,\n")

            isQuit = False
            while (not rospy.is_shutdown() and not isQuit):
                #when we move to Python 3 this will change to just input()
                text = raw_input("Enter message/hit enter:")
                if text is 'q':
                    isQuit = True
                else:
                    timestamp = time.strftime("%H:%M:%S")

                    gps_msg = self.mostRecentGPSMsg
                    file.write(timestamp + ", " + str(gps_msg.latitude) + ", " + str(gps_msg.longitude) + ", " + text + ",\n")

                    print("Waypoint at (" + str(gps_msg.latitude) + ", " + str(gps_msg.longitude) + ") saved.")

if __name__ == "__main__":
    #need to init node before checking the rosparams
    rospy.init_node("gps_waypoint_recorder", anonymous=True)

    recorderNode = GPSWaypointRecorder()

    try:
        recorderNode.executeNode()
    except rospy.ROSInterruptException:
        pass