#!/usr/bin/env python
import keyboard
from time import sleep
import pigpio

#Make sure to run 'sudo pigpiod' to start the pigpio daemon before running this code

#Constants
ServoControlPin = 18

MaxDegree = 180
MinDegree = 0

DegreeChangeRate = 1

MinPulse = 500
MaxPulse = 2500
PulseRange = MaxPulse - MinPulse


def getDutyCycle(position):
    return ((float(position)/float(MaxDegree)) * PulseRange) + MinPulse


if __name__ == "__main__":
    print("setting up pin...")

    pi = pigpio.pi()

    currentPosition = MaxDegree/2

    print("starting servo control...")
    isStopped = False
    while not isStopped:
        key = raw_input()

        if 'q' in key:
            print("stop")
            isStopped = True

        elif 'd' in key:
            print("left")
            currentPosition = min(currentPosition + DegreeChangeRate, MaxDegree)

        elif 'a' in key:
            print("right")
            currentPosition = max(currentPosition - DegreeChangeRate, MinDegree)

        pi.set_servo_pulsewidth(ServoControlPin, getDutyCycle(currentPosition))
        sleep(0.01)
