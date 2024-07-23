import serial

port = serial.Serial("/dev/ttyACM0", "9600")

print(port.readline())