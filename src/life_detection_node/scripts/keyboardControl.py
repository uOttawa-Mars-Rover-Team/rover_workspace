#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from std_msgs.msg import Empty
from std_msgs.msg import UInt8
from pynput import keyboard

rospy.init_node('LifeDetectionControl')
VacHosePub = rospy.Publisher('VacHoseCMD', String, queue_size=10)
FunnelFlapPub = rospy.Publisher('FunnelFlapCMD', Empty, queue_size=10)
VacMotorPub = rospy.Publisher('VacMotorCMD', Empty, queue_size=10)
BeakerPub = rospy.Publisher('BeakerCMD', String, queue_size= 10)
AgitatePub = rospy.Publisher('AgitateCMD', String, queue_size= 10)
WeatherCollectionPub = rospy.Publusher('WeatherCollectionCMD', Empty, queue_size= 10)

keyPressed = False

def on_key_release(key):
    global keyPressed
    key = repr(key)
    if (key == "<Key.up: <65362>>"):
        VacHosePub.publish("StopUpMove")
    if (key == "<Key.down: <65364>>"):
        VacHosePub.publish("StopDownMove")
    if (key == "u'a'"):
    	AgitatePub.publish("StopAgitation")
    keyPressed = False

def on_key_press(key):
    global keyPressed
    key = repr(key)
    key = key.replace("'", "")
    key = key.replace("u", "")
    if keyPressed == False:
        if (key == "x"):
            exit()
        elif (key == "<Key.up: <65362>>"):
            VacHosePub.publish("StartUpMove")
        elif (key == "<Key.down: <65364>>"):
            VacHosePub.publish("StartDownMove")
        elif (key == "f"):
	    rospy.loginfo("funnel flapped")
            FunnelFlapPub.publish(Empty())
        elif (key == "v"):
	    rospy.loginfo("vaccumed")
            VacMotorPub.publish(Empty())
        elif (key == "a"):
            AgitatePub.publish("StartAgitation")
        elif (key == "<Key.right: <65361>>"):
            BeakerPub.publish("StartCWRotate")
        elif (key == "<Key.left: <65363>>"):
            BeakerPub.publish("StartCCWRotate")
        elif (key == "w"):
            WeatherCollectionPub.publish(Empty())
        keyPressed = True

with keyboard.Listener(on_release = on_key_release, on_press = on_key_press) as listener:
    listener.join()

