
//we import the libraries
#include <AccelStepper.h>
#include <MultiStepper.h>
#include <ezButton.h>


// we declare the two steppers
// Alas its not possible to build an array of these with different pins for each :-(
AccelStepper stepper1(AccelStepper::DRIVER, 4, 5);
AccelStepper stepper2(AccelStepper::DRIVER, 6, 7);
// Up to 10 steppers can be handled as a group by MultiStepper
MultiStepper steppers;

//initialize limit switches
ezButton limitSwitchRed(42);  // create ezButton object that attach to pin 7;
ezButton limitSwitchBlack(43);  // create ezButton object that attach to pin 7;

long positions[2]; // Array of desired stepper positions
long maxRange = 1000;

void setup() {
  Serial.begin(9600);

  limitSwitchRed.setDebounceTime(50); // set debounce time to 50 milliseconds
  limitSwitchBlack.setDebounceTime(50);

  
  // Configure each stepper
  stepper1.setMaxSpeed(1000.0);
  stepper2.setMaxSpeed(1000.0);

  // Then give them to MultiStepper to manage
  steppers.addStepper(stepper1);
  steppers.addStepper(stepper2);

  positions[0] = 1000;
  positions[1] = -1000;

  steppers.moveTo(positions);

}

void loop() {

  Serial.println("Currennt position");
  Serial.println(stepper1.currentPosition());
  Serial.print("Distance to go: ");
  Serial.println(stepper1.distanceToGo());
  
  limitSwitchRed.loop(); // MUST call the loop() function first
  limitSwitchBlack.loop();
  
  //we create the positions array
  //long positions[2]; // Array of desired stepper positions
  
  //positions[0] = 1000;
  //positions[1] = -1000;

  if (stepper1.distanceToGo() == 0) {
    long tmpPosition = stepper1.currentPosition();
    positions[0] = tmpPosition * -1;
    positions[1] *= tmpPosition;
    steppers.moveTo(positions);
    
    
  }
    steppers.run();

  
  
  

//we check to see if the limit switched got pressed
  if(limitSwitchRed.isPressed()) {
    
    Serial.println("Red limit switch pressed");
    Serial.println("Start motor");


    //potential better way of doing this
    delay(2000);

    //we set up the new positions as the opposite of our theoredical max so let's say we have a range of 
    // 2000 steps in each direction, we now set our target destination as the other side of the range

    positions[0] = maxRange;
    positions[1] = -maxRange;

    steppers.moveTo(positions);
    
  }

    

  if(limitSwitchBlack.isPressed()) {
    Serial.println("black limmit switch is pressed");
    Serial.println("Stop Motor");


    //potential better way of doing this
    delay(2000);

    //we set up the new positions as the opposite of our theoredical max so let's say we have a range of 
    // 2000 steps in each direction, we now set our target destination as the other side of the range

    positions[0] = -maxRange;
    positions[1] = maxRange;

    steppers.moveTo(positions);
  }


  /*
  // put your main code here, to run repeatedly:
  steppers.moveTo(positions);
  steppers.runSpeedToPosition(); // Blocks until all are in position
  */

  /*
  Serial.println("Currennt position");
  Serial.println(stepper1.currentPosition());
  Serial.print("Distance to go: ");
  Serial.println(stepper1.distanceToGo());
  */

  /*
  delay(1000);
  
  // Move to a different coordinate
  positions[0] = -1000;
  positions[1] = 1000;
  steppers.moveTo(positions);
  steppers.runSpeedToPosition(); // Blocks until all are in position
  delay(1000);
  */
  

}
