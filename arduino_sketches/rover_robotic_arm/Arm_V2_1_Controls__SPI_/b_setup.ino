//We import the needed libraries namely:
//- AccelStepper (used for stepper control)
//- JrkG2 (used for linear actuator control)
//- SPI (used for encoder comms)
//- 
// Include the SPI library for the arduino boards
#include <AccelStepper.h>
#include <JrkG2.h>
#include <SPI.h>
#include <TimerOne.h>
#include <Servo.h>


////// Object Declaration //////

//We declare the steppers1
AccelStepper tower        (AccelStepper::DRIVER, 55,  54);  //step, direction
AccelStepper wristPitch   (AccelStepper::DRIVER, 4,   5);
AccelStepper wristRoll    (AccelStepper::DRIVER, 8,   9); 
AccelStepper endEffector  (AccelStepper::DRIVER, 12,  13);

//We set up the multistepper
//MultiStepper wristEE;

Servo cameraServo;
//We declare objects for the linear actuator drivers
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

////// Constant/Variable Declaration //////

// Serial rates for UART
#define BAUDRATE        1000000

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

#define SERVO_PIN 6

//#define verbose true

//create a 16 bit variable to hold the encoders position
int encoderPosition;
//let's also create a variable where we can count how many times we've tried to obtain the position in case there are errors
uint8_t attempts;

int servoPos = 90;
int stepSize = 5;

bool verbose = false;
bool emergency_stop_en = false;
bool wrist_angle_abs = false;
bool stepper_safety_en = false;
bool commandFlag = false;
bool svMoving = false;  
bool svUp = false;
bool svDown = false;

//Stop variables for steppers & limit switch purposes
int EEStopClose   = 0;
int EEStopOpen    = 0;
int wristStopUp   = 0;
int wristStopDown = 0;

//Time in ms for:
long enc_delay   = 50;  //how often to update encoder data
long motor_delay = 25; //how often to move motors
long dashb_delay = 100;//how often to publish via serial encoder data, etc...
long servo_delay = 500;
//long fault_delay = 100;//how often to check for faults on all drivers

//Timer for encoder & dashboard updates
unsigned long encoder_t  = millis();//timer for encoder updates
unsigned long motor_t    = millis();//timer for encoder updates
unsigned long dashb_t    = millis();//timer for sending data to dashboard
unsigned long fault_t    = millis();//timer for sending fault data
unsigned long camservo_t    = millis();//timer for servo movement (camera)

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

//Define what variables to use for our motor
struct Motor {
  int            direction;
  int            speed; //motor move speed
  float          velocity; //calculated speed w/ encoders
  long           acceleration;
  int            enc_status;   
  int            enc_turns;    
  long           enc_count;   
  volatile float currentPos;    
  float          desiredPos;
  int            sign;
  unsigned long  dirChange;    //time since dir has changed
  unsigned long  trig_delay;   //for mainly la encoder
  long           MAX_RANGE;    //max range allowed by motor/workspace
  int            ENC_PIN;      //enable pin for encoder, active low 
  int            BOOT_PIN;     //used to reboot the stepper drivers
  int            FAULT_PIN;    //to manage faults for all drivers
  int            MAX_SPEED;    //to manage faults for all drivers
  float          MAX_POS_POSITION; //Maximum forward position the motor can approach
  float          MAX_NEG_POSITION; //Maximum backward position the motor can approach
};

//Create the motor objects
//         dir  speed  vel   accel   enc_status  enc_turns  enc_count   curr    des   sign  dir_c      t_delay     MAX_R    ENC    BOOT_P   FAULT_P  MAX_SPEED    MAX_POS_POSITION    MAX_NEG_POSTION
Motor tw = {0,    0,    0,   5000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, 66,      16,     17,      1000,         90.00,               -90.00    };
Motor l1 = {0,    0,    0,     -1,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   -1,      68,     -1,      58,      600,             -1,                   -1    };    
Motor l2 = {0,    0,    0,     -1,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   -1,      69,     -1,      59,      600,             -1,                   -1    };
Motor wp = {0,    0,    0,  10000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, 67,      3,       2,      1000,         95.00,               -57.00    };
Motor wr = {0,    0,    0,  20000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, -1,      7,       6,      1000,            -1,                   -1    };
Motor ee = {0,    0,    0,  20000,     0,         0,          0,        0.0,    0.0,    1, millis(),   millis(),   1000000, -1,      11,     10,      1000,            -1,                   -1    };
//Note: added extra 1 zeroes for pitch and roll max ranges
// l1 encoder pin is for the shoulder encoder and l2 encoder pin is for the elbow encoder

//Pack into an array for iterability
Motor motor[] = {tw, l1, l2, wp, wr, ee};

byte size = 0;


//Everything setup related below

void setup() {
  //We start the serial comms at 115200 bps
  Serial.begin(BAUDRATE);

  //start I2C comms
  Wire.begin();
  
  //set the clockrate. Uno clock rate is 16Mhz, divider of 32 gives 500 kHz.
  //500 kHz is a good speed for our test environment
  SPI.setClockDivider(SPI_CLOCK_DIV4);   // 4 MHz
  
  //start SPI bus
  SPI.begin();

  cameraServo.attach(SERVO_PIN);

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

  //Set high to dip switch pins
  pinMode(motor[TW].BOOT_PIN, OUTPUT);
  digitalWrite(motor[TW].BOOT_PIN, HIGH);
  pinMode(motor[WP].BOOT_PIN, OUTPUT);
  digitalWrite(motor[WP].BOOT_PIN, HIGH);
  pinMode(motor[WR].BOOT_PIN, OUTPUT);
  digitalWrite(motor[WR].BOOT_PIN, HIGH);
  pinMode(motor[EE].BOOT_PIN, OUTPUT);
  digitalWrite(motor[EE].BOOT_PIN, HIGH);

  // Isr timer for the run() function
  Timer1.initialize(1200); // Every 250us. This has been tested and is the minimum frequency that works without vibrations.
  Timer1.attachInterrupt(timerIsr);
}//end of setup()