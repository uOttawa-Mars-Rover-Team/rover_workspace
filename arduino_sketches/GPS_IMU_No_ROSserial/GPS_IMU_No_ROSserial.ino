/* This code is based on the Adafruit GPS library - GPS_SoftwareSerial_Parsing example
 * and the SParkfunLSM9DS1IMU - LSM9DS1_Basic_I2C example. The values printed from
 * the Arduino via the serial port on this sketch are parsed by a node in the gps_imu_node
 * ROS package. This is to save enough space on the Arduino to allow both the IMU and the 
 * GPS to be run from the same Arduino. rosserial takes up too much memory and requires a 
 * node to be run computer side anyway to work. */

//PINOUT
// Connect the GPS VIN to 5V
// Connect the GPS GND pin to ground
// Connect the GPS TX (transmit) pin to Digital 8
// Connect the GPS RX (receive) pin to Digital 7

// Connect the IMU GND pin to ground
// Connect the IMU VDD pin to 3V
// Connect the IMU SDA (I2C data) to SDA on Arduino
// Connect the IMU SCL (I2C clock) to SCL on Arduino

//GPS
#include <Adafruit_GPS.h>
#include <SoftwareSerial.h>

//IMU
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>

LSM9DS1 imu;

//GPS
#define PRINT_CALCULATED
#define PRINT_SPEED 250 // 250 ms between prints
static unsigned long lastPrint = 0; // Keep track of print time

#define DECLINATION -8.58 // Declination (degrees) in Boulder, CO.


// you can change the pin numbers to match your wiring:
SoftwareSerial mySerial(8, 7);
Adafruit_GPS GPS(&mySerial);

// Set GPSECHO to 'false' to turn off echoing the GPS data to the Serial console
// Set to 'true' if you want to debug and listen to the raw GPS sentences
#define GPSECHO  false

void setup()
{

  // connect at 115200 so we can read the GPS fast enough and echo without dropping chars
  // also spit it out
  Serial.begin(115200);

  // 9600 NMEA is the default baud rate for Adafruit MTK GPS's- some use 4800
  GPS.begin(9600);

  // uncomment this line to turn on RMC (recommended minimum) and GGA (fix data) including altitude
  GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCGGA);
  // uncomment this line to turn on only the "minimum recommended" data
  //GPS.sendCommand(PMTK_SET_NMEA_OUTPUT_RMCONLY);
  // For parsing data, we don't suggest using anything but either RMC only or RMC+GGA since
  // the parser doesn't care about other sentences at this time

  // Set the update rate
  GPS.sendCommand(PMTK_SET_NMEA_UPDATE_1HZ);   // 1 Hz update rate
  // For the parsing code to work nicely and have time to sort thru the data, and
  // print it out we don't suggest using anything higher than 1 Hz

  // Request updates on antenna status, comment out to keep quiet
  GPS.sendCommand(PGCMD_ANTENNA);

  delay(1000);
  // Ask for firmware version
  mySerial.println(PMTK_Q_RELEASE);

  //IMU
  Wire.begin();

  if (imu.begin() == false) // with no arguments, this uses default addresses (AG:0x6B, M:0x1E) and i2c port (Wire).
  {
    while (1);
  }
}

uint32_t timer = millis();
void loop()                     // run over and over again
{
  //IMU
  // Update the sensor values whenever new data is available
  if ( imu.gyroAvailable() )
  {
    // update gx, gy, and gz
    imu.readGyro();
  }
  if ( imu.accelAvailable() )
  {
    // update ax, ay, and az
    imu.readAccel();
  }
  if ( imu.magAvailable() )
  {
    // update mx, my, and mz
    imu.readMag();
  }

  //GPS
  char c = GPS.read();
  // if you want to debug, this is a good time to do it!
  /*if ((c) && (GPSECHO))
    Serial.write(c);*/

  // if a sentence is received, we can check the checksum, parse it...
  if (GPS.newNMEAreceived()) {
    // a tricky thing here is if we print the NMEA sentence, or data
    // we end up not listening and catching other sentences!
    // so be very wary if using OUTPUT_ALLDATA and trytng to print out data
    //Serial.println(GPS.lastNMEA());   // this also sets the newNMEAreceived() flag to false

    if (!GPS.parse(GPS.lastNMEA()))   // this also sets the newNMEAreceived() flag to false
      return;  // we can fail to parse a sentence in which case we should just wait for another
  }

  // if millis() or timer wraps around, we'll just reset it
  if (timer > millis())  timer = millis();

  // approximately every 2 seconds or so, print out the current stats
  if (millis() - timer > 2000) {
    timer = millis(); // reset the timer

    //fix is 0 if not connected and 1 if is
    Serial.print("fix: ");
    Serial.print((int)GPS.fix);
    Serial.println(",");

    //the number of satellites connected to
    Serial.print("sats: ");
    Serial.print((int)GPS.satellites);
    Serial.println(",");

    //get latitude and longitude if has a fix
    if (GPS.fix) {
      Serial.print("lat: ");
      Serial.print(GPS.latitude, 4);
      Serial.print(GPS.lat);
      Serial.println(",");
      Serial.print("lon: ");
      Serial.print(GPS.longitude, 4);
      Serial.print(GPS.lon);
      Serial.println(",");
    } else {
      Serial.println("lat: None,\nlon: None,");
    }

    float ax, ay, az, mx, my, mz;
    ax = imu.ax;
    ay = imu.ay;
    az = imu.az;
    my = -imu.my;
    mx = -imu.mx;
    mz = imu.mz;
    
    float roll = atan2(ay, az);
  float pitch = atan2(-ax, sqrt(ay * ay + az * az));

  float heading;
  if (my == 0)
    heading = (mx < 0) ? PI : 0;
  else
    heading = atan2(mx, my);

  heading -= DECLINATION * PI / 180;

  if (heading > PI) heading -= (2 * PI);
  else if (heading < -PI) heading += (2 * PI);

  // Convert everything from radians to degrees:
  heading *= 180.0 / PI;
  pitch *= 180.0 / PI;
  roll  *= 180.0 / PI;

    //print the IMU stuff
    Serial.print("roll: ");
    Serial.print(roll, 4);
    Serial.println(",");
    Serial.print("pitch: ");
    Serial.print(pitch, 4);
    Serial.println(",");
    Serial.print("yaw: ");
    Serial.print(heading, 4);
    Serial.println(",");
  }
}
