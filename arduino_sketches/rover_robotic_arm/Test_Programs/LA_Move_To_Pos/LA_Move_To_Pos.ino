/* Include the SPI library for the arduino boards */
#include <SPI.h>
#include <JrkG2.h>

/* Serial rates for UART */
#define BAUDRATE        115200

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
#define ENC_0           68 //L1
//#define ENC_0           69 //L2
#define SPI_MOSI        51
#define SPI_MISO        50
#define SPI_SCLK        52

float goalPosition = 0.0;

// Linear actuator setup
JrkG2I2C LA1(11);
JrkG2I2C LA2(12);

void setup() 
{
  //Set the modes for the SPI IO
  pinMode(SPI_SCLK, OUTPUT);
  pinMode(SPI_MOSI, OUTPUT);
  pinMode(SPI_MISO, INPUT);
  pinMode(ENC_0, OUTPUT);
  
  //Initialize the UART serial connection for debugging
  Serial.begin(BAUDRATE);

  //Get the CS line high which is the default inactive state
  digitalWrite(ENC_0, HIGH);
  digitalWrite(69, HIGH);

  //set the clockrate. Uno clock rate is 16Mhz, divider of 32 gives 500 kHz.
  //500 kHz is a good speed for our test environment
  SPI.setClockDivider(SPI_CLOCK_DIV128);   // 4 MHz
  
  //start SPI bus
  SPI.begin();

  setZeroSPI(ENC_0); //sets starting position as 0 degrees

  //start I2C bus
  Wire.begin();
}

void loop() 
{
  //create a 16 bit variable to hold the encoders position
  uint16_t encoderPosition;
  float encoderPositionDegrees;
  int attempts = 0;

  //example string containing position to move the motor to:
  //100.0 move to 100 degrees
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n'); //read the input until newline
    input.trim(); //remove any leading or trailing whitespace
    goalPosition = input.toFloat(); //convert the string to a float
  }

  //this function gets the encoder position and returns it as a uint16_t
  //send the function either res12 or res14 for your encoders resolution
  encoderPosition = getPositionSPI(ENC_0, RES12); 

  //if the position returned was 0xFFFF we know that there was an error calculating the checksum
  //make 3 attempts for position. we will pre-increment attempts because we'll use the number later and want an accurate count
  while (encoderPosition == 0xFFFF && ++attempts < 3)
  {
    encoderPosition = getPositionSPI(ENC_0, RES12); //try again
  }

  if (encoderPosition == 0xFFFF) //position is bad, let the user know how many times we tried
  {
    Serial.println("Encoder error");
  }
  else //position was good, print to serial stream
  {
    encoderPositionDegrees = 360*float(encoderPosition)/4096;
    
    if (encoderPositionDegrees >= 180.0){
      encoderPositionDegrees -=360.0; 
    }
    
    float error = goalPosition - encoderPositionDegrees; //calculate the error from the goal position
    
    if (abs(error) < 0.5){ //0.5 degree tolerance for position
      LA1.stopMotor();
      //LA2.stopMotor();
    } else if (error < 0){ //goal position lower than current position --> retract
      LA1.setTarget(2048-600);
      LA2.setTarget(2048-600);
    } else { //goal position higher than current position --> extend
      LA1.setTarget(2048+600);
      //LA2.setTarget(2048+600);
    }

    Serial.print("Position: ");
    Serial.print(encoderPositionDegrees, DEC); //print the position in decimal format
    Serial.write(NEWLINE);
  }
}

uint16_t getPositionSPI(uint8_t encoder, uint8_t resolution)
{
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
  else
  {
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
uint8_t spiWriteRead(uint8_t sendByte, uint8_t encoder, uint8_t releaseLine)
{
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
void setCSLine (uint8_t encoder, uint8_t csLine)
{
  digitalWrite(encoder, csLine);
}

/*
 * The AMT22 bus allows for extended commands. The first byte is 0x00 like a normal position transfer, but the 
 * second byte is the command.  
 * This function takes the pin number of the desired device as an input
 */
void setZeroSPI(uint8_t encoder)
{
  spiWriteRead(AMT22_NOP, encoder, false);

  //this is the time required between bytes as specified in the datasheet.
  //We will implement that time delay here, however the arduino is not the fastest device so the delay
  //is likely inherantly there already
  delayMicroseconds(3); 
  
  spiWriteRead(AMT22_ZERO, encoder, true);
  delay(250); //250 second delay to allow the encoder to reset
}
