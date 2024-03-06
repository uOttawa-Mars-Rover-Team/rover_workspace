
//Everything before setup() and setup()

//We import the needed libraries namely:
//- AccelStepper (used for stepper control)
//- MultiStepper (used for simultaneous stepper control)
//- ezButton (takes care of button debouncing)
//- JrkG2 (used for linear actuator control)
#include <AccelStepper.h>
#include <MultiStepper.h>
#include <ezButton.h>
#include <JrkG2.h>
#include <SPI.h>
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
MultiStepper wristEE;

//We declare objects for the linear actuator drivers
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

////// Constant/Variable Declaration //////

/* SPI commands */
#define AMT22_NOP       0x00
#define AMT22_RESET     0x60
#define AMT22_ZERO      0x70

/* Define special ascii characters */
#define NEWLINE         0x0A
#define TAB             0x09

//SPI encoder resolution
#define RES12           12

//SPI pins
#define SPI_MISO        50
#define SPI_MOSI        51
#define SPI_SCLK        52

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
  float         current;    
  float         desired;
  unsigned long dir_change; //time since dir has changed
  const int     MAX_RANGE;  //max range allowed by motor/workspace
  int           ENC;        //encoder pin 1 if applicable
  uint16_t      attemps;    //check sum for SPI encoder data
};


//Create the motor objects
Motor tw = {0, 0, 2000, 0.0, 0.0, millis(), 2500,     31, 0};
Motor l1 = {0, 0, -1,   0.0, 0.0, millis(), -1,       33, 0};    
Motor l2 = {0, 0, -1,   0.0, 0.0, millis(), -1,       35, 0};
Motor wp = {0, 0, 2000, 0.0, 0.0, millis(), 250000,   37, 0};
Motor wr = {0, 0, 2000, 0.0, 0.0, millis(), 1750000,  -1, 0};
Motor ee = {0, 0, 2000, 0.0, 0.0, millis(), 861,      -1, 0};
//Note: added extra 2 zeroes for pitch and roll max ranges

//Pack into an array for iterability
Motor motor[] = {tw, l1, l2, wp, wr, ee};

//Stop variables for steppers & limit switch purposes
int EEStopClose   = 0;
int EEStopOpen    = 0;
int wristStopUp   = 0;
int wristStopDown = 0;

//Keeps track of tower encoder
int section = 0;

//Tmp uint16_t var to store encoder data
uint16_t tmpEncPos = 0;
uint16_t tmpEncPosPrev = 0;

//Time in ms for:
int ls_delay    = 20; //limit switch debounce time
int enc_delay   = 50; //how often to check encoder data and move motors
int dashb_delay = 100;//how often to publish via serial encoder data, etc...

//Timer for encoder & dashboard updates
unsigned long encoder_t  = millis();//timer for encoder updates
unsigned long dashb_t    = millis();//timer for sending data to dashboard

//Received serial command variables
const int INPUT_SIZE = 50;
char input[INPUT_SIZE + 1];
char* tmp;     //stores chars as we tokenize
char* mode = "M";    //"M" = manual, "I" = IK mode


void setup() {

  //Set the modes for the SPI IO
  pinMode(SPI_SCLK, OUTPUT);
  pinMode(SPI_MOSI, OUTPUT);
  pinMode(SPI_MISO, INPUT);
  pinMode(motor[TW].ENC, OUTPUT);
  pinMode(motor[L1].ENC, OUTPUT);
  pinMode(motor[L2].ENC, OUTPUT);
  pinMode(motor[WP].ENC, OUTPUT);
  
  //We start the serial comms at 115200 bps
  Serial.begin(115200);

  //start I2C comms
  Wire.begin();
  
  //Get the CS line high which is the default inactive state
  digitalWrite(motor[TW].ENC, HIGH);
  digitalWrite(motor[L1].ENC, HIGH);
  digitalWrite(motor[L2].ENC, HIGH);
  digitalWrite(motor[WP].ENC, HIGH);

  //we set the debounce time of the limitSwitches, that is the amount of time
  //the program is going to wait until it accepts another input from the switches
  LS1.setDebounceTime(ls_delay); //set debounce time to 50 milliseconds
  LS2.setDebounceTime(ls_delay);
  LS3.setDebounceTime(ls_delay);
  LS4.setDebounceTime(ls_delay);

  //we configure the default speed for each stepper
  //TODO: verify each of these speeds in a separate test and then modify these values
  //High acceleration values seem to work best (less struggling sounds)
  wristLeft.  setAcceleration(2000.0);
  wristRight. setAcceleration(2000.0);
  tower.      setAcceleration(2000.0);
  endEffector.setAcceleration(2000.0);

  //we add the wristSteppers to the multiStepper object
  //Then give them to MultiStepper to manage
  wristEE.addStepper(wristRight);
  wristEE.addStepper(wristLeft);

  //set the clockrate. Uno clock rate is 16Mhz, divider of 32 gives 500 kHz.
  //500 kHz is a good speed for our test environment
  //SPI.setClockDivider(SPI_CLOCK_DIV2);   // 8 MHz
  //SPI.setClockDivider(SPI_CLOCK_DIV4);   // 4 MHz
  //SPI.setClockDivider(SPI_CLOCK_DIV8);   // 2 MHz
  //SPI.setClockDivider(SPI_CLOCK_DIV16);  // 1 MHz
  SPI.setClockDivider(SPI_CLOCK_DIV32);    // 500 kHz
  //SPI.setClockDivider(SPI_CLOCK_DIV64);  // 250 kHz
  //SPI.setClockDivider(SPI_CLOCK_DIV128); // 125 kHz
  
  //start SPI bus
  SPI.begin();

  //Update current positions on startup
  for (int i = TW ; i < LAST ; i++) {
    tmpEncPos = getPositionSPI(motor[i].ENC, RES12);
    if (tmpEncPos != 0xFFFF) 
      motor[i].current = (float)tmpEncPos*0.00153398078789;
  }

}//end of setup()
