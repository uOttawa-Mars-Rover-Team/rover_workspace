
//Everything before setup()

//We import the needed libraries namely:
//- AccelStepper (used for stepper control)
//- MultiStepper (used for simultaneous stepper control)
//- ezButton (takes care of button debouncing)
//- JrkG2 (used for linear actuator control)
// Include the SPI library for the arduino boards
#include <AccelStepper.h>
//#include <MultiStepper.h>
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
AccelStepper tower        (AccelStepper::DRIVER, 6,   7);  //step, direction
AccelStepper wristPitch   (AccelStepper::DRIVER, 8,   9);
AccelStepper wristRoll    (AccelStepper::DRIVER, 10,  11); 
AccelStepper endEffector  (AccelStepper::DRIVER, 12,  13);

//We set up the multistepper
//MultiStepper wristEE;

//We declare objects for the linear actuator drivers
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

////// Constant/Variable Declaration //////

// Serial rates for UART
#define BAUDRATE        500000

// SPI commands */
#define AMT22_NOP       0x00
#define AMT22_RESET     0x60
#define AMT22_ZERO      0x70

// Define special ascii characters
#define NEWLINE         0x0A
#define TAB             0x09

// We will use these define macros so we can write code once compatible with 12 or 14 bit encoders
#define RES12           12

// SPI pins
#define SPI_MOSI        51
#define SPI_MISO        50
#define SPI_SCLK        52

//create a 16 bit variable to hold the encoders position
int encoderPosition;
//let's also create a variable where we can count how many times we've tried to obtain the position in case there are errors
uint8_t attempts;

#define verbose         false
#define graph           true

//Stop variables for steppers & limit switch purposes
int EEStopClose   = 0;
int EEStopOpen    = 0;
int wristStopUp   = 0;
int wristStopDown = 0;

//Time in ms for:
int ls_delay    = 20; //limit switch debounce time (ms)
int enc_delay   = 50;  //how often to update encoder data
int motor_delay = 50; //how often to move motors
int dashb_delay = 200;//how often to publish via serial encoder data, etc...
int fault_delay = 500;//how often to check for faults on all drivers

//Timer for encoder & dashboard updates
unsigned long encoder_t  = millis();//timer for encoder updates
unsigned long motor_t    = millis();//timer for encoder updates
unsigned long dashb_t    = millis();//timer for sending data to dashboard
unsigned long fault_t    = millis();//timer for sending fault data

//Received serial command variables
const int INPUT_SIZE = 130;
char input[INPUT_SIZE + 1];
char* tmp;     //stores chars as we tokenize
char* mode = "M";    //"M" = manual, "I" = IK mode

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

const char* motor_names[] = {"TW", "L1", "L2","WP", "WR", "EE"};

//Define what variables to use for our motor
struct Motor {
  int           direction;
  int           speed;//motor move speedd
  float         velocity;//calculated speed w/ encoders
  long          acceleration;
  int           enc_status;   
  int           enc_turns;    
  long          enc_count;   
  float         currentPos;    
  float         desiredPos;
  int           sign;
  unsigned long dirChange;    //time since dir has changed
  unsigned long trig_delay;   //for mainly la encoder
  long          MAX_RANGE;    //max range allowed by motor/workspace
  int           ENC_PIN;      //enable pin for encoder, active low 
  int           BOOT_PIN;     //used to reboot the stepper drivers
  int           FAULT_PIN;    //to manage faults for all drivers
};

//Create the motor objects
//         dir  speed  vel   accel   enc_status  enc_turns  enc_count   curr    des   sign  dir_c      t_delay     MAX_R    ENC    BOOT_P   FAULT_P 
Motor tw = {0,    0,    0,   3000,     0,         0,          0,        0.0,    0.0,   -1, millis(),   millis(),   1000000, 56,      17,     68};
Motor l1 = {0,    0,    0,     -1,     0,         0,          0,        0.0,    0.0,   -1, millis(),   millis(),   -1,      63,     -1,      30};    
Motor l2 = {0,    0,    0,     -1,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   -1,      64,     -1,      31};
Motor wp = {0,    0,    0,  30000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, 57,      16,     62};
Motor wr = {0,    0,    0,  30000,     0,         0,          0,        0.0,    0.0,   -1, millis(),   millis(),   1000000, -1,      4,      55};
Motor ee = {0,    0,    0,  10000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, -1,      5,      54};
//Note: added extra 1 zeroes for pitch and roll max ranges
// l1 encoder pin is for the shoulder encoder and l2 encoder pin is for the elbow encoder

//Pack into an array for iterability
Motor motor[] = {tw, l1, l2, wp, wr, ee};

//Define what variables to use for our LED
struct LED {
  int           R_PIN;    //red
  int           G_PIN;    //green
  int           B_PIN;    //blue
};

//Create the LED object(s)
//         r_pin   g_pin   b_pin  
LED led = {58,      59,      60};

//Laser 
int LASER_PIN = 29;


//Everything setup related below

void setup() {
  //We start the serial comms at 115200 bps
  Serial.begin(BAUDRATE);

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
  tower.      setAcceleration(motor[TW].acceleration);
  wristPitch. setAcceleration(motor[WP].acceleration);
  wristRoll.  setAcceleration(motor[WR].acceleration);
  endEffector.setAcceleration(motor[EE].acceleration);

  //Set the modes for the SPI IO
  pinMode(SPI_SCLK, OUTPUT);
  pinMode(SPI_MOSI, OUTPUT);
  pinMode(SPI_MISO, INPUT);

  //Set up encoder pins for SPI
  pinMode(motor[TW].ENC_PIN, OUTPUT);
  digitalWrite(motor[TW].ENC_PIN, HIGH);
  pinMode(motor[L1].ENC_PIN, OUTPUT);
  digitalWrite(motor[L1].ENC_PIN, HIGH);
  pinMode(motor[L2].ENC_PIN, OUTPUT);
  digitalWrite(motor[L2].ENC_PIN, HIGH);
  pinMode(motor[WP].ENC_PIN, OUTPUT);
  digitalWrite(motor[WP].ENC_PIN, HIGH);

  //Set the LED pins to output
  pinMode(led.R_PIN, OUTPUT);
  pinMode(led.G_PIN, OUTPUT);
  pinMode(led.B_PIN, OUTPUT);
  //Set the LED off
  writeLED(255,255,255);

  //Turn laser on
  pinMode(LASER_PIN, OUTPUT);
  digitalWrite(LASER_PIN, HIGH);

  //Set high to dip switch pins
  pinMode(motor[TW].BOOT_PIN, OUTPUT);
  digitalWrite(motor[TW].BOOT_PIN, HIGH);
  pinMode(motor[WP].BOOT_PIN, OUTPUT);
  digitalWrite(motor[WP].BOOT_PIN, HIGH);
  pinMode(motor[WR].BOOT_PIN, OUTPUT);
  digitalWrite(motor[WR].BOOT_PIN, HIGH);
  pinMode(motor[EE].BOOT_PIN, OUTPUT);
  digitalWrite(motor[EE].BOOT_PIN, HIGH);
  
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

}//end of setup()
