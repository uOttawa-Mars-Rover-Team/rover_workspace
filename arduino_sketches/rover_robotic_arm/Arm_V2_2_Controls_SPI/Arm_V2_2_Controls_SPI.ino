#include <AccelStepper.h> //Used for non-blocking stepper control
#include <JrkG2.h> //Vendor provided library for linear actuator drivers
#include <SPI.h> //Communication with encoders
#include <TimerThree.h> //Moving steppers at reliable intervals
#include <Servo.h> //Moving camera servo joints

//Motor Constants
enum Joint_ID {
  TW,
  WP,
  WR,
  EE,
  SL,
  EL,
  JOINT_NUM//not a joints
};

//Group all common stepper data into this struct
struct StepperConfigs{
  int STEP_PIN;
  int DIR_PIN;
  int BOOT_PIN;
  int ACCELERATION;
};

#define MAX_STEPPER_RANGE 1000000
#define NUMBER_OF_STEPPERS 4

// Defining the struct outside of the array would then require
// this array to be an array of pointers which I wanted to avoid
const StepperConfigs STEPPER_CONFIGS[NUMBER_OF_STEPPERS] = {
  [TW] = {55, 54, 16, 5000},
  [WP] = {4,  5,  3, 10000},
  [WR] = {8,  9,  7, 20000},
  [EE] = {12, 13, 11, 20000}
};

#define LA1_DEVICE_NUM 11
#define LA2_DEVICE_NUM 12
#define LA_ZERO_POINT  2048 //when sending messages to LA, 2048 is actually 0 speed

#define SERVO_STEP_SIZE 1 //Servo moves by this amount of degrees at a time
#define SERVO_PIN       6

//UART Constants
#define BAUDRATE        9600
#define MAX_UART_INPUT_SIZE 130

//SPI Constants
#define SPI_MOSI        51
#define SPI_MISO        50
#define SPI_SCLK        52
#define ENCODER_RES     12 //encoder resolution in bits
#define AMT22_NOP       0x00 //SPI NOP command
#define AMT22_RESET     0x60 //SPI Reset command
#define AMT22_ZERO      0x70 //Sets current encoder point as zero
#define NEWLINE         0x0A //ASCII Characters
#define TAB             0x09 //ASCII Characters

//Delay Constants
//Used to ensure that certain time consuming code isn't run too often in loop()
#define ENCODER_DELAY   50
#define UART_DELAY     100
#define SERVO_DELAY    100

//servo joints declarations
bool sv_up = false;
bool sv_down = false;

bool verbose = false; //toggles GPIO and position feedback

bool emergency_stop_en = false; //turns off all steppers and sends stop command to LAs

//Stepper Object Declarations:
AccelStepper tower(AccelStepper::DRIVER, STEPPER_CONFIGS[TW].STEP_PIN, STEPPER_CONFIGS[TW].DIR_PIN);
AccelStepper wristPitch(AccelStepper::DRIVER, STEPPER_CONFIGS[WP].STEP_PIN, STEPPER_CONFIGS[WP].DIR_PIN);
AccelStepper wristRoll(AccelStepper::DRIVER, STEPPER_CONFIGS[WR].STEP_PIN, STEPPER_CONFIGS[WR].DIR_PIN);
AccelStepper endEffector(AccelStepper::DRIVER, STEPPER_CONFIGS[EE].STEP_PIN, STEPPER_CONFIGS[EE].DIR_PIN);

//Linear Acutator Declarations:
JrkG2I2C shoulder(LA1_DEVICE_NUM);
JrkG2I2C elbow(LA2_DEVICE_NUM);

Servo cameraServo; //servo for shoulder camera

//Data types that are generally the same between all joints are stored in this struct:
struct Joint {
  float          velocity_multiplier; //recieved from serial data
  float          currentPos;    
  bool           motor_state_changed;
  int            ENC_SIGN_MULTIPLIER; 
  int            ENC_PIN;      //enable pin for encoder, active low 
  bool           ENC_ENABLE;    //encoder in use when set to true
  int            MAX_SPEED;
  float          MAX_POS_POSITION; //Maximum forward position the joints can approach -> 0 means this field is invalid
  float          MAX_NEG_POSITION; //Maximum backward position the joints can approach
};

Joint joints[JOINT_NUM] = {
  [TW] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = 66,
    .ENC_ENABLE = true,
    .MAX_SPEED = 1000,
    .MAX_POS_POSITION = 90.0f,
    .MAX_NEG_POSITION = -90.0f
  },
  [WP] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = 67,
    .ENC_ENABLE = true,
    .MAX_SPEED = 1000,
    .MAX_POS_POSITION = 95.0f,
    .MAX_NEG_POSITION = -360f
  },
  [WR] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = -1,
    .ENC_ENABLE = false,
    .MAX_SPEED = 1000,
    .MAX_POS_POSITION = -1,
    .MAX_NEG_POSITION = -1
  },
  [EE] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = -1,
    .ENC_ENABLE = false,
    .MAX_SPEED = 1000,
    .MAX_POS_POSITION = -1,
    .MAX_NEG_POSITION = -1
  },
  [SL] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = 68,
    .ENC_ENABLE = false,
    .MAX_SPEED = 600,
    .MAX_POS_POSITION = -1,
    .MAX_NEG_POSITION = -1
  },
  [EL] = {
    .velocity_multiplier = 0,
    .currentPos = 0.0f,
    .motor_state_changed = false,
    .ENC_SIGN_MULTIPLIER = 1,
    .ENC_PIN = 69,
    .ENC_ENABLE = false,
    .MAX_SPEED = 600,
    .MAX_POS_POSITION = -1,
    .MAX_NEG_POSITION = -1
  }
};

void setup() {
  //Set the modes for the SPI IO
  pinMode(SPI_SCLK, OUTPUT);
  pinMode(SPI_MOSI, OUTPUT);
  pinMode(SPI_MISO, INPUT);

  //Initialize communication protocols
  Serial.begin(BAUDRATE);
  Wire.begin();
  SPI.setClockDivider(SPI_CLOCK_DIV4);   //This is the fastest SPI rate that works with the encoders
  SPI.begin();

  // Configure stepper acceleration
  tower.setAcceleration(STEPPER_CONFIGS[TW].ACCELERATION);
  wristPitch.setAcceleration(STEPPER_CONFIGS[WP].ACCELERATION);
  wristRoll.setAcceleration(STEPPER_CONFIGS[WR].ACCELERATION);
  endEffector.setAcceleration(STEPPER_CONFIGS[EE].ACCELERATION);

  // Enable all stepper drivers
  for (int i = 0; i < NUMBER_OF_STEPPERS; i++) {
    if (STEPPER_CONFIGS[i].BOOT_PIN >= 0) {
      pinMode(STEPPER_CONFIGS[i].BOOT_PIN, OUTPUT);
      digitalWrite(STEPPER_CONFIGS[i].BOOT_PIN, HIGH);
    }
  }

  // Set up encoder CS pins (if encoder is enabled)
  for (int i = 0; i < JOINT_NUM; i++) {
    if (joints[i].ENC_ENABLE) {
      pinMode(joints[i].ENC_PIN, OUTPUT);
      digitalWrite(joints[i].ENC_PIN, HIGH);
    }
  }

  //Timer based ISR ensures that jointss are run often enough
  Timer3.initialize(400); // Every 250us. This has been tested and is the minimum frequency that works without vibrations.
  Timer3.attachInterrupt(timerIsr);

  cameraServo.attach(SERVO_PIN); //ensures that this pin is only used for servo
}//end of setup()


//Everything to do with serial comms is here (read and writing)
void loop(){
  // Timers:
  static unsigned long encoder_t = millis();
  static unsigned long joints_t = millis();
  static unsigned long dashb_t = millis();
  static unsigned long fault_t = millis();
  static unsigned long camservo_t = millis();

  if (emergency_stop_en) {
    emergencyStopHandler();
  }

  //Typical command example:
  //Manual: "S;1024;-1024;0;0;0;0;!"
  if (Serial.available()) {
    readSerialInput();
  }

  //Every dashb_delay ms, publish stuff
  if (millis() - dashb_t >= UART_DELAY and verbose) {
    sendSerialFeedback();
    dashb_t = millis();
  }

  //Every enc_delay ms, sample encoder data and move jointss when needed
  if (millis() - encoder_t >= ENCODER_DELAY) {
    updateEncoderPositions();
    encoder_t = millis();
  }

  //Every enc_delay ms, sample encoder data and move jointss when needed
  for (int i = TW ; i < LAST ; i++) {
    bool fwd = false;
    bool bwd = false;
    
    if (joints[i].desiredPos < 0.0){
      fwd = true;

      if (i == TW && joints[TW].currentPos <= motor[TW].MAX_NEG_POSITION){
        fwd = false;
      } else if (i == WP && joints[WP].currentPos >= motor[WP].MAX_POS_POSITION){
        fwd = false;
      }
    } else if (joints[i].desiredPos > 0.0){
      bwd = true;

      if (i == TW && joints[TW].currentPos >= motor[TW].MAX_POS_POSITION){
        bwd = false;
      } 
    }
    
    if (fwd) {          
      joints[i].direction = -1;
      movejointss(i, -1);
    }
    else if (bwd) {
      joints[i].direction = 1;
      movejointss(i, 1);
    }
    else {
      joints[i].direction = 0;
      movejointss(i, 0);
    }
  }

  // Non-blocking servo movement
  if (millis() - camservo_t >= SERVO_DELAY) {
    updateCameraServo();
    camservo_t = millis();
  }
} //end of loop()

//This function reads a byte from the UART/USB everytime it is called
//Once the terminating character (!) is found, the full command is processed
void readSerialInput() {
  static int uart_input_pos = 0; //tracks current index in input buffer
  static char uart_input[MAX_UART_INPUT_SIZE + 1]; //+1 for the terminating string character

  char head = Serial.read();

  if (head == '!') {
    uart_input[uart_input_pos] = '\0'; //Null terminate character
    processCommand(uart_input); // Your function to parse and act on the command
  } 
  else if (c == '\n') {
    //Ignore newline (generally an issue when inputting commands through arduino IDE serial monitor)
    continue;
  } 
  else if (uart_input_pos < MAX_UART_INPUT_SIZE) {
    uart_input[uart_input_pos++] = head;
  }
  else {
    // Reset buffer position when buffer is full to avoid missing the most recent data
    uart_input_pos = 0;
  }
}

//Processes command strings from readSerialInput()
void processCommand(char* input) {
  char* token = strtok(input, ";");

  if (equalsStr(token, "S")) {
    // Set desiredPos for all joints from input
    for (int i = TW; i < JOINT_NUM; i++) {
        token = strtok(NULL, ";");
        if (token) {
          float new_vel_mult = atof(token);

          if(!floatsEqual(new_vel_mult, joints[i].velocity_multiplier)){
            joints[i].velocity_multiplier = new_vel_mult;
            joints[i].motor_state_changed = true;
          }
        }
    }
  }
  else if (equalsStr(token, "set0")) {
    // Reset directions and positions
    for (int i = TW; i < JOINT_NUM; i++) {
      joints[i].velocity_multiplier = 0;
      joints[i].currentPos = 0.0f;

      if(joints[i].ENC_ENABLE){
        setZeroSPI(joints[i].ENC_PIN);  // Your existing function to reset encoder zero
      }
    }
    Serial.println("All joints zeroed!");
  }
  else if (equalsStr(token, "stepper1")) {
    digitalWrite(joints[TW].BOOT_PIN, !digitalRead(joints[TW].BOOT_PIN));
  }
  else if (equalsStr(token, "stepper2")) {
    digitalWrite(joints[WP].BOOT_PIN, !digitalRead(joints[WP].BOOT_PIN));
  }
  else if (equalsStr(token, "stepper3")) {
    digitalWrite(joints[WR].BOOT_PIN, !digitalRead(joints[WR].BOOT_PIN));
  }
  else if (equalsStr(token, "stepper4")) {
    digitalWrite(joints[EE].BOOT_PIN, !digitalRead(joints[EE].BOOT_PIN));
  }
  else if (equalsStr(token, "stop")) {
    emergency_stop_en = true;
  }
  else if (equalsStr(token, "v")) {
    verbose = !verbose;
  }
  else if (equalsStr(token, "svu")) {
    sv_down = false;
    sv_up = true;
    Serial.println("Servo moving up");
  }
  else if (equalsStr(token, "svd")) {
    sv_up = false;
    sv_down = true;
    Serial.println("Servo moving down");
  }
  else if (equalsStr(token, "svs")) {
    sv_up = false;
    sv_down = false;
    Serial.println("Servo stopped moving");
  }
  else {
    Serial.println("Unknown command!");
  }
}

//Sends both GPIO and Encoder feedback over UART/USB when called
void sendSerialFeedback() {
  // Publish current positions for all steppers
  Serial.println();
  Serial.print("f;");
  for (int i = TW; i < JOINT_NUM; i++) {
      Serial.print(joints[i].currentPos);
      Serial.print(";");
  }
  Serial.println("!");

  // Publish GPIO states for each stepper BOOT_PIN
  Serial.println();
  Serial.print("g;");
  for (int i = TW; i < NUMBER_OF_STEPPERS; i++) {
      Serial.print(digitalRead(STEPPER_CONFIGS[i].BOOT_PIN));
      Serial.print(";");
  }
  Serial.print(emergency_stop_en);
  Serial.println(";!");
}

void updateEncoderPositions(){
  for (int i = TW ; i < NUMBER_OF_STEPPERS ; i++) {
    if(joints[i].ENC_ENABLE){
      float new_pos = getPositionDegrees(joints[i].ENC_PIN) * joints[i].ENC_SIGN_MULTIPLIER;
      
      if (floatsEqual(new_pos, joints[i].currentPos)){
        joints[i].currentPos = new_pos;
        joints[i].motor_state_changed = true;
      }
    }
  }
}

void updateCameraServo(){
  static int servo_angular_pos = 90;

  if (sv_up) {
    servo_angular_pos += SERVO_STEP_SIZE;

    if (servo_angular_pos >= 180) {
      servo_angular_pos = 180;
      sv_up = false;
      Serial.println("Reached max position, stopped");
    }

    cameraServo.write(servo_angular_pos);
  }
  else if (sv_down) {
    servo_angular_pos -= stepSize;

    if (servo_angular_pos <= 0) {
      servo_angular_pos = 0;
      sv_down = false;
      Serial.println("Reached min position, stopped");
    }

    cameraServo.write(servo_angular_pos);
  }
}

//Basic logic for controlling jointss
//Should not be called often since its blocking
void movejointss(int i, int dir) {

  joints[i].speed = calculateNextSpeed(i);
  joints[i].direction = dir;

  //Tower joints
  if (i == TW) {
    //Moves to whichever direction towards a step goal
    if (dir != 0) {
      tower.setMaxSpeed(joints[i].speed);
      tower.move(-joints[i].sign*dir*motor[i].MAX_RANGE);
    }
    //stops stepper
    else {
      tower.stop();
      tower.runToPosition();
    }
  }
  //LA1
  else if (i == L1) {
    //extend (dir == 1) or retract (dir == -1)
    if (dir != 0)
      LA1.setTarget(2048+dir*joints[i].sign*motor[i].speed);
    //stop LA joints
    else 
      LA1.stopjoints();
  }
  //LA2 
  else if (i == L2) {
    if (dir != 0) 
      LA2.setTarget(2048+dir*joints[i].sign*motor[i].speed);
    else 
      LA2.stopjoints();
  }
  //Wrist pitch
  else if (i == WP) {
    if (dir != 0) {
      wristPitch.setMaxSpeed(joints[i].speed);
      wristPitch.move(-joints[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      wristPitch.stop();
      wristPitch.runToPosition();
    }
  }
  //Wrist roll
  else if (i == WR) {
    if (dir != 0) {
      wristRoll.setMaxSpeed(joints[i].speed);
      wristRoll.move(joints[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      wristRoll.stop();
      wristRoll.runToPosition();
    }
  }
  //End effector 
  else {
    if (dir != 0) {
      endEffector.setMaxSpeed(joints[i].speed);
      endEffector.move(joints[i].sign*dir*motor[i].MAX_RANGE);
    }
    else {
      endEffector.stop();
      endEffector.runToPosition();
    }
  }
} //end of movejointss()

void timerIsr() {
  sei(); //enable global interrupts for servo pwm generation,

  // The run function moves the steppers one step if the target position is not reached (set by the move function)
  // Needs to be called consistently to avoid vibrations at a very high frequency
  wristRoll.run();
  endEffector.run();
  wristPitch.run();
  tower.run();
}

// Absolute Encoder helper functions below

// For a joints with id i, update its associated position by converting SPI enc. data to radians
float getPositionDegrees(uint8_t encoder_cs){
  //create a 16 bit variable to hold the encoders position
  uint16_t encoderPosition;
  float encoderPositionDegrees = 0;
  int attempts = 0;

  //this function gets the encoder position and returns it as a uint16_t
  encoderPosition = getPositionSPI(encoder_cs, ENCODER_RES); 

  //if the position returned was 0xFFFF we know that there was an error calculating the checksum
  //make 3 attempts for position. we will pre-increment attempts because we'll use the number later and want an accurate count
  while (encoderPosition == 0xFFFF && ++attempts < 3) {
    encoderPosition = getPositionSPI(encoder_cs, ENCODER_RES); //try again
  }

  if (encoderPosition == 0xFFFF) { //position is bad, send error message
    Serial.println("Encoder error");
  }
  else {
    //Encoder outputs value between 0 to 4095 (2^12 - 1)
    //The conversion to degrees is (enc_count/# of positions) * Max degrees
    encoderPositionDegrees = 360*float(encoderPosition)/4096;

    //Normalizes degrees to signed range (-180 to 180) without changing where the zero point is 
    if (encoderPositionDegrees >= 180.0){
      encoderPositionDegrees -=360.0; 
    }
  }

  return encoderPositionDegrees;
}


/*
 * This function gets the absolute position from the AMT22 encoder using the SPI bus. The AMT22 position includes 2 checkbits to use
 * for position verification. Both 12-bit and 14-bit encoders transfer position via two bytes, giving 16-bits regardless of resolution.
 * For 12-bit encoders the position is left-shifted two bits, leaving the right two bits as zeros. This gives the impression that the encoder
 * is actually sending 14-bits, when it is actually sending 12-bit values, where every number is multiplied by 4. 
 * This function takes the pin number of the desired device as an input
 * This funciton expects res12 or res14 to properly format position responses.
 * Error values are returned as 0xFFFF
 */
uint16_t getPositionSPI(uint8_t encoder, uint8_t resolution){
  uint16_t currentPosition;       //16-bit response from encoder
  bool binaryArray[16];           //after receiving the position we will populate this array and use it for calculating the checksum

  //get first byte which is the high byte, shift it 8 bits. don't release line for the first byte
  currentPosition = spiWriteRead(AMT22_NOP, encoder, false) << 8;   

  //this is the time required between bytes as specified in the datasheet.
  //We will implement that time delay here, however the arduino is not the fastest device so the delay
  //is likely inherantly there already
  delayMicroseconds(3);

  //OR the low byte with the currentPosition variable. release line after second byte
  currentPosition |= spiWriteRead(AMT22_NOP, encoder, true);        

  //run through the 16 bits of position and put each bit into a slot in the array so we can do the checksum calculation
  for(int i = 0; i < 16; i++) binaryArray[i] = (0x01) & (currentPosition >> (i));

  //using the equation on the datasheet we can calculate the checksums and then make sure they match what the encoder sent
  if ((binaryArray[15] == !(binaryArray[13] ^ binaryArray[11] ^ binaryArray[9] ^ binaryArray[7] ^ binaryArray[5] ^ binaryArray[3] ^ binaryArray[1]))
          && (binaryArray[14] == !(binaryArray[12] ^ binaryArray[10] ^ binaryArray[8] ^ binaryArray[6] ^ binaryArray[4] ^ binaryArray[2] ^ binaryArray[0])))
    {
      //we got back a good position, so just mask away the checkbits
      currentPosition &= 0x3FFF;
    }
  else{
    currentPosition = 0xFFFF; //bad position
  }

  //If the resolution is 12-bits, and wasn't 0xFFFF, then shift position, otherwise do nothing
  if ((resolution == RES12) && (currentPosition != 0xFFFF)) currentPosition = currentPosition >> 2;

  return currentPosition;
}

/*
 * This function does the SPI transfer. sendByte is the byte to transmit. 
 * Use releaseLine to let the spiWriteRead function know if it should release
 * the chip select line after transfer.  
 * This function takes the pin number of the desired device as an input
 * The received data is returned.
 */
uint8_t spiWriteRead(uint8_t sendByte, uint8_t encoder, uint8_t releaseLine){
  //holder for the received over SPI
  uint8_t data;

  //set cs low, cs may already be low but there's no issue calling it again except for extra time
  setCSLine(encoder ,LOW);

  //There is a minimum time requirement after CS goes low before data can be clocked out of the encoder.
  //We will implement that time delay here, however the arduino is not the fastest device so the delay
  //is likely inherantly there already
  delayMicroseconds(3);

  //send the command  
  data = SPI.transfer(sendByte);
  delayMicroseconds(3); //There is also a minimum time after clocking that CS should remain asserted before we release it
  setCSLine(encoder, releaseLine); //if releaseLine is high set it high else it stays low
  
  return data;
}

/*
 * This function sets the state of the SPI line. It isn't necessary but makes the code more readable than having digitalWrite everywhere 
 * This function takes the pin number of the desired device as an input
 */
void setCSLine (uint8_t encoder, uint8_t csLine){
  digitalWrite(encoder, csLine);
}

/*
 * The AMT22 bus allows for extended commands. The first byte is 0x00 like a normal position transfer, but the 
 * second byte is the command.  
 * This function takes the pin number of the desired device as an input
 */
void setZeroSPI(uint8_t encoder){
  spiWriteRead(AMT22_NOP, encoder, false);

  //this is the time required between bytes as specified in the datasheet.
  //We will implement that time delay here, however the arduino is not the fastest device so the delay
  //is likely inherantly there already
  delayMicroseconds(3); 
  
  spiWriteRead(AMT22_ZERO, encoder, true);
  delay(250); //250 second delay to allow the encoder to reset
}

/*
 * The AMT22 bus allows for extended commands. The first byte is 0x00 like a normal position transfer, but the 
 * second byte is the command.  
 * This function takes the pin number of the desired device as an input
 */
void resetAMT22(uint8_t encoder){
  spiWriteRead(AMT22_NOP, encoder, false);

  //this is the time required between bytes as specified in the datasheet.
  //We will implement that time delay here, however the arduino is not the fastest device so the delay
  //is likely inherantly there already
  delayMicroseconds(3); 
  
  spiWriteRead(AMT22_RESET, encoder, true);
  
  delay(250); //250 second delay to allow the encoder to start back up
}

//Helper functions used across
//A more understandable way to use strcmp
boolean equalsStr(char* str1, char* str2) {
  return !strcmp(str1, str2);
}

//Due to floating point values not being exact we can't use != or == to compare two floating point numbers
//Floats equal up to a difference;
bool floatsEqual(float a, float b) {
  const int fp_threshold = 0.0001; //typically we don't care about precision lower than 

  return abs(a-b) <= 0.000;
}