#!/usr/bin/env python2

# Code from https://pyimagesearch.com/2020/12/21/detecting-aruco-markers-with-opencv-and-python/
# and http://wiki.ros.org/ROS/Tutorials/WritingPublisherSubscriber%28python%29

import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

# parameter from launch file specifying camera feed to subscribe to
PARAM_CAM_FEED = "/aruco_decoder_feed/cam_feed" 

arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
arucoParams = cv2.aruco.DetectorParameters_create()

bridge = CvBridge()

def publishCorners(data):
    pub = rospy.Publisher('cornerCoordinates', String, queue_size=10) # topic to publish corner coords
    
    frame = bridge.imgmsg_to_cv2(data, desired_encoding='passthrough') # convert ROS image to OpenCV image

    # detect ArUco markers in the input frame
    (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict, parameters=arucoParams)

    # verify at least one ArUco marker was detected
    if len(corners) > 0:
        # flatten the ArUco IDs list
        ids = ids.flatten()

        # loop over the detected ArUCo corners
        for (markerCorner, markerID) in zip(corners, ids):
            # extract the marker corners (which are always returned
            # in top-left, top-right, bottom-right, and bottom-left
            # order)
            corners = markerCorner.reshape((4, 2))
            (topLeft, topRight, bottomRight, bottomLeft) = corners

            # convert each of the (x, y)-coordinate pairs to integers
            topLeft = (int(topLeft[0]), int(topLeft[1]))
            topRight = (int(topRight[0]), int(topRight[1]))
            bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
            bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))

            topSide = abs(int(topLeft[0]) - int(topRight[0]))
            rightSide = abs(int(topRight[1]) - int(bottomRight[1]))
            bottomSide = abs(int(bottomLeft[0]) - int(bottomRight[0]))
            leftSide = abs(int(topLeft[1]) - int(bottomLeft[1]))

            # corner coordinates
            #coords = " | [TAG ID = " + str(markerID) + "] top left = " + str(topLeft) +  "; top right = " + str(topRight) + "; bottom left = " + str(bottomLeft) +  "; bottom right = " + str(bottomRight)
            
            # dimensions of tag in px
            coords = "\n[TAG ID = " + str(markerID) + "] top = " + str(topSide) + "; bottom = " + str(bottomSide) + "; left = " + str(leftSide) + "; right = " + str(rightSide)
            rospy.loginfo(rospy.get_caller_id() + coords)
            pub.publish(coords)

            # draw the bounding box of the ArUCo detection
            cv2.line(frame, topLeft, topRight, (0, 255, 0), 2)
            cv2.line(frame, topRight, bottomRight, (0, 255, 0), 2)
            cv2.line(frame, bottomRight, bottomLeft, (0, 255, 0), 2)
            cv2.line(frame, bottomLeft, topLeft, (0, 255, 0), 2)

            # compute and draw the center (x, y)-coordinates of the ArUco marker
            cX = int((topLeft[0] + bottomRight[0]) / 2.0)
            cY = int((topLeft[1] + bottomRight[1]) / 2.0)
            cv2.circle(frame, (cX, cY), 4, (0, 0, 255), -1)

            # draw the ArUco marker ID on the frame
            cv2.putText(frame, str(markerID),
                (topLeft[0], topLeft[1] - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (0, 255, 0), 2)

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

def main():
    rospy.init_node("aruco_decoder_node")
    rate = rospy.Rate(10) # 10hz

    if rospy.has_param(PARAM_CAM_FEED):
        videoCapture = rospy.get_param(PARAM_CAM_FEED)
        rospy.Subscriber(videoCapture, Image, publishCorners)
    else:
        print("No camera feed parameter!")

    rospy.spin()

if __name__ == "__main__":
    main()
    
