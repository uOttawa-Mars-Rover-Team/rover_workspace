/**
 * This sketch is used to determine the gyroscope offsets for a specific IMU.
 * The average values are calculated when the IMU is not moving. These values are
 * then input into the GPS_IMU_No_ROSserial.ino sketch. The values must be updated
 * everytime the IMU is changed. Failure to do so will result in the IMU not reading
 * 0 properly and the locatization software thinking the rover is spinning.
 * 
 * To Use:
 * Run this sketch while the IMU is connected to the Arduino and stationnary.
 * After the values output in the serial monitor stablize, copy them into the
 * GPS_IMU_No_ROSserial.ino sketch for the values GYRO_X_OFFSET, GYRO_Y_OFFSET 
 * and GYRO_Z_OFFSET.
 */

//PINOUT
// Connect the IMU GND pin to ground
// Connect the IMU VDD pin to 3V
// Connect the IMU SDA (I2C data) to SDA on Arduino
// Connect the IMU SCL (I2C clock) to SCL on Arduino

// The SFE_LSM9DS1 library requires both Wire and SPI be
// included BEFORE including the 9DS1 library.
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>

LSM9DS1 imu;

// Sketch Output Settings 
#define PRINT_SPEED 250 // 250 ms between prints
static unsigned long lastPrint = 0; // Keep track of print time

//Function definitions
void printGyro();

void setup()
{
  Serial.begin(115200);

  Wire.begin();

  if (imu.begin() == false) // with no arguments, this uses default addresses (AG:0x6B, M:0x1E) and i2c port (Wire).
  {
    Serial.println("Failed to communicate with LSM9DS1.");
    Serial.println("Double-check wiring.");
    Serial.println("Default settings in this sketch will " \
                   "work for an out of the box LSM9DS1 " \
                   "Breakout, but may need to be modified " \
                   "if the board jumpers are.");
    while (1);
  }
}

void loop()
{
  // Update the sensor values whenever new data is available
  if ( imu.gyroAvailable() )
  {
    imu.readGyro();
  }

  if ((lastPrint + PRINT_SPEED) < millis())
  {
    printGyro(); 
    Serial.println();

    lastPrint = millis(); // Update lastPrint time
  }
}

void printGyro()
{
  static float xTotal = 0;
  static float yTotal = 0;
  static float zTotal = 0;

  static int numMeasures = 0;
  
  Serial.print("G: ");
  // Get the deg/s value from the ADC value
  float x = imu.calcGyro(imu.gx);
  float y = imu.calcGyro(imu.gy);
  float z = imu.calcGyro(imu.gz);
  
  xTotal += x;
  yTotal += y;
  zTotal += z;

  ++numMeasures;
  
  Serial.print(x, 2);
  Serial.print(", ");
  Serial.print(y, 2);
  Serial.print(", ");
  Serial.print(z, 2);
  Serial.println(" deg/s");

  Serial.print("New gryo avgs: ");
  Serial.print(xTotal/numMeasures, 2);
  Serial.print(", ");
  Serial.print(yTotal/numMeasures, 2);
  Serial.print(", ");
  Serial.print(zTotal/numMeasures, 2);
  Serial.println(" deg/s");
}
