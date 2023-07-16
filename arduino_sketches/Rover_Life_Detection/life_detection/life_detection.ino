#include <ros.h>
#include <std_msgs/Empty.h>
#include <std_msgs/String.h>
#include <std_msgs/UInt8.h>
#include <std_msgs/Float32.h>
#include <Servo.h>
#include <HCSR04.h>
#include <Adafruit_SI1145.h>
#include <Adafruit_BME280.h>
#include <ezButton.h>


ros::NodeHandle  nh;

//Publishing topics

//=================================================================================================
// VACUUM HOSE EXTENDER 

const int hoseDirPin = 10;
const int hoseStepPin = 11;
const int stepsPerRevolution = 25;
const int trig = 2;
const int echo = 4;
ezButton lowerLimitSwitch(52);
ezButton upperLimitSwitch(53);
int dir = 0;
HCSR04 hc(trig, echo);

std_msgs::Float32 flo_msg;
ros::Publisher hoseDistance("hose_distance", &flo_msg);


void hoseCb(std_msgs::UInt8& hose_cmd) {
  if (hose_cmd.data == 1) {
    digitalWrite(hoseDirPin, false);
    nh.loginfo("Moving hose down....");
    dir = 1;
    nh.spinOnce();
  } else if (hose_cmd.data == 4) {
    dir = 0;
    nh.loginfo("Stopped Down Movement");
    return;
  } else if (hose_cmd.data == 2) {
    digitalWrite(hoseDirPin, true);  
    nh.loginfo("Moving hose up....");
    dir = -1;
    nh.spinOnce();
  } else if (hose_cmd.data == 3) {
    dir = 0;
    nh.loginfo("Stopped Up Movement");
    return;
  }
  float avgDistance = 0;
  for (int i = 0; i<=5;i++){
    float distance = hc.dist();
    avgDistance = avgDistance + distance;
  }
  avgDistance = avgDistance/6;
  flo_msg.data = avgDistance;
  hoseDistance.publish(&flo_msg);
  for (int x = 0; x < stepsPerRevolution; x++){
    if (checkLimits()) {
      backOff();
      break;
    } else {
      digitalWrite(hoseStepPin, HIGH);
      delayMicroseconds(2000);
      digitalWrite(hoseStepPin, LOW);
      delayMicroseconds(2000);
    }   
  }
}


bool checkLimits(){
  int lsUpperLimit = upperLimitSwitch.getState();
  int lsLowerLimit = lowerLimitSwitch.getState();
  if(lsUpperLimit == LOW) {
    nh.logwarn("Upper Limit hit");
  }
  if(lsLowerLimit  == LOW) {
    nh.logwarn("Lower Limit hit");
  }

  if (!lsUpperLimit || !lsLowerLimit){
    return true;
  } else {
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
  if (dir == 1){
     digitalWrite(hoseDirPin, true);
  }else if (dir == -1){
     digitalWrite(hoseDirPin, false);
  }else{
    nh.logerror("check limit switches");
    dir = 0;
    return;
  }
  delay(1000);
  for(int x = 0; x < 400; x++)
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

int forwardVacuumState = LOW;
int backwardVacuumState = LOW;
const int vacuumPin = 3;
const int forwardEnPin = 20;
const int backwardEnPin = 21;
const int forwardPWMPin = 7;
const int backwardPWMPin = 6;

/*
 * Function:  vacuumCb 
 * --------------------
 * callback function that toggles the vacuum relay.
 */
void vacuumCb( const std_msgs::UInt8& toggle_vacuum){
  if (toggle_vacuum.data == 1) {
    digitalWrite(backwardEnPin, LOW);
    digitalWrite(forwardEnPin, HIGH);
    if (forwardVacuumState == LOW) {
      nh.loginfo("Turning on vacuum....");
      for (int i = 0; i <= 255; i += 1){
        analogWrite(forwardPWMPin, i);
        delay(20);
      }
      nh.loginfo("Vacuum is at full sucking power");
      forwardVacuumState = HIGH;
    } else {
      nh.loginfo("Turning off vacuum....");
      for (int i = 255; i >= 0; i -= 1){
        analogWrite(forwardPWMPin, i);
        delay(20);
      }
      nh.loginfo("Vacuum is off");
      forwardVacuumState = LOW;
      digitalWrite(forwardEnPin, LOW);
    }
  } else if (toggle_vacuum.data == 2) {
    digitalWrite(forwardEnPin, LOW);
    digitalWrite(backwardEnPin, HIGH);
    if (backwardVacuumState == LOW) {
      nh.loginfo("Turning on vacuum....");
      for (int i = 0; i <= 255; i += 1){
        analogWrite(backwardPWMPin, i);
        delay(20);
      }
      nh.loginfo("Vacuum is at full sucking power");
      backwardVacuumState = HIGH;
    } else {
      nh.loginfo("Turning off vacuum....");
      for (int i = 255; i >= 0; i -= 1){
        analogWrite(backwardPWMPin, i);
        delay(20);
      }
      nh.loginfo("Vacuum is off");
      backwardVacuumState = LOW;
      digitalWrite(backwardEnPin, LOW);
    }
  }
}

// FUNNEL FLAP CONTROLLER
/*
 * Function:  funnelFlapCb 
 * --------------------
 * callback function that toggles the position of the funnel flap
 */

Servo servo;
int pos = 0;
bool flapIsOpen = false;

void funnelFlapCb( const std_msgs::Empty& toggle_funnel_flap){
  if (!flapIsOpen){
    nh.loginfo("Opening funnel flap....");
    for (pos = 0; pos <= 90; pos += 1) { // goes from 0 degrees to 90 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = true;
    nh.loginfo("funnel flap opened");
  }else{
    nh.loginfo("Closing funnel flap....");
    for (pos = 90; pos > 0; pos -= 1) { // goes from 0 degrees to 90 degrees
      // in steps of 1 degree
      servo.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
    flapIsOpen = false;
    nh.loginfo("funnel flap closed");
  }
}

//=================================================================================================
// BEAKER SAMPLE SYSTEM CONTROLLER

const float degrees_between_beaker = 25.00/360;
const float gear_ratio = 309/14;
const int beakerDirPin = 12;
const int beakerStepPin = 13;

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
  if (sample_sys_cmd.data == 1){
    moveBeaker(true);
  }else if (sample_sys_cmd.data == 2){
    moveBeaker(false);
  }
}

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

/*
 * Function:  aggitationCb 
 * --------------------
 * callback function that shakes the samples
 *
 *  aggitation_timer: UInt8 ROS topic that passes the amount of time 
 *                    (in seconds) to aggitate the samples for.
 */

// bool checkStatus(String message){
//         if (message == 1) {
//             return true;
//         } else {
//             return false; 
//         }
// }
bool checkStatus(int aggitationCMD) {
  nh.spinOnce();
  if (aggitationCMD == 1){
    nh.loginfo("Aggitation Started");
    return true;
  }
  else {
    nh.loginfo("Aggitation Stopped");
    return false;
  }
}


void aggitationCb( const std_msgs::UInt8& aggitationCMD){
        while (checkStatus(aggitationCMD.data)) {
            
            digitalWrite(beakerDirPin, HIGH);

            digitalWrite(beakerStepPin, HIGH);
            delayMicroseconds(4000);
            digitalWrite(beakerStepPin, LOW);
            delayMicroseconds(4000);

            digitalWrite(beakerDirPin, LOW);

            digitalWrite(beakerStepPin, HIGH);
            delayMicroseconds(4000);
            digitalWrite(beakerStepPin, LOW);
            delayMicroseconds(4000);
            delay(10); // Wait a second
        }
}

bool collectWeather = false;
Adafruit_SI1145 uv = Adafruit_SI1145();
Adafruit_BME280 bme;
std_msgs::String str_msg;
ros::Publisher weatherLogger("weather_logger", &str_msg);


void collectWeatherCb( const std_msgs::String& WeatherCollectionCMD){
  if (collectWeather == true){
    collectWeather = false;
    nh.loginfo("Stopped weather collection");
    return;
  } else {
    nh.loginfo("Collecting Weather...");
    collectWeather = true;
    while (collectWeather){
      nh.spinOnce();
      float UV = uv.readUV();
      UV /= 100.0;  
      float humidity = bme.readHumidity();
      float temp = bme.readTemperature();
      float windSpeed = 5.0;
      float pressure = bme.readPressure();
      String data1 = String(String(UV) + ";" + String(humidity) + ";" + String(temp) + ";" + String(windSpeed) + ";" + String(pressure));
      int len = data1.length() + 1;
      char data[len];
      data1.toCharArray(data, len);
      str_msg.data = data;
      weatherLogger.publish(&str_msg);
      delay(5000);
    }
  }

}

//=================================================================================================

//Subscribing topics hose_cmd
ros::Subscriber<std_msgs::UInt8> hoseSub("VacHoseCMD", &hoseCb );
ros::Subscriber<std_msgs::UInt8> sampleSystemSub("BeakerCMD", &sampleSystemCb );
ros::Subscriber<std_msgs::UInt8> aggitationSub("AgitateCMD", &aggitationCb );
ros::Subscriber<std_msgs::UInt8> vacuumSub("VacMotorCMD", &vacuumCb );
ros::Subscriber<std_msgs::Empty> funnelFlapSub("FunnelFlapCMD", &funnelFlapCb );
ros::Subscriber<std_msgs::Empty> weatherCollectionSub("WeatherCollectionCMD", &collectWeatherCb );


void setup() {

  // VACUUM HOSE EXTENDER
  pinMode(hoseStepPin, OUTPUT);
  pinMode(hoseDirPin, OUTPUT);

  // VACUUM CONTROLLER
  pinMode(vacuumPin, OUTPUT);
  digitalWrite(vacuumPin, LOW);
  servo.attach(8);
  servo.write(0);

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
  nh.advertise(weatherLogger); 
  nh.advertise(hoseDistance); 

  bme.begin();
  uv.begin();
}

void loop() {
  upperLimitSwitch.loop();
  lowerLimitSwitch.loop();
  nh.spinOnce();
  delay(1);
}
