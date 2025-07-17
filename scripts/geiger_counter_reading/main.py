import serial
import datetime

ser = serial.Serial("/dev/ttyTHS1", 115200, timeout=1)

print("Reading data from Geiger counter...")

try:
    while True:
        line = ser.readline().decode("ascii").strip()
        if line:
            print(f"[{datetime.datetime.now().isoformat()}] Geiger data: {line}")
except KeyboardInterrupt:
    print("Stopped by user.")
finally:
    ser.close()
