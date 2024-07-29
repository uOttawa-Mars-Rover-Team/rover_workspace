
//Everything before setup()

//We import the needed libraries namely:
//- AccelStepper (used for stepper control)
//- MultiStepper (used for simultaneous stepper control)
//- ezButton (takes care of button debouncing)
//- JrkG2 (used for linear actuator control)
#include <AccelStepper.h>
//#include <MultiStepper.h>
#include <ezButton.h>
#include <JrkG2.h>
#include <math.h>

////// Object Declaration //////

//We initialize the Wrist Limit switch objects
ezButton LS1(43);
ezButton LS2(44);
ezButton LS3(45);
ezButton LS4(46);

//We declare the steppers
AccelStepper wristRight (AccelStepper::DRIVER, 11,  10); //step, direction
AccelStepper wristLeft  (AccelStepper::DRIVER, 9,   8);
AccelStepper tower      (AccelStepper::DRIVER, 7,   6);
AccelStepper endEffector(AccelStepper::DRIVER, 13,  12);

//We set up the multistepper
//MultiStepper wristEE;

//We declare objects for the linear actuator drivers
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

////// Constant/Variable Declaration //////

//Enumeration for motors
enum M_ID {
  TW,
  L1,
  L2,
  WP,
  WR,
  EE,
  LAST//not a motor
};

//Define what variables to use for our motor
struct Motor {
  int           direction;
  int           speed;
  int           acceleration;
  int           currentCount;
  float         current;    
  float         desired;
  unsigned long dirChange; //time since dir has changed
  const int     MAX_RANGE;  //max range allowed by motor/workspace
  int           ENC_A;      //encoder pin 1 if applicable
  int           ENC_B;      //encoder pin 2 if applicable
  unsigned long trig_delay; //for mainly la encoder
};

//Create the motor objects
//         dir  speed  accel   ccnt   curr    des   dir_c    MAX_R     E_A   E_B  t_delay
Motor tw = {0,    0,    3000,   0,    0.0,    0.0, millis(), 2500,     18,   39,  millis()};
Motor l1 = {0,    0,    -1,     0,    0.0,    0.0, millis(), -1,        2,   -1,  millis()};    
Motor l2 = {0,    0,    -1,     0,    0.0,    0.0, millis(), -1,        3,   -1,  millis()};
Motor wp = {0,    0,    30000,  0,    0.0,    0.0, millis(), 25000,   19,   41,  millis()};
Motor wr = {0,    0,    30000,  0,    0.0,    0.0, millis(), 175000,  -1,   -1,  millis()};
Motor ee = {0,    0,    10000,   0,    0.0,    0.0, millis(), 8610,     -1,   -1,  millis()};
//Note: added extra 1 zeroes for pitch and roll max ranges

//Pack into an array for iterability
Motor motor[] = {tw, l1, l2, wp, wr, ee};

//Stop variables for steppers & limit switch purposes
int EEStopClose   = 0;
int EEStopOpen    = 0;
int wristStopUp   = 0;
int wristStopDown = 0;

//Time in ms for:
int ls_delay    = 20; //limit switch debounce time
int enc_delay   = 50; //how often to check encoder data and move motors
int dashb_delay = 100;//how often to publish via serial encoder data, etc...

//Timer for encoder & dashboard updates
unsigned long encoder_t  = millis();//timer for encoder updates
unsigned long dashb_t    = millis();//timer for sending data to dashboard

//Received serial command variables
const int INPUT_SIZE = 130;
char input[INPUT_SIZE + 1];
char* tmp;     //stores chars as we tokenize
char* mode = "I";    //"M" = manual, "I" = IK mode

//Everything setup related

void setup() {
  //We start the serial comms at 115200 bps
  Serial.begin(115200);

  //start I2C comms
  Wire.begin();
  

  //we set the debounce time of the limitSwitches, that is the amount of time
  //the program is going to wait until it accepts another input from the switches
  LS1.setDebounceTime(ls_delay); //set debounce time to 50 milliseconds
  LS2.setDebounceTime(ls_delay);
  LS3.setDebounceTime(ls_delay);
  LS4.setDebounceTime(ls_delay);

  //we configure the default speed for each stepper
  //TODO: verify each of these speeds in a separate test and then modify these values
  //High acceleration values seem to work best (less struggling sounds)
  wristLeft.  setAcceleration(motor[WP].acceleration);
  wristRight. setAcceleration(motor[WP].acceleration);
  tower.      setAcceleration(motor[TW].acceleration);
  endEffector.setAcceleration(motor[EE].acceleration);

  //we add the wristSteppers to the multiStepper object
  //Then give them to MultiStepper to manage
  //wristEE.addStepper(wristRight);
  //wristEE.addStepper(wristLeft);

  pinMode(motor[TW].ENC_A, INPUT_PULLUP);
  pinMode(motor[TW].ENC_B, INPUT);
  attachInterrupt(digitalPinToInterrupt(motor[TW].ENC_A), towerCounter, RISING);

  pinMode(motor[WP].ENC_A, INPUT_PULLUP);
  pinMode(motor[WP].ENC_B, INPUT);
  attachInterrupt(digitalPinToInterrupt(motor[WP].ENC_A), pitchCounter, RISING);

  //set up the optical encoder pins with pullup resistors
  pinMode(motor[L1].ENC_A, INPUT_PULLUP);
  pinMode(motor[L2].ENC_A, INPUT_PULLUP);

  //set up interrupt pins for the LA encoders
  attachInterrupt(digitalPinToInterrupt(motor[L1].ENC_A), counter_LA1, RISING);
  attachInterrupt(digitalPinToInterrupt(motor[L2].ENC_A), counter_LA2, RISING);

}//end of setup()
