#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from gps_node.msg import gps
from gps_node.msg import imu
import serial
import sys

#The default serial port the Arduino is connected to
DEFAULT_PORT = "/dev/ttyACM0"

"""This script is responsable for parsing the incoming data that the Arduino sends via serial
port with all the values read from the sensors. This script puts that data into messages and 
sends them. The GPS data is put in the gps.msg message and published under the GPS topic. The
IMU data is put in the imu.msg message and published under the IMU topic."""

def talker(serial_port):
	"""(string) -> (None)
	serial_port - the port the Arduino is connected to
	Function that runs the Pulbishsers and parses the info from the serial port.
	"""
	#setup the serial port connection to the Arduino (always close the serial port)
	with serial.Serial(serial_port, 115200, timeout=1) as ser:

		#set up the publishers for the GPS and IMU
		gps_pub = rospy.Publisher("GPS", gps, queue_size=10)
		imu_pub = rospy.Publisher("IMU", imu, queue_size=10)
		rospy.init_node("arduino_gps", anonymous=True)
		rate = rospy.Rate(2)

		#loop until roscore closes
		while not rospy.is_shutdown():
			#read all the data from the serial port until the message is received
			info = ""
			required_data = ["fix", "sats", "lat", "lon", "roll", "pitch", "yaw"]
			missing_data = True

			while missing_data:
				#read from the port(data entries should be separated by newlines)
				info = info + ser.readline().decode("utf-8")

				#check if all the data for this cycle has been received
				missing_data = False
				for data_entry in required_data:
					if data_entry not in info:
						missing_data = True
			
			#make the messages
			gps_data = gps()
			imu_data = imu()

			#find 'fix' in the data and update the GPS message 
			#(constant is length of 'fix' plus 2 for the ':' and space)
			fix_loc = info.find("fix")+5
			gps_data.fix = int(info[fix_loc:fix_loc + 1])

			#find 'sats' in the data and update the GPS message
			sat_loc = info.find("sats")+6
			gps_data.satellites = int(info[sat_loc:info.find(",", sat_loc)])
			
			#if the GPS doesn't have a fix ignore the latitude and longitude in the data
			if (gps_data.fix == 0):
				gps_data.latitude = 0.0
				gps_data.longitude = 0.0
			else:
				#find the latitude and longitude in the data
				lat_end = info.find(",", sat_loc+2)
				lat = info[info.find("lat:")+5:lat_end]
				lon = info[info.find("lon:")+5:info.find(",", lat_end+2)]

				#set the sign of the float based on the direction (N vs S and W vs E)
				if "S" in lat:
					gps_data.latitude = -1 *float(lat[:lat.find("S")])
				else:
					gps_data.latitude = float(lat[:lat.find("N")])
				if "W" in lon:
					gps_data.longitude = -1 * float(lon[:lon.find("W")])
				else:
					gps_data.longitude = float(lon[:lon.find("E")])

			#find 'roll' in the data and update the IMU message
			roll_loc = info.find("roll")+6
			imu_data.roll = float(info[roll_loc:info.find(",", roll_loc)])

			#find 'pitch' in the data and update the IMU message
			pitch_loc = info.find("pitch")+7
			imu_data.pitch = float(info[pitch_loc:info.find(",", pitch_loc)])

			#find 'yaw' in the data and update the IMU message
			yaw_loc = info.find("yaw")+5
			imu_data.yaw = float(info[yaw_loc:info.find(",", yaw_loc)])

			#publish the ros messages		
			rospy.loginfo(gps_data)
			gps_pub.publish(gps_data)
			rospy.loginfo(imu_data)
			imu_pub.publish(imu_data)
			rate.sleep()


if __name__ == "__main__":
	if len(sys.argv) > 2:
		print("Error: Too many arguments. This script takes either one argument (the serial port of the Arduino) "
			"or no arguments to use the default port '/dev/tty/ACM0'")
		sys.exit()
	#if passed with one command line argument the argument is used as the port
	if len(sys.argv) == 2:
		serial_port = sys.argv[1]
	else:
		serial_port = DEFAULT_PORT

	print("Using port: " + serial_port)

	try:
		talker(serial_port)
	except rospy.ROSInterruptException:
		pass
