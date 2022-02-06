
/*
Life Detection Module

 */

#include <Servo.h>

// Define pin connections & motor's steps per revolution
const int beakerDirPin = 6;
const int beakerStepPin = 7;

const int hoseDirPin = 2;
const int hoseStepPin = 3;
const int stepsPerRevolution = 200;

const int upperPin = 12; 
const int lowerPin = 13;

const int vacuumPin = 10;

Servo servo;
int pos = 0;
boolean flapIsOpen = false;


int upperLimit = LOW;
int lowerLimit = LOW;
int vibration = LOW;
int vacuumState = LOW;

int stepCount = 0;  // number of steps the motor has taken

String command;
int dir = 0;

void setup() {

  // VACUUM HOSE EXTENDER
  pinMode(upperPin, INPUT);
  pinMode(lowerPin, INPUT);

  pinMode(hoseStepPin, OUTPUT);
  pinMode(hoseDirPin, OUTPUT);

  // VACUUM MOTOR CONTROLLER
  pinMode(vacuumPin, OUTPUT);
  digitalWrite(vacuumPin, LOW);

  // BEAKER CAROUSEL CONTROLLER
  pinMode(beakerStepPin, OUTPUT);
  pinMode(beakerDirPin, OUTPUT);

  servo.attach(9);

  Serial.begin(9600);
  delay(2000);  
 
  Serial.println("Available commands: hose-up, hose-down, hose-stop, vacuum, beaker[INSERT BEAKER INDEX], home, +, -");
  
}

void loop() {
  check_limits();
  handleSerial();
  move_hose();
  
}


void handleSerial() {
 if(Serial.available()){
        command = Serial.readStringUntil('\n');
         
        if(command.equals("hose-up")){
          //check_limits();
          if(upperLimit == LOW){
            Serial.println("Upper bound reached... Command ignored");
            dir = 0;
          }else{
            dir = 1;
          }
        }
        else if(command.equals("hose-down")){
          check_limits();
          if(lowerLimit == LOW){
            Serial.println("Lower bound reached... Command ignored");
            dir = 0;
          }else{
            dir = -1;
          }
        }
        else if(command.equals("hose-stop")){
            dir = 0;
        }
        //+++++++++++++++++++++++++++++++++++++++
        // BEAKER CAROUSEL CONTROLLER
        else if(command.equals("vacuum")){
            toggleVacuum();
        }
        //+++++++++++++++++++++++++++++++++++++++
        // BEAKER CAROUSEL CONTROLLER
        else if(command.equals("vibrate")){
          vibration = HIGH;
          Serial.println("Starting vibration motors...");
        }
        else if(command.equals("vibrate-stop")){
          vibration = LOW;
          Serial.println("Stopping vibration motors...");
        }
        else if(command.equals("+")){
          step_forward();
        }
        else if(command.equals("-")){
          step_back();
        }
        else if(command.equals("beaker1")){
          beakerController(1);
        }
        else if(command.equals("beaker2")){
          beakerController(2);
        }
        else if(command.equals("beaker3")){
          beakerController(3);
        }
        else if(command.equals("beaker4")){
          beakerController(4);
        }
        else if(command.equals("beaker5")){
          beakerController(5);
        }
        else if(command.equals("beaker6")){
          beakerController(6);
        }
        else if(command.equals("beaker7")){
          beakerController(7);
        }
        else if(command.equals("beaker8")){
          beakerController(8);
        }
        else if(command.equals("beaker9")){
          beakerController(9);
        }
        else if(command.equals("beaker10")){
          beakerController(10);
        }
        else if(command.equals("home")){
          returnHome();
        }
        //+++++++++++++++++++++++++++++++++++++++
        // FUNNEL FLAP CONTROLLER
        else if(command.equals("funnel-open")){
          openFlap();
        }
        else if(command.equals("funnel-close")){
          closeFlap();
        }
        //+++++++++++++++++++++++++++++++++++++++
        else{
            Serial.println("Invalid command......");
            Serial.println("Available commands: up, down, stop");
        }
    }
}


//=================================================================================================
// VACUUM HOSE EXTENDER 
void move_hose(){
  int stopFlag = LOW;
    if (dir != 0){
       // Set motor direction clockwise
      if (dir == 1){
        digitalWrite(hoseDirPin, HIGH);
      }else if (dir == -1){
        digitalWrite(hoseDirPin, LOW);
      }
      // Spin motor slowly
      for(int x = 0; x < stepsPerRevolution; x++)
      {
        if (!check_limits()){
        digitalWrite(hoseStepPin, HIGH);
        delayMicroseconds(2000);
        digitalWrite(hoseStepPin, LOW);
        delayMicroseconds(2000);
      }else{
        Serial.println("BREAK");
        stopFlag = HIGH;
        break; 
      }
    }
    if(stopFlag == HIGH){
      backOff();
    }
  } 
}

bool check_limits(){
  upperLimit = digitalRead(upperPin);
  lowerLimit = digitalRead(lowerPin);

  if(upperLimit  == LOW){
    //Serial.println("UPPER HIGH");
  }

  if(lowerLimit  == LOW){
    //Serial.println("LOWER HIGH");
  }

  if(!upperLimit || !lowerLimit){
    return true;
  }else{
    return false;
  }
}

void backOff(){
  Serial.println("BACKOFF");
  if (dir == 1 && !upperLimit){
     digitalWrite(hoseDirPin, LOW);
  }else if (dir == -1 && !lowerLimit){
     digitalWrite(hoseDirPin, HIGH);
  }else{
    Serial.println("ERROR: check limit switches");
    dir = 0;
    return;
  }
  delay(1000);
  for(int x = 0; x < stepsPerRevolution; x++)
      {
        digitalWrite(hoseStepPin, HIGH);
        delayMicroseconds(2000);
        digitalWrite(hoseStepPin, LOW);
        delayMicroseconds(2000);
      }
  dir = 0;
  
}

  
  


//=================================================================================================
// VACUUM MOTOR CONTROLLER

void toggleVacuum(){
  if (vacuumState == LOW){
    digitalWrite(vacuumPin, LOW);
    vacuumState = HIGH;
  }else{
    digitalWrite(vacuumPin, HIGH);
    vacuumState = LOW;
  }
}


//=================================================================================================
// BEAKER CAROUSEL CONTROLLER

float const degrees_between_beaker = 25.00/360;
float const gear_ratio = 309/14;

int currentBeakerIndex = 0;
int beakerHome = 1;

void shake(){
  
      digitalWrite(beakerDirPin, HIGH);
      // Spin motor slowly
     
      
        digitalWrite(beakerStepPin, HIGH);
        delayMicroseconds(2000);
        digitalWrite(beakerStepPin, LOW);
        delayMicroseconds(2000);
      
      delay(1000); // Wait a second
      digitalWrite(beakerDirPin, LOW);
      // Spin motor slowly
      
      
        digitalWrite(beakerStepPin, HIGH);
        delayMicroseconds(2000);
        digitalWrite(beakerStepPin, LOW);
        delayMicroseconds(2000);
     
      delay(1000); // Wait a second
}

void step_forward(){
  digitalWrite(beakerDirPin, HIGH);
     
  for(int x = 0; x < 10; x++)
  {
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  }
}

void step_back(){
  digitalWrite(beakerDirPin, LOW);
     
  for(int x = 0; x < 10; x++)
  {
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  }
}

void moveBeaker(int beakerIndex, bool homeIndex){
  int steps = round(degrees_between_beaker*gear_ratio*stepsPerRevolution*beakerIndex);
  // Rotate to correct position

  digitalWrite(beakerDirPin, homeIndex);
  for(int x = 0; x < steps; x++)
  {
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  } 
  
}

void beakerController(int beakerIndex){
  if(beakerHome){
    moveBeaker(beakerIndex, false);
    beakerHome = 0;
    currentBeakerIndex = beakerIndex;
  }else{
    //Return beaker to home position
    moveBeaker(currentBeakerIndex, true);
    delay(2000);
    moveBeaker(beakerIndex, false);
    beakerHome = 0;
    currentBeakerIndex = beakerIndex;
  }
}

void returnHome(){
  moveBeaker(currentBeakerIndex, true);
  beakerHome = 1;
  currentBeakerIndex = 0;
}

//=================================================================================================
// FUNNEL FLAP CONTROLLER

void openFlap(){
  if (!flapIsOpen){
    for (pos = 0; pos <= 180; pos += 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = true;
  }else{
    Serial.println("ERROR: Funnel flap is already open");
  }
}

void closeFlap(){
  if (flapIsOpen){
    for (pos = 180; pos > 0; pos -= 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = false;
  }else{
    Serial.println("ERROR: Funnel flap is already closed");
  }
}
