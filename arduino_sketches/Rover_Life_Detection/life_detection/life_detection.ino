
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
bool collectWeather = false;


void hoseCb(std_msgs::String& hose_cmd) {
    if (hose_cmd.data == "StartMoveDown") {
        nh.loginfo("Moving hose down....");
        dir = 1;
        digitalWrite(hoseDirPin, HIGH);
    } else if (hose_cmd.data == "StopMoveDown") {
        dir = 0;
        nh.loginfo("Stopped Down Movement");
        return;
    } else if (hose_cmd.data == "StartMoveUp") {
        nh.loginfo("Moving hose up....");
        dir = -1;
        digitalWrite(hoseDirPin, LOW);        
    } else if (hose_cmd.data == "StopMoveUp") {
        dir = 0;
        nh.loginfo("Stopped Up Movement");
        return;
    }
    while (!checkLimits){
        nh.spinOnce();
        /* publish distance data */
        if (dir == 0){
          break;
        }
        for (int x = 0; x < stepsPerRevolution; x++){
          if (!checkLimits()) {
              digitalWrite(hoseStepPin, HIGH);
              delayMicroseconds(2000);
              digitalWrite(hoseStepPin, LOW);
              delayMicroseconds(2000);
          } else {
              backOff();
              break;
          }
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
    for (pos = 0; pos <= 90; pos += 1) { // goes from 0 degrees to 90 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = true;
    nh.loginfo("funnelFlapCb: Done");
  }else{
    nh.loginfo("Closing funnel flap....");
    for (pos = 90; pos > 0; pos -= 1) { // goes from 0 degrees to 90 degrees
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
void sampleSystemCb( const std_msgs::String& sample_sys_cmd){
  if (sample_sys_cmd.data == "StartCWRotate"){
    moveBeaker(true);
  }else if (sample_sys_cmd.data == "StartCCWRotate"){
    moveBeaker(false);
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

bool checkStatus(String message){
        if (message == "StartAgitation") {
            return true;
        } else {
            return false; 
        }
}

void aggitationCb( const std_msgs::String& aggitationCMD){
    if (aggitationCMD.data == "StartAgitation") {
        while (checkStatus(aggitationCMD.data)){
            nh.spinOnce();
            
            digitalWrite(beakerDirPin, HIGH);

            digitalWrite(beakerStepPin, HIGH);
            delayMicroseconds(4000); 
            digitalWrite(beakerDirPin, LOW);

            digitalWrite(beakerStepPin, HIGH);
            delayMicroseconds(4000);
            digitalWrite(beakerStepPin, LOW);
            delayMicroseconds(4000);
            delay(10); // Wait a second
        }
    }
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
void moveBeaker(bool reverse){
  int steps = round(degrees_between_beaker*gear_ratio*stepsPerRevolution);
  
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


void collectWeatherCb( const std_msgs::String& WeatherCollectionCMD){
  if (collectWeather){
    collectWeather = false;
    return;
  } else {
    bool collectWeather = true;
    while (collectWeather){
      nh.spinOnce();
      /*float UV = 
      float humidity = 
      float temp = 
      float windSpeed = 
      float pressure = 
      String data = UV + ";" + humidity + ";" + temp + ";" + windSpeed + ";" + pressure
      publish data */
    }
  }

}

//=================================================================================================

//Publishing topics
std_msgs::String str_msg;
ros::Publisher TempLogger("life_detection_logger", &str_msg);

//Subscribing topics hose_cmd
ros::Subscriber<std_msgs::String> hoseSub("VacHoseCMD", &hoseCb );
ros::Subscriber<std_msgs::UInt8> sampleSystemSub("BeakerCMD", &sampleSystemCb );
ros::Subscriber<std_msgs::String> aggitationSub("AgitateCMD", &aggitationCb );
ros::Subscriber<std_msgs::Empty> vacuumSub("VacMotorCMD", &vacuumCb );
ros::Subscriber<std_msgs::Empty> funnelFlapSub("FunnelFlapCMD", &funnelFlapCb );
ros::Subscriber<std_msgs::Empty> weatherCollectionSub("WeatherCollectionCMD", &collectWeatherCb );


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
  nh.subscribe(weatherCollectionSub);
  nh.advertise(TempLogger); 
}

void loop() {
  nh.spinOnce();
  delay(1);
}
