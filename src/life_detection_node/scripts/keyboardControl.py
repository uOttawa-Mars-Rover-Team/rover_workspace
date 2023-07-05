#!/usr/bin/env python
import rospy
from std_msgs.msg import Empty
from std_msgs.msg import UInt8
from pynput import keyboard
import time

rospy.init_node('LifeDetectionControl')
VacHosePub = rospy.Publisher('VacHoseCMD', UInt8, queue_size=100)
FunnelFlapPub = rospy.Publisher('FunnelFlapCMD', Empty, queue_size=100)
VacMotorPub = rospy.Publisher('VacMotorCMD', Empty, queue_size=100)
BeakerPub = rospy.Publisher('BeakerCMD', UInt8, queue_size= 100)
AgitatePub = rospy.Publisher('AgitateCMD', UInt8, queue_size= 100)
WeatherCollectionPub = rospy.Publisher('WeatherCollectionCMD', Empty, queue_size= 100)

keyPressed = False

def on_key_release(key):
    global keyPressed
    key = repr(key)
    if (key == "<Key.up: <65362>>"):
        VacHosePub.publish(3)
    if (key == "<Key.down: <65364>>"):
        VacHosePub.publish(4)
    if (key == "u'a'"):
    	AgitatePub.publish(0)
    keyPressed = False

def on_key_press(key):
    global keyPressed
    key = repr(key)
    key = key.replace("'", "")
    key = key.replace("u", "")
    if keyPressed == False:
        if (key == "x"):
            exit()
        elif (key == "<Key.down: <65364>>"):
            VacHosePub.publish(1)
        elif (key == "<Key.p: <65362>>"):
            VacHosePub.publish(2)
        elif (key == "f"):
            FunnelFlapPub.publish(Empty())
        elif (key == "v"):
            VacMotorPub.publish(1)
        elif (key == "r"):
            VacMotorPub.publish(2)
        elif (key == "a"):
            AgitatePub.publish(1)
        elif (key == "<Key.right: <65363>>"):
            BeakerPub.publish(1)
        elif (key == "<Key.left: <65361>>"):
            BeakerPub.publish(2)
        elif (key == "w"):
            WeatherCollectionPub.publish(Empty())
        keyPressed = True

with keyboard.Listener(on_release = on_key_release, on_press = on_key_press) as listener:
    listener.join()

