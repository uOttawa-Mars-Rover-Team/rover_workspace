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

int stepper1EnablePin = 24; //Enable pin for the step resolutions, enabeling this one gives full step resolution

//we initialise one stepper motor
// Define a stepper and the pins it will use
AccelStepper stepper(AccelStepper::DRIVER, 7, 6); // 1 = Easy Driver interface
// NANO Pin 7 connected to STEP pin of Easy Driver
// NANO Pin 6 connected to DIR 

                                                   
// AccelStepper stepper2(AccelStepper::DRIVER, 9, 8);
// AccelStepper stepper3(AccelStepper::DRIVER, 11, 10);
// AccelStepper stepper4(AccelStepper::DRIVER, 13, 12);



void setup() {
  // put your setup code here, to run once:
  // Change these to suit your stepper if you want
  stepper.setMaxSpeed(1000);
  stepper.setAcceleration(1000);
  //stepper.moveTo(-500);
  
  // stepper2.setMaxSpeed(1000);
  // stepper2.setAcceleration(1000);
  // stepper2.moveTo(500);
  
  // stepper3.setMaxSpeed(1000);
  // stepper3.setAcceleration(1000);
  // stepper3.moveTo(500);

  // stepper4.setMaxSpeed(1000);
  // stepper4.setAcceleration(1000);
  // stepper4.moveTo(-500);

  //we set the digital
  pinMode(stepper1EnablePin, OUTPUT);
  digitalWrite(stepper1EnablePin, HIGH);

}

void loop() {
  // put your main code here, to run repeatedly:
  // If at the end of travel go to the other end
    //if (stepper.distanceToGo() == 0)
      //stepper.moveTo(-stepper.currentPosition());
    
    stepper.run();
    // stepper2.run();
    // stepper3.run();
    // stepper4.run();


    //we move the motor in both directions
    Serial.println("Moving stepper clockwise");
  stepper.setMaxSpeed(50);
  stepper.moveTo(100);
  stepper.runToPosition();

  // we move anticlockwise to the max range for the tower
  Serial.println("Moving tower counterclockwise");
  stepper.moveTo(-100);
  stepper.runToPosition();

}
