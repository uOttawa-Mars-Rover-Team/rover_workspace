/*
   This program is the (as of now) the main robotic arm control code. That is the program which is going to take in inputs from the joystick (or keyboard while testing)
   and is going to interpret it and control the motors accordingly.

   Author of this version of the program: Olivier Caron (30-jan-2022)
*/

//we inport the needed libraries nameley AccelStepper (used for stepper control) and ezButton (takes care of button debouncing)
#include <ezButton.h>
#include <AccelStepper.h>
#include <MultiStepper.h>


//we declare and sometimes initialize all of the necessary variables


//we initialize the two Wrist Limit switches objects
ezButton limitSwitchRed(42);  // create ezButton object that attach to pin 7;
ezButton limitSwitchBlack(43);  // create ezButton object that attach to pin 7;

//we declare the stepper enable pins
int wristRightEnablePin = 27; //stepper 2
int wristLeftEnablePin = 30; //stepper 3
int towerEnablePin = 33; //stepper 4
int endEffectorEnablePin = 24; //stepper 1

//we declare the steppers
AccelStepper wristRight(AccelStepper::DRIVER, 9, 8); //step, direction
AccelStepper wristLeft(AccelStepper::DRIVER, 11, 10);
AccelStepper tower(AccelStepper::DRIVER, 13, 12);
//TODO: put right pin numbers for the tower stepper
AccelStepper endEffector(AccelStepper::DRIVER, 7, 6);

//we set up the multistepper
MultiStepper wristEE;

//enable pin for LA2
int LA2_EN = 30;

//we declare the Linear Actuator pins
//TODO: make sure that the pins are the right ones
int LA1_RPWM_Output = 3; // Arduino PWM output pin 5; connect to IBT-2 pin 1 (RPWM) Forward
int LA1_LPWM_Output = 2; // Arduino PWM output pin 6; connect to IBT-2 pin 2 (LPWM) Backward;
int LA2_RPWM_Output = 5;
int LA2_LPWM_Output = 4;

//we set up the max range constants/variables for the diffrents motors/Steppers

//TODO: make sure that these values are accurate and or are updated during the init sequence
//const long wristMaxRange = 2500;
constexpr long wristPitchMaxRange = 2500;
const long wristRollMaxRange = 17500;

const long endEffectorMaxRange = 861;
const long towerMaxRange = 2500;

//stop var for Wrist
bool wristStop = true;

//input size var
const int INPUT_SIZE = 11;

/*
struct Command {
public:

  String commandType;
  int direction;
  int speed;

};
*/

//we set up the motor and button variables and
void setup() {
  //we start the serial comms
  Serial.begin(115200);

  //we set the debounce time of the limitSwitches, that is the amount of time the program is going to wait until it accepts another input from the switches
  limitSwitchRed.setDebounceTime(50); // set debounce time to 50 milliseconds
  limitSwitchBlack.setDebounceTime(50);

  //we do some stepper setup stuff
  // Configure each stepper

  //setup and enable the stepper enable pins
  pinMode(wristRightEnablePin, OUTPUT);
  pinMode(wristLeftEnablePin, OUTPUT);
  pinMode(towerEnablePin, OUTPUT);
  pinMode(endEffectorEnablePin, OUTPUT);

  //we set the pins to high
  digitalWrite(wristRightEnablePin, HIGH);
  digitalWrite(wristLeftEnablePin, HIGH);
  digitalWrite(towerEnablePin, HIGH);
  digitalWrite(endEffectorEnablePin, HIGH);

  //we configure the default speed for each stepper
  //TODO: verify each of these speeds in a separate test and then modify these values
  wristLeft.setMaxSpeed(500.0);
  wristRight.setMaxSpeed(500.0);
  tower.setMaxSpeed(50.0);
  tower.setAcceleration(1000.0);
  endEffector.setMaxSpeed(50.0);
  endEffector.setAcceleration(1000.0);

  //TODO: decide if we want to add acceleration to the motors when using them

  //we add the wristSteppers to the multiStepper object
  // Then give them to MultiStepper to manage
  wristEE.addStepper(wristRight);
  wristEE.addStepper(wristLeft);

  //we also do some linear actuator setup stuff
  //maybe enable the LA and set the basic speed?
  //we setup the pin modes for the LA
  pinMode(LA1_RPWM_Output, OUTPUT);
  pinMode(LA1_LPWM_Output, OUTPUT);
  pinMode(LA2_RPWM_Output, OUTPUT);
  pinMode(LA2_LPWM_Output, OUTPUT);

  //we call stop to make sure that none of the motors move
  stop();

  //we enable the LA2
  digitalWrite(LA2_EN, HIGH);
}

/*
Command parseCommand() {

}
*/

void loop() {
  //we do some of the needed setup to get the limitSwitches working
  limitSwitchRed.loop(); // MUST call the loop() function first
  limitSwitchBlack.loop();

  //we need to add a timeout function which stops everything if we haven't gotten a new instruction in a set ammount of time
  //that being said, this could probably be done on the python side of things and then we just send the stop command here, YES!

  //Typical command example:
  //"EE;OP;1000;!"

  //we check if a command has been given and then interpret it
  if (Serial.available()) {
    //Serial.println("\nA New command was sent");
    Serial.println("\nNew Command Received");

    
    //char tmp = Serial.read();
    //int tmpSize = atoi(tmp);
    //Serial.print("Tmp:");
    //Serial.println(tmp);
    
    //New potential way to read input
    // Get next command from Serial (add 1 for final 0)
    char input[INPUT_SIZE + 1];
    byte size = Serial.readBytesUntil('!',input, INPUT_SIZE);
    // Add the final 0 to end the C string
    input[size] = 0;

    //we print the input
    Serial.println(input);

    //we create all of the necessary variables for the command information
    //String type;
    String command;
    int dir = 0; //setting default value, in theory it's impossible for the direction to be 0
    int speed = 0; //setting the default value, whenever this variable will be assigned, it is in theory impossible that the speed will be 0

    // Read each command pair
    //we get the first part of the command and we assign it to a variable
    char* inputStr = strtok(input, ";");
    //we extract the command type from inputStr
    //type = inputStr;
    command = inputStr;

    //use only one if which checks if the type is motor, if that's the case we get all of the required motor information
    //in theory we don't need a more complicated if because some of the lines are repeated and can be extracted, and we will make sure that the only valid inputs are send by the python code

    //we get the command from the input data, this block is exectued regardless of if we're doing M or C commands
    //inputStr = strtok(NULL, ";");
    //command = inputStr;

    //if to check which type of command was entered
    if (!command.equals("stop")){
      //Serial.println("The Motor command type was entered");
      Serial.println("Motor Command Entered");
      //we get the rest of the inforation needed for the motors

      //we get the dir
      //Serial.println("input str: " + inputStr;
      inputStr = strtok(NULL, ";");
      dir = atoi(inputStr);

      //we get the speed
      inputStr = strtok(NULL, ";");
      speed = atoi(inputStr);
    } //end of if

    //we print all of the data which was extracted
    //Serial.println("Here is the extracted information from the command");
    Serial.println("Command Info");
    //Serial.println("command Type: " + type);
    Serial.println("Command: " + command);
    Serial.print("Dir: ");
    Serial.println(dir);
    Serial.print("Speed: ");
    Serial.println(speed);

    //we do some string manipulation to extract the different parts of the string
    //either we have an if which checks if there is a space character/a seperation character deoending on what the command format is

    //before the following block of code is executed, we check to see if the command is the same as the last one, if this is the case, we

    //TODO: Things which will taken care of by the python code
    /*
       Things which will be taken care of by the python code
       - Timing out code, that is if a command hasn't been send in a long time, the python code sends a stop command so that we don't continue actuating the arm
          - This can probably be taken care of by teh code on the PI
       - Checking if the commands are the same, that is if we're moving the wrist, instead of sending the "WR" command over and over, the python code only sends it once and if anything changes (ex: speed)
         When the command stops being send the code is going to send the "stop" command, or if we want to actuate another motor, the code is going to send the corresponding command

    */

    
    if (command.equals("stop")) {
      //we stop every motor exaclty where it is
      //this command could also be the one sent when the joystick comes back to it's neutral position
      //Serial.println("The stop command was entered");
      //Serial.println("Stopping all motors");

      //we call the stop function
      stop();

    }
    else if (command.equals("EE")) {
      //Serial.println("The EE command was entered");
      stop();

      //we set the speed for the motor and then set it's target destination
      endEffector.setMaxSpeed(speed);
      endEffector.moveTo(dir*endEffectorMaxRange);
    }
    else if (command.equals("WR")) {
      //here we control the roll of the wrist
      //We might need to have a different variable than wristMaxRange, because when doing the roll motion, i think the wrist doesn't have any limits
      //Serial.println("The WR command was entered");
      stop();

      //we set the wristStop bool to false so that the motors can move
      wristStop = false;

      //we set the speed of the motors
      wristRight.setMaxSpeed(speed);
      wristLeft.setMaxSpeed(speed);

      //we set the target of the motors
      long tmpPositions[2] = {dir*wristRollMaxRange, dir*wristRollMaxRange};
      wristEE.moveTo(tmpPositions);
    }
    else if (command.equals("WP")){
      //here we control the pitch of the wrist
      //Serial.println("The WP command was entered");
      stop();

      //we set the wristStop bool to false so that the motors can move
      wristStop = false;

      //we set the speed of the motors
      wristRight.setMaxSpeed(speed);
      wristLeft.setMaxSpeed(speed);

      //we set the target of the motors
      //we multiply the direction by the maxRange, in the case of the second item, we also multiply it by -1 because it's supposed to be the opposite of item 1
      long tmpPositions[2] = {dir*wristPitchMaxRange, -1*dir*wristPitchMaxRange};
      wristEE.moveTo(tmpPositions);
    }
    else if (command.equals("TW")) {
      //Serial.println("The TW command was entered");
      stop();

      //we set the speed for the motor and then set it's target destination
      tower.setMaxSpeed(speed);
      tower.moveTo(dir*towerMaxRange);
    }
    //consider using or instead of separate ifs for L1 and L2
    else if (command.equals("L1")) {
      //Serial.println("The L1 command was entered");
      moveActuators(command, dir, speed);
    }
    else if (command.equals("L2")) {
      //Serial.println("The L2 command was entered");
      moveActuators(command, dir, speed);
    }
    else {
      Serial.println("Invalid command");
    }

  } //end of if serial available

  //we make the steppers move, that is that we call the run functions for all of the stepper funcs
  //wristEE.run();

  //if which checks if wristStop is true or false. if false, the run function is called permitting the motors to move.
  if (!wristStop) {
    wristEE.run();
  }
  tower.run();
  endEffector.run();
} //end of loop()

//we create the stop function since it's functionality can be used multiple times
void stop() {

  //This function stops every motor from moving

  //we stop every motor exaclty where it is
  //this command could also be the one sent when the joystick comes back to it's neutral position
  //Serial.println("The stop function was entered");
  Serial.println("Stopping all motors");

  //we stop the EE
  endEffector.stop();
  endEffector.runToPosition();

  //we stop the tower
  tower.stop();
  tower.runToPosition();

  //we stop the wrist
  //it's currently not 100% clear how to do this, but either we swith a bool to off
  //or we change their target so that it becomes their current position
  //Make sure to test this in a smaller context
  //long tmpPositions[2] = {wristRight.currentPosition(), wristLeft.currentPosition()};
  //wristEE.moveTo(tmpPositions);
  //we set the wristStop command to true so that the run command cannot be called and the motors will thus not move.
  wristStop = true;



  //we stop the LA
  //again this is somewhat unclear but we could by instance set their enable pin to low

  //LA 1
  analogWrite(LA1_RPWM_Output, 0);
  analogWrite(LA1_LPWM_Output, 0);

  //LA 2
  analogWrite(LA2_RPWM_Output, 0);
  analogWrite(LA2_LPWM_Output, 0);

}



//this function is the one which moves the linear actuators
void moveActuators(String command, int dir, int speed) {
  stop();

  //Extend is done on the LPWM pin
  //Rectract is done on the RPWM pin

  //in theory we don't need to set the other pins to 0 because we called stop() at the start of this function

  if (dir == 1){
    //we check to see which actuator needs to move and then extend it 
    if (command.equals("L1")) {
      //we extend L1
      analogWrite(LA1_LPWM_Output, speed);
    }
    else {
      //we extend L2
      analogWrite(LA2_LPWM_Output, speed);
    } //end of else
  } 
  else {
    //we retract
    if (command.equals("L1")) {
      //we retract L1
      analogWrite(LA1_RPWM_Output, speed);
    }
    else {
      //we retract L2
      analogWrite(LA2_RPWM_Output, speed);
    } //end of else
  } //end of if

} //end of moveActuators()
