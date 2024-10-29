/*
 * program to move one singular stepper motor, hopefully serving as a proof of concept / proof of life
 * that we can make the steppers work
 * This example was found in teh accelStepper doccumentation online
 * link: http://www.airspayce.com/mikem/arduino/AccelStepper/Bounce_8pde-example.html
 * 
 * essentially it make the stepper bounce, that is we set a position and then step until we get there
 * when the position is reached, the stepper "bounces" and starts going in the opposite direction 
 * until the desired posision is acheived (the same position as before but in the opposite direction)
 * The stepper accelerates from 0 and accelerates to the targeted speed until it gets close to the desired position where it decelerates
 * until it arrives at the desired positon and stops
 */

//we import the AccelStepper library for stepper control
#include <AccelStepper.h>

int towerEnablePin = 17; //Enable pin for the step resolutions, enabeling this one gives full step resolution
int wristPitchEnablePin = 16;
int wristRollEnablePin = 4;
int endEffectorEnablePin = 5;

int towerMaxRange = 1000000;
int wristPitchMaxRange = 1000000;
int wristRollMaxRange = 1000000;
int endEffectorMaxRange = 1000000;

int towerMaxSpeed = 1000;
int wristPitchMaxSpeed = 1000;
int wristRollMaxSpeed = 1000;
int endEffectorMaxSpeed = 1000;

int towerSpeed = 1;
int wristPitchSpeed = 1;
int wristRollSpeed = 1;
int endEffectorSpeed = 1;

//we initialise one stepper motor
// Define a stepper and the pins it will use
AccelStepper tower        (AccelStepper::DRIVER, 6,   7);  //step, direction
AccelStepper wristPitch   (AccelStepper::DRIVER, 8,   9);
AccelStepper wristRoll    (AccelStepper::DRIVER, 10,  11); 
AccelStepper endEffector  (AccelStepper::DRIVER, 12,  13);
// NANO Pin 7 connected to STEP pin of Easy Driver
// NANO Pin 6 connected to DIR 

                                                   
// AccelStepper stepper2(AccelStepper::DRIVER, 9, 8);
// AccelStepper stepper3(AccelStepper::DRIVER, 11, 10);
// AccelStepper stepper4(AccelStepper::DRIVER, 13, 12);



void setup() {
  // Tower
  tower.setMaxSpeed(towerMaxSpeed * towerSpeed);
  tower.setAcceleration(1000);
  pinMode(towerEnablePin, OUTPUT);
  digitalWrite(towerEnablePin, HIGH);

  // Wrist Pitch
  wristPitch.setMaxSpeed(wristPitchMaxSpeed * wristPitchSpeed);
  wristPitch.setAcceleration(1000);
  pinMode(wristPitchEnablePin, OUTPUT);
  digitalWrite(wristPitchEnablePin, HIGH);

  // Wrist Roll
  wristRoll.setMaxSpeed(wristRollMaxSpeed * wristRollSpeed);
  wristRoll.setAcceleration(1000);
  pinMode(wristRollEnablePin, OUTPUT);
  digitalWrite(wristRollEnablePin, HIGH);

  // End Effector
  endEffector.setMaxSpeed(endEffectorMaxSpeed * endEffectorSpeed);
  endEffector.setAcceleration(1000);
  pinMode(endEffectorEnablePin, OUTPUT);
  digitalWrite(endEffectorEnablePin, HIGH);

  // Tower
  int towerDir = 1;
  tower.moveTo(towerMaxRange * towerDir);

  // Wrist Pitch
  int wristPitchDir = 1;
  wristPitch.moveTo(wristPitchMaxRange * wristPitchDir);

  // Wrist Roll
  int wristRollDir = 1;
  wristRoll.moveTo(wristRollMaxRange * wristRollDir);

  // End Effector
  int endEffectorDir = 1;
  endEffector.moveTo(endEffectorMaxRange * endEffectorDir);
}

void loop() {
  tower.run();
  wristPitch.run();
  wristRoll.run();
  endEffector.run();
}
