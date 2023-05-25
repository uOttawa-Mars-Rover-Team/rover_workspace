/*
 * Created by ArduinoGetStarted.com
 *
 * This example code is in the public domain
 *
 * Tutorial page: https://arduinogetstarted.com/tutorials/arduino-limit-switch
 */

#include <ezButton.h>
#include <AccelStepper.h>

ezButton limitSwitchRed(44);  // create ezButton object that attach to pin 7;
ezButton limitSwitchBlack(46);  // create ezButton object that attach to pin 7;

//we create the motor object
AccelStepper stepper(AccelStepper::DRIVER, 7, 6); // Defaults to AccelStepper::DRIVER, step / DIR

//enable pin
int endEffectorEnablePin = 24; //stepper 1

void setup() {
  Serial.begin(9600);
  limitSwitchRed.setDebounceTime(50); // set debounce time to 50 milliseconds
  limitSwitchBlack.setDebounceTime(50);

  //set up stepper
  //stepper.setMaxSpeed(1000);
  //stepper.setSpeed(50);  

  stepper.setMaxSpeed(150.0);
  stepper.setAcceleration(100.0);
  stepper.moveTo(-500);

  //enable pin stuff
  pinMode(endEffectorEnablePin, OUTPUT);
  digitalWrite(endEffectorEnablePin, HIGH);

  //test output
  Serial.println("Hello");
}

void loop() {
  limitSwitchRed.loop(); // MUST call the loop() function first
  limitSwitchBlack.loop();

  //make stepper move
  stepper.run();

  //Serial.println("Hello");
  
  //Serial.println(limitSwitchRed.getState());
  //Serial.println(limitSwitchBlack.getState());
  
  if(limitSwitchRed.isPressed()) {
    Serial.println("Red limit switch pressed");
    Serial.println("Start motor");
    //stepper.runSpeed();
    //stepper.run();

    stepper.stop(); // Stop as fast as possible: sets new target
    stepper.runToPosition(); 
    // Now stopped after quickstop
  }
    

  if(limitSwitchBlack.isPressed()) {
    Serial.println("black limmit switch is pressed");
    Serial.println("Stop Motor");
    stepper.stop(); // Stop as fast as possible: sets new target
    stepper.runToPosition(); 
    // Now stopped after quickstop
  }
    
/*
  int state = limitSwitchRed.getState();
  if(state == HIGH)
    Serial.println("The red limit switch: UNTOUCHED");
  else
    Serial.println("The red limit switch: TOUCHED");
    */
}
