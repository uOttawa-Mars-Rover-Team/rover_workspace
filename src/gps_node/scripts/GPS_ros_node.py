#!/usr/bin/env python
import rospy
from std_msgs.msg import String
from gps_node.msg import gps
from gps_node.msg import imu
from sensor_msgs.msg import Imu, NavSatFix, NavSatStatus
from geometry_msgs.msg import Twist
from tf.transformations import quaternion_from_euler
import serial
import sys

START_CHAR = "#"
GPS_CHAR = "G"
IMU_CHAR = "I"

#The default serial port the Arduino is connected to
DEFAULT_PORT = "/dev/ttyACM0"
DATA_TAG_EXTRA_LENGTH = 1

#The name of the rosparam (in the launch file) to check for the port name
ROSPARAM_PORT = "/GPS_ros_node/arduino_port"

#Max and Min values for Latitude and Longitude degrees
MAX_LAT_DEG = 90
MIN_LAT_DEG = -90
MAX_LON_DEG = 180
MIN_LON_DEG = -180

"""This script is responsable for parsing the incoming data that the Arduino sends via serial
port with all the values read from the sensors. This script puts that data into messages and 
sends them. The GPS data is put in the gps.msg message and published under the GPS topic. The
IMU data is put in the imu.msg message and published under the IMU topic."""

def get_data(raw_str, data_tag):
	"""(string, string) -> (string)
	raw_str - the raw data received from the Arduino
	dat_tag - the tag to look for to get the required data
	Returns the associated with the given data_tag from the raw_data. Returns
	None if the data is not present.
	"""
	start = raw_str.find(data_tag)
	if (start == -1):
		return None
	else:
		end = raw_str.find(" ", start)
		if (end == -1):
			return None
		else:
			return raw_str[start + len(data_tag) + DATA_TAG_EXTRA_LENGTH : end].strip().strip(",")

def get_int(raw_str):
	"""(string) -> (int/None)
	raw_str - string of an integer to be parsed
	Returns the int if it can be parsed or None if an error occurs.
	"""
	try:
		return int(raw_str)
	except:
		return None

def get_latitude(raw_str):
	"""(string) -> (float/None)
	raw_str - the string with latitude from the GPS in the form DDMM.MMMM
	Converts the latitude from the GPS to decimal degrees. Value is negative
	if latitude is south and positive to the norht. Returns None if an error
	occurs during parsing.
	"""
	if (raw_str == None):
		return None 

	if ("None" in raw_str):
		return 0.0

	raw_float = None
	isNeg = False
	if ("N" in raw_str):
		lat = raw_str[0:raw_str.find("N")]
		try:
			raw_float = float(lat)
		except:
			return None

	elif ("S" in raw_str):
		lat = raw_str[0:raw_str.find("S")]
		try:
			raw_float = float(lat)
			isNeg = True
		except:
			return None

	#Need to convert to degrees from DDMM.MMMM(format from GPS)
	if raw_float != None:
		dec_deg = convert_to_decimal_degrees(raw_float, MAX_LAT_DEG, MIN_LAT_DEG, isNeg)
		if dec_deg == None:
			print("Error: Latitude outside accepted values. (", raw_float, ")")
		return dec_deg

	else:
		return None

def get_longitude(raw_str):
	"""(string) -> (float/None)
	raw_str - the string with longitude from the GPS in the form DDMM.MMMM
	Converts the longitude from the GPS to decimal degrees. Value is negative
	if longitude is west and positive to the east. Returns None if an error
	occurs during parsing.
	"""
	if (raw_str == None):
		return None 
		
	if ("None" in raw_str):
		return 0.0

	raw_float = None
	isNeg = False	
	if ("E" in raw_str):
		lon = raw_str[0:raw_str.find("E")]
		try:
			raw_float = float(lon)
		except:
			return None

	elif ("W" in raw_str):
		lon = raw_str[0:raw_str.find("W")]
		try:
			raw_float = float(lon)
			isNeg = True
		except:
			return None

	#Need to convert to degrees from DDMM.MMMM(format from GPS)
	if raw_float != None:
		dec_deg = convert_to_decimal_degrees(raw_float, MAX_LON_DEG, MIN_LON_DEG, isNeg)
		if dec_deg == None:
			print("Error: Longitude outside accepted values. (", raw_float, ")")
		return dec_deg
	else:
		return None

def convert_to_decimal_degrees(raw_dec, max_deg, min_deg, isNeg):
	"""(float, int, int, bool) -> (float)
	raw_dec - the raw GPS info in DDMM.MMMM
	max_deg - the maximum value of the degrees portion
	min_deg - the minimum value of the degrees portion
	isNeg - true if the final value should be negative
	Converts the raw value from the DDMM.MMMM format to decimal degrees (what is
	used in ROS messages). Max_deg and min_deg will change based on whether the 
	conversion is happening on latitude or longitude. isNeg will be dependent on 
	whether the value is N vs S or W vs E.
	"""
	degrees = int(raw_dec // 100)
	if (degrees < min_deg or degrees > max_deg):
		return None

	minutes = raw_dec % 100
	if (minutes < 0 or minutes > 60):
		return None

	decimal_degrees = degrees + (minutes/60)

	if isNeg:
		return -1 * decimal_degrees
	else:
		return decimal_degrees

def get_float(raw_str):
	"""(string) -> (float/None)
	raw_str - a string to be parsed as a float
	Returns the corresponding float or None if an error occured while parsing.
	"""
	try:
		return float(raw_str)
	except:
		return None

def get_float_list(raw_str):
	"""(string) -> (list of floats)
	raw_str - a string of floats separated by commas
	Returns a list of floats parsed from the string. May contain None in place of 
	a float if it could not be parsed.
	"""
	str_list = raw_str.split(",")
	float_list = []

	for item in str_list:
		float_list.append(get_float(item))

	return float_list

def parse_gps(msg, seq_num, gps_pub, kal_gps_pub):
	#make the messages
	gps_data = gps()
	kal_gps_data = NavSatFix()

	#set timestamp, (seq# is set by publisher)
	kal_gps_data.header.stamp = rospy.Time.now()
	kal_gps_data.header.frame_id = "gps_tf"

	kal_gps_data.header.seq = seq_num

	# GPS DATA
	fix = get_int(get_data(msg, "fix"))
	sats = get_int(get_data(msg, "sats"))
	lat = get_latitude(get_data(msg, "lat"))
	lon = get_longitude(get_data(msg, "lon"))

	if ((fix != None) and (sats != None) and (lat != None) and (lon != None)):
		gps_data.fix = fix
		gps_data.satellites = sats
		gps_data.latitude = lat
		gps_data.longitude = lon

		if (gps_data.fix == 1):
			kal_gps_data.status.status = NavSatStatus.STATUS_FIX
		else:
			kal_gps_data.status.status = NavSatStatus.STATUS_NO_FIX

		kal_gps_data.status.service = NavSatStatus.SERVICE_GPS

		kal_gps_data.latitude = gps_data.latitude
		kal_gps_data.longitude = gps_data.longitude
		kal_gps_data.altitude = float("NaN")
		kal_gps_data.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN

		#publish the ros messages		
		#rospy.loginfo(gps_data)
		gps_pub.publish(gps_data)
		#rospy.loginfo(kal_gps_data)
		kal_gps_pub.publish(kal_gps_data)
		return True
	return False

def parse_imu(msg, seq_num, imu_pub, kal_imu_pub):
	#make the messages
	imu_data = imu()
	kal_imu_data = Imu()

	#set timestamp, (seq# is set by publisher)
	kal_imu_data.header.stamp = rospy.Time.now()
	kal_imu_data.header.frame_id = "imu_tf"
	kal_imu_data.header.seq = seq_num

	# IMU DATA
	roll = get_float(get_data(msg, "roll"))
	pitch = get_float(get_data(msg, "pitch"))
	yaw = get_float(get_data(msg, "yaw"))

	if ((roll != None) and (pitch != None) and (yaw != None)):
		imu_data.roll = roll
		imu_data.pitch = pitch
		imu_data.yaw = yaw

		#publish the ros messages
		#rospy.loginfo(imu_data)
		imu_pub.publish(imu_data)

		# EXTRA IMU DATA FOR KALMAN
		#find angular velocity(deg/s)
		ang_vel = get_float_list(get_data(msg, "ang_vel"))
		lin_accel = get_float_list(get_data(msg, "lin_accel"))

		if ((len(ang_vel) == 3) and (None not in ang_vel) and (len(lin_accel) == 3) and (None not in lin_accel)):
			#convert to rad/s (originally in deg/s)
			kal_imu_data.angular_velocity.x = ang_vel[0] * ((2*3.14)/180.0)
			kal_imu_data.angular_velocity.y = ang_vel[1] * ((2*3.14)/180.0)
			kal_imu_data.angular_velocity.z = ang_vel[2] * ((2*3.14)/180.0)

			#convert to m/s^2 (1g = 9.81m/s^2) (originally in g's)
			kal_imu_data.linear_acceleration.x = lin_accel[0]/9.81
			kal_imu_data.linear_acceleration.y = lin_accel[1]/9.81
			kal_imu_data.linear_acceleration.z = lin_accel[2]/9.81

			#orientation
			quat = quaternion_from_euler(roll, pitch, yaw)
			
			kal_imu_data.orientation.x = quat[0]
			kal_imu_data.orientation.y = quat[1]
			kal_imu_data.orientation.z = quat[2]
			kal_imu_data.orientation.w = quat[3]

			#publish the ros messages
			#rospy.loginfo(kal_imu_data)
			kal_imu_pub.publish(kal_imu_data)
			return True
		else:
			print("missing lin accel")
	else:
		print("missing rpy")
	return False


def talker(serial_port):
	"""(string) -> (None)
	serial_port - the port the Arduino is connected to
	Function that runs the Pulbishsers and parses the info from the serial port.
	"""
	#setup the serial port connection to the Arduino (always close the serial port)
	with serial.Serial(serial_port, 115200, timeout=1) as ser:

		#get rid of old stuff to use newest data
		ser.reset_input_buffer()

		#set up the publishers for the GPS and IMU
		gps_pub = rospy.Publisher("GPS", gps, queue_size=10)
		imu_pub = rospy.Publisher("IMU", imu, queue_size=10)
		kal_imu_pub = rospy.Publisher("/imu/sensor/data", Imu, queue_size=10)
		kal_gps_pub = rospy.Publisher("/gps/sensor/data", NavSatFix, queue_size=10)

		rate = rospy.Rate(2)

		imu_seq_num = 0
		gps_seq_num = 0

		#loop until roscore closes
		while not rospy.is_shutdown():
			#read all the data from the serial port until the message is received
			msg = ""
			try:
				msg = str(ser.readline().decode("utf-8"))
			except:
				print("unable to read message")

			if((len(msg) > 2) and (msg[0] == START_CHAR)):
				if((msg[1] == GPS_CHAR) and parse_gps(msg, gps_seq_num, gps_pub, kal_gps_pub)):
					gps_seq_num += 1
				elif((msg[1] == IMU_CHAR) and parse_imu(msg, imu_seq_num, imu_pub, kal_imu_pub)):
					imu_seq_num += 1
				else:
					print("Invalid message type", msg[1])
			else:
				print("Message too short or invalid start char", msg)


			# required_data = ["fix", "sats", "lat", "lon", "roll", "pitch", "yaw", "ang_vel", "lin_accel"]
			# missing_data = True

			# while ("fix" not in info):
			# 	#read from the port(data entries should be separated by newlines)
			# 	info = info + ser.readline().decode("utf-8")

			# #crop off anything before start of message
			# info = info[info.find("fix"):len(info)]

			# while missing_data:
			# 	#read from the port(data entries should be separated by newlines)
			# 	info = info + ser.readline().decode("utf-8")

			# 	#check if all the data for this cycle has been received
			# 	missing_data = False
			# 	for data_entry in required_data:
			# 		if data_entry not in info:
			# 			missing_data = True

			#cut off any excess
			# if (info.count("fix") > 1):
			# 	first = info.find("fix")
			# 	info = info[0:info.find("fix", first)]

			# print(info)
			
			# #make the messages
			# gps_data = gps()
			# imu_data = imu()
			# kal_imu_data = Imu()
			# kal_gps_data = NavSatFix()

			# #set timestamp, (seq# is set by publisher)
			# kal_imu_data.header.stamp = rospy.Time.now()
			# kal_imu_data.header.frame_id = "imu_tf"

			# kal_gps_data.header.stamp = rospy.Time.now()
			# kal_gps_data.header.frame_id = "gps_tf"

			# kal_imu_data.header.seq = seq_num
			# kal_gps_data.header.seq = seq_num
			# seq_num += 1

			# # GPS DATA
			# fix = get_int(get_data(info, "fix"))
			# sats = get_int(get_data(info, "sats"))
			# lat = get_latitude(get_data(info, "lat"))
			# lon = get_longitude(get_data(info, "lon"))

			# if ((fix != None) and (sats != None) and (lat != None) and (lon != None)):
			# 	gps_data.fix = fix
			# 	gps_data.satellites = sats
			# 	gps_data.latitude = lat
			# 	gps_data.longitude = lon

			# 	if (gps_data.fix == 1):
			# 		kal_gps_data.status.status = NavSatStatus.STATUS_FIX
			# 	else:
			# 		kal_gps_data.status.status = NavSatStatus.STATUS_NO_FIX

			# 	kal_gps_data.status.service = NavSatStatus.SERVICE_GPS

			# 	kal_gps_data.latitude = gps_data.latitude
			# 	kal_gps_data.longitude = gps_data.longitude
			# 	kal_gps_data.altitude = float("NaN")
			# 	kal_gps_data.position_covariance_type = NavSatFix.COVARIANCE_TYPE_UNKNOWN

			# 	#publish the ros messages		
			# 	#rospy.loginfo(gps_data)
			# 	gps_pub.publish(gps_data)
			# 	#rospy.loginfo(kal_gps_data)
			# 	kal_gps_pub.publish(kal_gps_data)

			# # IMU DATA
			# roll = get_float(get_data(info, "roll"))
			# pitch = get_float(get_data(info, "pitch"))
			# yaw = get_float(get_data(info, "yaw"))

			# if ((roll != None) and (pitch != None) and (yaw != None)):
			# 	imu_data.roll = roll
			# 	imu_data.pitch = pitch
			# 	imu_data.yaw = yaw

			# 	#publish the ros messages
			# 	#rospy.loginfo(imu_data)
			# 	imu_pub.publish(imu_data)

			# 	# EXTRA IMU DATA FOR KALMAN
			# 	#find angular velocity(deg/s)
			# 	ang_vel = get_float_list(get_data(info, "ang_vel"))
			# 	lin_accel = get_float_list(get_data(info, "lin_accel"))

			# 	if ((len(ang_vel) == 3) and (None not in ang_vel) and (len(lin_accel) == 3) and (None not in lin_accel)):
			# 		#convert to rad/s (originally in deg/s)
			# 		kal_imu_data.angular_velocity.x = ang_vel[0] * ((2*3.14)/180.0)
			# 		kal_imu_data.angular_velocity.y = ang_vel[1] * ((2*3.14)/180.0)
			# 		kal_imu_data.angular_velocity.z = ang_vel[2] * ((2*3.14)/180.0)

			# 		#convert to m/s^2 (1g = 9.81m/s^2) (originally in g's)
			# 		kal_imu_data.linear_acceleration.x = lin_accel[0]/9.81
			# 		kal_imu_data.linear_acceleration.y = lin_accel[1]/9.81
			# 		kal_imu_data.linear_acceleration.z = lin_accel[2]/9.81

			# 		#orientation
			# 		quat = quaternion_from_euler(roll, pitch, yaw)
					
			# 		kal_imu_data.orientation.x = quat[0]
			# 		kal_imu_data.orientation.y = quat[1]
			# 		kal_imu_data.orientation.z = quat[2]
			# 		kal_imu_data.orientation.w = quat[3]

			# 		#publish the ros messages
			# 		#rospy.loginfo(kal_imu_data)
			# 		kal_imu_pub.publish(kal_imu_data)

			rate.sleep()


if __name__ == "__main__":
	#need to init node before checking the rosparams
	rospy.init_node("arduino_gps", anonymous=True)

	# clean out any ROS added params
	args = rospy.myargv(argv=sys.argv)

	serial_port = DEFAULT_PORT

	#if passed with one command line argument the argument is used as the port
	if len(args) == 2:
		serial_port = args[1]

	#check for rosparams passed through a launch file
	if rospy.has_param(ROSPARAM_PORT):
		serial_port = rospy.get_param(ROSPARAM_PORT)


	print("Using port: " + serial_port)

	try:
		talker(serial_port)
	except rospy.ROSInterruptException:
		pass
