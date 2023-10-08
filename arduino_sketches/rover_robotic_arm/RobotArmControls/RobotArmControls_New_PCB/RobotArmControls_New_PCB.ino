//we inport the needed libraries nameley AccelStepper (used for stepper control) and ezButton (takes care of button debouncing)
#include <ezButton.h>
#include <AccelStepper.h>
#include <MultiStepper.h>
#include <JrkG2.h>

//we initialize the Wrist Limit switches objects
ezButton LS1(43);
ezButton LS2(44);
ezButton LS3(45);
ezButton LS4(46);

//we declare the steppers
AccelStepper wristRight(AccelStepper::DRIVER, 11, 10); //step, direction
AccelStepper wristLeft(AccelStepper::DRIVER, 9, 8);
AccelStepper tower(AccelStepper::DRIVER, 7, 6);
AccelStepper endEffector(AccelStepper::DRIVER, 13, 12);

//we set up the multistepper
MultiStepper wristEE;

//we declare objects for the Linear Actuator drivers
//TODO: set the device number for LA2 to 12
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

//declare pin numbers for the linear actuator optical encoders
const int L1_ENCODERPIN = 2;
const int L2_ENCODERPIN = 3;

//we set up the max range constants/variables for the diffrents motors/Steppers
//TODO: make sure that these values are accurate and or are updated during the init sequence
//const long WRISTMAXRANGE = 2500;
constexpr long WRISTPITCHMAXRANGE = 2500;
const long WRISTROLLMAXRANGE = 17500;
const long ENDEFFECTORMAXRANGE = 861;
const long TOWERMAXRANGE = 2500;

//Timers to remove false positive counts from encoder pulse count
unsigned long trigDelay_LA1 = millis();
unsigned long trigDelay_LA2 = millis();

int timeBetweenPulses = 60; //time between pulses at 125 speed

//LA Encoder count variables
int count[] = {0,0}; //count[0] tracks LA1 encoder pulses and count[1] tracks LA2 encoder pulses

//direction array to track the direction the Linear Actuators are moving in
//directionLA[0] tracks the direction of LA1 and directionLA[1] tracks the direction of LA2
int directionLA[2]; 

//input size var
const int INPUT_SIZE = 12;
char input[INPUT_SIZE + 1];
char* tmp;     //stores chars as we tokenize
char* command; //cmd type; stop, EE, etc
int dir;       //1 or -1
int speed;     //0-1000 for motors, 0-600 for LA's (new PCB)

//stop vars
int EEStopClose = 0;
int EEStopOpen = 0;
int wristStopUp = 0;
int wristStopDown = 0;
bool wristStop = true;

//used to limit serial output from encoder feedback (every 50ms)
static uint32_t start = millis();

void setup() {
  //we start the serial comms
  Serial.begin(115200);

  //start I2C comms
  Wire.begin();

  //we set the debounce time of the limitSwitches, that is the amount of time the program is going to wait until it accepts another input from the switches
  LS1.setDebounceTime(50); //set debounce time to 50 milliseconds
  LS2.setDebounceTime(50);
  LS3.setDebounceTime(50);
  LS4.setDebounceTime(50);

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
  //Then give them to MultiStepper to manage
  wristEE.addStepper(wristRight);
  wristEE.addStepper(wristLeft);

  //set up the optical encoder pins with pullup resistors
  pinMode(L1_ENCODERPIN, INPUT_PULLUP);
  pinMode(L2_ENCODERPIN, INPUT_PULLUP);
  //set up interrupt pins for the LA encoders
  attachInterrupt(digitalPinToInterrupt(L1_ENCODERPIN),counter_LA1,RISING);
  attachInterrupt(digitalPinToInterrupt(L2_ENCODERPIN),counter_LA2,RISING);

  ////zero LA1 to the most retracted position
  //trigDelay_LA1 = millis();
  //zeroActuators("L1", 125);
  ////zero LA2 to the most retracted position
  //trigDelay_LA2 = millis();
  //zeroActuators("L2",125);

  //zeroEndEffector();

  //we call stop to make sure that none of the motors move
  stop();
}

void loop() {
  //we do some of the needed setup to get the limitSwitches working
  LS1.loop(); //MUST call the loop() function first
  LS2.loop();
  LS3.loop();
  LS4.loop();

  //when LS's are pressed the states are toggled to allow/disallow movement to a direction
  if (EEStopClose == LS1.getState()) {
    if (LS1.getState()) {
      Serial.print("\nLS1 unpressed; EE may close!");
    } else {
      Serial.print("\nLS1 pressed; no EE closing!");
    }
    EEStopClose = !LS1.getState();
  }
  if (EEStopOpen == LS2.getState()) {
    if (LS2.getState()) {
      Serial.print("\nLS2 unpressed; EE may open!");
    } else {
      Serial.print("\nLS2 pressed; no EE opening!");
    }
    EEStopOpen = !LS2.getState();
  }
  if (wristStopUp == LS3.getState()) {
    if (LS3.getState()) {
      Serial.print("\nLS4 unpressed; wrist may pitch up!");
    } else {
      wristStop = true;
      Serial.print("\nLS3 pressed; no pitching up!");
    }
    wristStopUp = !LS3.getState();
  }
  if (wristStopDown == LS4.getState()) {
    if (LS4.getState()) {
      Serial.print("\nLS4 unpressed; wrist may pitch down!");
    } else {
      wristStop = true;
      Serial.print("\nLS4 pressed; no pitching down!");
    }
    wristStopDown = !LS4.getState();
  }
  
  //we need to add a timeout function which stops everything if we haven't gotten a new instruction in a set ammount of time
  //that being said, this could probably be done on the python side of things and then we just send the stop command here, YES!

  //we check if a command has been given and then interpret it
  if (Serial.available()) {
    
    //use memset to 'empty' input buffer; may not be necessary,
    //but ensures that input is in a well-defined state
    memset(input, 0, sizeof(input));

    //characters from the serial input are read into the input array
    //readBytesUntil returns the number of characters read to the size variable
    byte size = Serial.readBytesUntil('!',input, INPUT_SIZE);

    //Add the final 0 to end the C string
    input[size] = 0;

    //Typical command example:
    //"EE;OP;1000;!"
    Serial.print("\nNew command received: ");
    Serial.println(input);

    //Read each command pair
    //we get the first part of the command and we assign it to a variable
    tmp = strtok(input, ";");
    command = tmp;
    dir = 0;
    speed = 0;

    //we print all of the data which was extracted
    //Serial.println("Here is the extracted information from the command");
    Serial.print("Command: ");
    Serial.println(command);

    //use only one if which checks if the type is motor, if that's the case we get all of the required motor information
    //in theory we don't need a more complicated if because some of the lines are repeated and can be extracted, and we will make sure that the only valid inputs are send by the python code

    //if to check which type of command was entered
    if (strcmp(command, "stop")) {
      //we get the rest of the inforation needed for the motors
      tmp = strtok(NULL, ";");
      dir = atoi(tmp);

      tmp = strtok(NULL, ";");
      speed = atoi(tmp);

      Serial.print("Dir: ");
      Serial.println(dir);
      Serial.print("Speed: ");
      Serial.print(speed);
      Serial.print("!");//add ! delimiter for receiving node
    } //end of if


    //we do some string manipulation to extract the different parts of the string
    //either we have an if which checks if there is a space character/a seperation character deoending on what the command format is

    //before the following block of code is executed, we check to see if the command is the same as the last one, if this is the case, we

    //TODO: Things which will taken care of by the python code
    /*
       Things which will be taken care of by the python code
       - Timing out code, that is if a command hasn't been send in a long time, the python code sends a stop command so that we don't continue actuating the arm
          - This can probably be taken care of by the code on the PI
       - Checking if the commands are the same, that is if we're moving the wrist, instead of sending the "WR" command over and over, the python code only sends it once and if anything changes (ex: speed)
         When the command stops being send the code is going to send the "stop" command, or if we want to actuate another motor, the code is going to send the corresponding command

    */

    if (!strcmp(command, "stop")) {
      //we stop every motor exaclty where it is
      //this command could also be the one sent when the joystick comes back to it's neutral position
      //Serial.println("The stop command was entered");
      //Serial.println("Stopping all motors");

      //we call the stop function
      stop();

    }
    else if (!strcmp(command, "EE")) {
      //Serial.println("The EE command was entered");
      //stop();
      wristStop = true;

      endEffector.setMaxSpeed(speed);
      endEffector.moveTo(dir*ENDEFFECTORMAXRANGE);
      
    }
    else if (!strcmp(command, "WR")) {
      //here we control the roll of the wrist
      //We might need to have a different variable than WRISTMAXRANGE, because when doing the roll motion, i think the wrist doesn't have any limits
      //Serial.println("The WR command was entered");
      //stop();

      //we set the wristStop bool to false so that the motors can move
      wristStop = false;

      //we set the speed of the motors
      wristRight.setMaxSpeed(speed);
      wristLeft.setMaxSpeed(speed);

      //we set the target of the motors
      long tmpPositions[2] = {dir*WRISTROLLMAXRANGE, dir*WRISTROLLMAXRANGE};
      wristEE.moveTo(tmpPositions);
    }
    else if (!strcmp(command, "WP")) {
      //here we control the pitch of the wrist
      //Serial.println("The WP command was entered");
      //stop();
      wristStop = false;

      wristRight.setMaxSpeed(speed);
      wristLeft.setMaxSpeed(speed);

      long tmpPositions[2] = {dir*WRISTPITCHMAXRANGE, -dir*WRISTPITCHMAXRANGE};
      wristEE.moveTo(tmpPositions);
    
    }
    else if (!strcmp(command, "TW")) {
      //Serial.println("The TW command was entered");
      //stop();
      wristStop = true;

      //we set the speed for the motor and then set it's target destination
      tower.setMaxSpeed(speed);
      tower.moveTo(dir*TOWERMAXRANGE);
    }
    //consider using or instead of separate ifs for L1 and L2
    else if (!strcmp(command, "L1")) {
      //Serial.println("The L1 command was entered");
      //stop();
      wristStop = true;
      moveActuators(&command, &dir, &speed);
    }
    else if (!strcmp(command, "L2")) {
      //Serial.println("The L2 command was entered");
      //stop();
      wristStop = true;
      moveActuators(&command, &dir, &speed);
    }
    else {
      Serial.print("\nInvalid command!");//add ! delimiter for receiving node
    }

  } //end of if serial available

  //we make the steppers move, that is that we call the run functions for all of the stepper funcs
  //if which checks if wristStop is true or false. if false, the run function is called permitting the motors to move.
  if (!wristStop) {
    if ((LS3.getState() and dir == -1) | (LS4.getState() and dir == 1)) {
      wristEE.run();
    }
  }
  tower.run();
  if ((LS1.getState() and dir == -1) | (LS2.getState() and dir == 1)) {
    endEffector.run();
  }

  //send the current linear actuator positions over serial
  /*if (millis() - start >= 50) {
    sendLinearActuatorPositions();
    start = millis();
  }*/
} //end of loop()

//we create the stop function since it's functionality can be used multiple times
void stop() {

  //This function stops every motor from moving

  //we stop every motor exaclty where it is
  //this command could also be the one sent when the joystick comes back to it's neutral position
  Serial.print("\nStopping all motors!");//add ! delimiter for receiving node

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

  //we stop the LAs
  LA1.stopMotor();
  LA2.stopMotor();

} //end of stop

//this function is the one which moves the linear actuators
void moveActuators(char* *command, int *dir, int *speed) {
  
  //we check to see which actuator needs to move and then extend it 
  if (!strcmp(*command, "L1")) {
    //if dir is 1 extend, if -1 retract
    //The linear actuator driver sets the speed by subtracting 2048 from the given value so a value of 2048 corresponds to 0 speed
    LA1.setTarget(2048+((*dir)*(*speed)));
    directionLA[0] = *dir;
  }
  else {
    //we extend or retract L2
    LA2.setTarget(2048+((*dir)*(*speed)));
    directionLA[1] = *dir;
  } //end of else

} //end of moveActuators()

//Method to set Linear Actuators at 0 in stroke position
void zeroActuators(char* actuator, int speed){
  stop(); // stop all motors
  
  int index = 0;

  if (!strcmp(actuator, "L2")){
    index = 1;
  }

  // timer to ensure that the encoder count hasn't been updated for long enough before stopping the linear actuator 
  unsigned long prevTimer = millis(); 
  int homeFlag = 0;
  int prevCount = 0;

  while(homeFlag == 0){
    moveActuators(&actuator, 1, &speed); // retracts the actuator
    
    if(prevCount == count){ // if the previous count hasn't updated the actuator might have stopped
      if(millis() - prevTimer > timeBetweenPulses){ // if it has stopped for the time indicated by timeBetweenPulses it's done retracting
        stop();
        //reset count, break out of loop
        count[index] = 0;
        homeFlag = 1;
      }
    }else{ // if the count is updating reset the prevCount variable and timer
      prevCount = count[index];
      prevTimer = millis();
    }
  }
}


//Zero End Effector to middle position 
//***CHECK SIGNS IN MOVETO FUNCTIONS***
void zeroEndEffector(){
  stop();
  Serial.print("\nZeroing EE!");//add ! delimiter for receiving node
  
  // set max speed and acceleration, we could alternatively set these values based on function inputs
  endEffector.setMaxSpeed(50.0);
  endEffector.setAcceleration(1000.0);
  //set target position for max range, this target accounts for the worst case scenario of the initial stepper position
  endEffector.moveTo(ENDEFFECTORMAXRANGE*2);

  while (LS1.getState() == HIGH){
    endEffector.run(); //moves motor towards target position
    Serial.print(LS1.getState());//add ! delimiter for receiving node
    Serial.print("!");//add ! delimiter for receiving node
  }
  endEffector.stop(); //stop motor
  Serial.print("\nEE STOPPING!");//add ! delimiter for receiving node

  endEffector.move(-ENDEFFECTORMAXRANGE); //relative position, should move stepper to the middle
  // run the motor until the distance from the target position is 0.
  while (endEffector.distanceToGo() != 0){
    endEffector.run();
  }

  long numSteps = endEffector.currentPosition(); // returns our position relative to our initial point
  endEffector.setCurrentPosition(numSteps); //sets current position to be the absolute zero position
  Serial.print("\nEE zeroing complete!");//add ! delimiter for receiving node
}

//Zero wrist to middle position
//***CHECK SIGNS***
//INCOMPLETE
void zeroWristPitch(){
  stop();
  // condition for while loop
  int homeFlag = 0;
  // positions
  long positions[2] = {WRISTPITCHMAXRANGE, -1*WRISTPITCHMAXRANGE};
  // set speeds and target positions
  wristRight.setMaxSpeed(500.0);
  wristLeft.setMaxSpeed(500.0);
  wristEE.moveTo(positions);

  while (homeFlag == 0){
    wristEE.run(); // move stepper to target position
    if (LS2.getState() == LOW){ // if limit switch is pressed
      homeFlag = 1; // break out of while loop, so motors are not being run anymore
    }
  }

  // move them back to the middle
}

// ISR for LA1 encoder
void counter_LA1(){
  if (millis() - trigDelay_LA1 >= timeBetweenPulses){
    trigDelay_LA1 = millis();
    count[0] += directionLA[0];
  } 
}

// ISR for LA2 encoder
void counter_LA2(){
  if (millis() - trigDelay_LA2 >= timeBetweenPulses){
    trigDelay_LA2 = millis();
    count[1] += directionLA[1];
  } 
}

// converts encoder pulses to mm and sends them over serial
void sendLinearActuatorPositions(){
  float positionInMM_LA1 = count[0]/100 * 25.4;
  float positionInMM_LA2 = count[1]/100 * 25.4;
  Serial.print(positionInMM_LA1);
  Serial.print(";");
  Serial.print(positionInMM_LA2);
  Serial.print("!"); //add ! delimiter for receiving node
}
