#include <Arduino.h>
#include <Servo.h>

//This sketch is loaded onto the Arduino that handles the drive system.

// Pins to Left Wheels
#define pinL1 3
// Pins to Right Wheels
#define pinR1 6

#define sparkMax 1000 // Default full-reverse input pulse
#define sparkMin 2000 // Default full-forward input pulse

Servo leftWheels;
Servo rightWheels;

struct DATA {
    float linear;
    float rotation;
} received;

void setWheelVelocity(int left, int right) {
    leftWheels.writeMicroseconds(map(left, -100, 100, sparkMin, sparkMax));
    rightWheels.writeMicroseconds(map(right, -100, 100, sparkMin, sparkMax));
}

void setup() {
    Serial.begin(9600);
    leftWheels.attach(pinL1);
    rightWheels.attach(pinR1);
}

void loop() {
   if (Serial.available() >= sizeof(uint8_t)) {
       delayMicroseconds(10);
       uint8_t cmd = (uint8_t) Serial.read();


       if (cmd == 0) {
           Serial.readBytes((char *) &received.linear, sizeof(float));
           Serial.readBytes((char *) &received.rotation, sizeof(float));

           setWheelVelocity((int) ((received.linear - received.rotation) * 100), (int) ((received.linear + received.rotation) * -100));
       }
   }
}