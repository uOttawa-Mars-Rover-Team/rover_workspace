#!/usr/bin/env python2

# Code from https://pyimagesearch.com/2020/12/21/detecting-aruco-markers-with-opencv-and-python/
# and http://wiki.ros.org/ROS/Tutorials/WritingPublisherSubscriber%28python%29

import rospy
from std_msgs.msg import String
import argparse
import time
import cv2
import sys

#def publishCorners(tl, tr, bl, br):
#    pub = rospy.Publisher('cornerCoordinates', String, queue_size=10)
#    rospy.init_node('aruco_decoder_node', anonymous=True)
#    rate = rospy.Rate(10) # 10hz
#    while not rospy.is_shutdown():
#        coords = "Top left = " + tl + "; top right = " + tr + "; bottom left = " + bl + "; bottom right = " + br
#        rospy.loginfo(coords)
#        pub.publish(coords)
#        rate.sleep()

arucoDict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
arucoParams = cv2.aruco.DetectorParameters_create()

# initialize the video stream and allow the camera sensor to warm up
print("Starting video stream")
videoCapture = cv2.VideoCapture(0)
time.sleep(2.0)

# loop over the frames from the video stream
while True:
	# grab the frame from the threaded video stream
    ret, frame = videoCapture.read()
    if not ret:
        print("Can't receive frame")
        break

    # detect ArUco markers in the input frame
    (corners, ids, rejected) = cv2.aruco.detectMarkers(frame, arucoDict, parameters=arucoParams)

    # verify *at least* one ArUco marker was detected
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
		    topRight = (int(topRight[0]), int(topRight[1]))
		    bottomRight = (int(bottomRight[0]), int(bottomRight[1]))
		    bottomLeft = (int(bottomLeft[0]), int(bottomLeft[1]))
		    topLeft = (int(topLeft[0]), int(topLeft[1]))

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

        # publish the corner coordinates for the marker
#        publishCorners(topLeft, topRight, bottomLeft, bottomRight)

    # show the output frame
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

videoCapture.release()
cv2.destroyAllWindows()
