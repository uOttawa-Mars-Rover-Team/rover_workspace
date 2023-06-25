
//we import the libraries
#include <AccelStepper.h>
#include <MultiStepper.h>


// we declare the two steppers
// Alas its not possible to build an array of these with different pins for each :-(
AccelStepper stepper1(AccelStepper::DRIVER, 4, 5);
AccelStepper stepper2(AccelStepper::DRIVER, 6, 7);
// Up to 10 steppers can be handled as a group by MultiStepper
MultiStepper steppers;

void setup() {
  Serial.begin(9600);
  // Configure each stepper
  stepper1.setMaxSpeed(100);
  stepper2.setMaxSpeed(100);
  stepper1.setAcceleration(20);
  stepper2.setAcceleration(20);

  stepper1.moveTo(500);
  stepper2.moveTo(500);
  

}

void loop() {
  // put your main code here, to run repeatedly:

  // put your main code here, to run repeatedly:
  // If at the end of travel go to the other end
    if (stepper1.distanceToGo() == 0)
      stepper1.moveTo(-stepper1.currentPosition());
    stepper1.run();

    //same code but for 2nd motor
    if (stepper2.distanceToGo() == 0)
      stepper2.moveTo(-stepper2.currentPosition());
    stepper2.run();
  

}
