/*
Life Detection Module

Maintainer: Ken Lorbetskie
*/

#include <ros.h>
#include <std_msgs/Empty.h>
#include <std_msgs/String.h>
#include <std_msgs/UInt8.h>
#include <Servo.h>

ros::NodeHandle  nh;
//=================================================================================================
// VACUUM HOSE EXTENDER 

const int stepsPerRevolution = 200;
const int hoseDirPin = 2;
const int hoseStepPin = 3;
const int upperPin = 13; 
const int lowerPin = 12;

int upperLimit = LOW;
int lowerLimit = LOW;
int dir = 0;

/*
 * Function:  hoseCb 
 * --------------------
 * callback function that raises or lowers the
 * the hose depending on the input parameter.
 *
 *  hose_cmd: UInt8 ROS topic that passes a number which 
 *            maps to a certain command.
 *            
 *            hose_cmd:
 *                1 : Lower the hose
 *                2 : Raise the hose
 *  (Anything else) : Do nothing
 */
void hoseCb( const std_msgs::UInt8& hose_cmd){
  int stopFlag = LOW;

  if (hose_cmd.data==1){
    // Move Down
    nh.loginfo("Moving hose down....");
    dir = 1;
    digitalWrite(hoseDirPin, HIGH);
  }
  else if (hose_cmd.data==2){
    // Move Up
    nh.loginfo("Moving hose up....");
    dir = -1;
    digitalWrite(hoseDirPin, LOW);
  }else{
    dir = 0;
    return;
  }
  // Spin motor slowly
  while (!checkLimits()){
    nh.spinOnce();
    for(int x = 0; x < stepsPerRevolution; x++){
      if (!checkLimits()){
      digitalWrite(hoseStepPin, HIGH);
      delayMicroseconds(2000);
      digitalWrite(hoseStepPin, LOW);
      delayMicroseconds(2000);
      }else{
        stopFlag = HIGH;
        break; 
      }
    }
    if(stopFlag == HIGH){
      nh.loginfo("Limit reached. Backing off....");
      backOff();
      break;
    }
  }
}

/*
 * Function:  checkLimits 
 * --------------------
 * reads the state of the upper an lower limit
 * switches of the vacuum hose extender.
 * 
 * returns: true if a switch is pressed
 */
bool checkLimits(){
  upperLimit = digitalRead(upperPin);
  lowerLimit = digitalRead(lowerPin);

  if(upperLimit  == LOW){
    nh.logwarn("Upper Limit LOW");
  }
  if(lowerLimit  == LOW){
    nh.logwarn("Lower Limit LOW");
  }

  if(!upperLimit || !lowerLimit){
    return true;
  }else{
    return false;
  }
}

/*
 * Function:  backOff 
 * --------------------
 * lowers/raises the hose to release pressure off of
 * the limit switch.
 * 
 */
void backOff(){
  if (dir == 1 && !lowerLimit){
     digitalWrite(hoseDirPin, LOW);
  }else if (dir == -1 && !upperLimit){
     digitalWrite(hoseDirPin, HIGH);
  }else{
    nh.logerror("check limit switches");
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
  nh.loginfo("backOff: Done");
}

//=================================================================================================
// VACUUM CONTROLLER

const int vacuumPin = 10;

int vacuumState = LOW;
Servo servo;
int pos = 0;
boolean flapIsOpen = false;

/*
 * Function:  vacuumCb 
 * --------------------
 * callback function that toggles the vacuum relay.
 */
void vacuumCb( const std_msgs::Empty& toggle_vacuum){
  if (vacuumState == LOW){
    nh.loginfo("Turning on vacuum....");
    digitalWrite(vacuumPin, LOW);
    vacuumState = HIGH;
  }else{
    nh.loginfo("Turning off vacuum....");
    digitalWrite(vacuumPin, HIGH);
    vacuumState = LOW;
  }
}

// FUNNEL FLAP CONTROLLER
/*
 * Function:  funnelFlapCb 
 * --------------------
 * callback function that toggles the position of the funnel flap
 */
void funnelFlapCb( const std_msgs::Empty& toggle_funnel_flap){
  if (!flapIsOpen){
    nh.loginfo("Opening funnel flap....");
    for (pos = 0; pos <= 180; pos += 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = true;
    nh.loginfo("funnelFlapCb: Done");
  }else{
    nh.loginfo("Closing funnel flap....");
    for (pos = 180; pos > 0; pos -= 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = false;
    nh.loginfo("funnelFlapCb: Done");
  }
}

//=================================================================================================
// BEAKER SAMPLE SYSTEM CONTROLLER

const float degrees_between_beaker = 25.00/360;
const float gear_ratio = 309/14;
const int beakerDirPin = 6;
const int beakerStepPin = 7;

int currentBeakerIndex = 0;
int beakerHome = 1;

/*
 * Function:  sampleSystemCb 
 * --------------------
 * callback function that controls the sample system
 *
 *  sample_sys_cmd: UInt8 ROS topic that passes a number which 
 *            maps to a certain command.
 *            
 *            sample_sys_cmd:
 *                0 : Return Sample System to home position
 *             1-10 : Index beaker[1-10]
 *               11 : Rotate the system forward
 *               12 : Rotate the system backward
 *  (Anything else) : Do nothing
 */
void sampleSystemCb( const std_msgs::UInt8& sample_sys_cmd){
  //Return Sampler to home position
  if (sample_sys_cmd.data==0){
    returnHome();
  }
  //Beaker Selection
  else if (sample_sys_cmd.data>0 && sample_sys_cmd.data<11){
    beakerController(sample_sys_cmd.data);
  }
  //Step Foward
  else if (sample_sys_cmd.data==11){
    stepForward();
  }
  //Step Backward
  else if (sample_sys_cmd.data==12){
    stepBack();
  }
}

/*
 * Function:  aggitationCb 
 * --------------------
 * callback function that shakes the samples
 *
 *  aggitation_timer: UInt8 ROS topic that passes the amount of time 
 *                    (in seconds) to aggitate the samples for.
 */
void aggitationCb( const std_msgs::UInt8& aggitation_timer){
  unsigned long starttime = millis();
  unsigned long endtime = starttime;
  int timer = aggitation_timer.data*1000;
  char log_str [100];
  snprintf(log_str, 100, "Aggitating samples for: %d seconds....", aggitation_timer.data);
  nh.loginfo(log_str);
  
  while ((endtime - starttime) <=timer){
    digitalWrite(beakerDirPin, HIGH);

    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
    
    delay(1000); // Wait a second
    digitalWrite(beakerDirPin, LOW);

    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
    delay(1000); // Wait a second
    endtime = millis();
  }
  nh.loginfo("aggitationCb: Done");  
}

/*
 * Function:  stepForward 
 * --------------------
 * steps the motor foward 10 times to make fine adjustment
 * to the sample system's position
 */
void stepForward(){
  nh.loginfo("Step Forward");
  digitalWrite(beakerDirPin, HIGH);
     
  for(int x = 0; x < 10; x++)
  {
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  }
}

/*
 * Function:  stepBack
 * --------------------
 * steps the motor backward 10 times to make fine adjustment
 * to the sample system's position
 */
void stepBack(){
  nh.loginfo("Step Backward");
  digitalWrite(beakerDirPin, LOW);
     
  for(int x = 0; x < 10; x++)
  {
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  }
}

/*
 * Function:  moveBeaker 
 * --------------------
 * rotates the Sample System to the desired postion
 *
 *  beakerIndex: The desired beaker to fetch
 *      reverse: Flag that rotates system in reverse direction
 */
void moveBeaker(int beakerIndex, bool reverse){
  int steps = round(degrees_between_beaker*gear_ratio*stepsPerRevolution*beakerIndex);
  // Rotate to correct position

  char log_str [100];
  if (reverse){
    snprintf(log_str, 100, "Rotating sampler to position: %d ....", 0);
  }else{
    snprintf(log_str, 100, "Rotating sampler to position: %d ....", beakerIndex);
  }
  nh.loginfo(log_str);
  
  digitalWrite(beakerDirPin, reverse);
  for(int x = 0; x < steps; x++)
  {
    nh.spinOnce();
    digitalWrite(beakerStepPin, HIGH);
    delayMicroseconds(2000);
    digitalWrite(beakerStepPin, LOW);
    delayMicroseconds(2000);
  } 
  
}

/*
 * Function:  beakerController 
 * --------------------
 * keeps track of Sample System's state and rotates
 * system to desired position
 *
 *  beakerIndex: The desired beaker to fetch
 */
void beakerController(int beakerIndex){
  if(beakerHome){
    moveBeaker(beakerIndex, false);
    beakerHome = 0;
    currentBeakerIndex = beakerIndex;
  }else{
    //Return beaker to home position
    nh.loginfo("Returning sampler to home position....");
    moveBeaker(currentBeakerIndex, true);
    nh.loginfo("beakerController: Done");
    delay(2000);
    moveBeaker(beakerIndex, false);
    beakerHome = 0;
    currentBeakerIndex = beakerIndex;
  }
  nh.loginfo("beakerController: Done");
}

/*
 * Function:  returnHome 
 * --------------------
 * returns Sample system to home postion
 */
void returnHome(){
  moveBeaker(currentBeakerIndex, true);
  beakerHome = 1;
  currentBeakerIndex = 0;
}

//=================================================================================================

//Publishing topics
std_msgs::String str_msg;
ros::Publisher logger("life_detection_logger", &str_msg);

//Subscribing topics hose_cmd
ros::Subscriber<std_msgs::UInt8> hoseSub("hose_cmd", &hoseCb );
ros::Subscriber<std_msgs::UInt8> sampleSystemSub("sample_sys_cmd", &sampleSystemCb );
ros::Subscriber<std_msgs::UInt8> aggitationSub("aggitation_timer", &aggitationCb );
ros::Subscriber<std_msgs::Empty> vacuumSub("toggle_vacuum", &vacuumCb );
ros::Subscriber<std_msgs::Empty> funnelFlapSub("toggle_funnel_flap", &funnelFlapCb );

void setup() {

  // VACUUM HOSE EXTENDER
  pinMode(upperPin, INPUT);
  pinMode(lowerPin, INPUT);

  pinMode(hoseStepPin, OUTPUT);
  pinMode(hoseDirPin, OUTPUT);

  // VACUUM CONTROLLER
  pinMode(vacuumPin, OUTPUT);
  digitalWrite(vacuumPin, LOW);
  servo.attach(9);

  // BEAKER CAROUSEL CONTROLLER
  pinMode(beakerStepPin, OUTPUT);
  pinMode(beakerDirPin, OUTPUT);

  // Setup ROS Publisher and Subscribers
  nh.initNode();
  nh.subscribe(hoseSub);
  nh.subscribe(sampleSystemSub);
  nh.subscribe(aggitationSub);
  nh.subscribe(vacuumSub);
  nh.subscribe(funnelFlapSub);
  nh.advertise(logger); 
}

void loop() {
  nh.spinOnce();
  delay(1);
}
