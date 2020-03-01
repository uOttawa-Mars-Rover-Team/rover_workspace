#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from gps_node.msg import gps
import serial

def talker():
	ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)
	pub = rospy.Publisher("GPS", gps, queue_size=10)
	rospy.init_node("arduino_gps", anonymous=True)
	rate = rospy.Rate(2)
	while not rospy.is_shutdown():
		#read the serial port
		info = ""
		while ("fix" not in info or "sats" not in info or "lat" not in info or "lon" not in info):
			info = info + ser.readline().decode("utf-8")
		
		#make the message
		data = gps()

		fix_loc = info.find("fix")+5
		#print(info,fix_loc, info[fix_loc:fix_loc + 1])

		data.fix = int(info[fix_loc:fix_loc + 1])

		sat_loc = info.find("sats")+6
		data.satellites = int(info[sat_loc:info.find(",", sat_loc)])
		
		if (data.fix == 0):
			data.latitude = 0.0
			data.longitude = 0.0
		else:
			lat_end = info.find(",", sat_loc+2)
			lat = info[info.find("lat:")+5:lat_end]
			lon = info[info.find("lon:")+5:info.find(",", lat_end+2)]
			if "S" in lat:
				data.latitude = -1 *float(lat[:lat.find("S")])
			else:
				data.latitude = float(lat[:lat.find("N")])
			if "W" in lon:
				data.longitude = -1 * float(lon[:lon.find("W")])
			else:
				data.longitude = float(lon[:lon.find("E")])

		#ros message stuff		
		rospy.loginfo(data)
		pub.publish(data)
		rate.sleep()
	ser.close()
	#pub = rospy.Publisher("chatter", String, queue_size=10)
	#rospy.init_node("talker", anonymous=True)
	#rate = rospy.Rate(10)
	#while not rospy.is_shutdown():
	#	hello_str = "Hello world %s" % rospy.get_time()
	#	rospy.loginfo(hello_str)
	#	pub.publish(hello_str)
	#	rate.sleep()

if __name__ == "__main__":
	try:
		talker()
	except rospy.ROSInterruptException:
		pass
