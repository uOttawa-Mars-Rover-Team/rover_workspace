#include <ros.h>
//#include <std_msgs/String.h>
#include <std_msgs/MultiArrayLayout.h>
#include <std_msgs/MultiArrayDimension.h>
#include <std_msgs/Float32MultiArray.h>
#include <Wire.h>
#include <SPI.h>
#include <SparkFunLSM9DS1.h>

LSM9DS1 imu;

#define PRINT_CALCULATED
//#define PRINT_RAW
#define PRINT_SPEED 250 // 250 ms between prints
static unsigned long lastPrint = 0; // Keep track of print time

#define DECLINATION -8.58 // Declination (degrees) in Boulder, CO.

//ros stuff
ros::NodeHandle nh;
//std_msgs::String str_msg;
//ros::Publisher chatter("IMU", &str_msg);
std_msgs::Float32MultiArray imu_msg;
static std_msgs::MultiArrayDimension dimen;
ros::Publisher chatter("IMU", &imu_msg);

//char hello[13] = "hello world!";
//char imu_data[128];
//gx,gy,gz,ax,ay,az,mx,my,mz,roll,pitch,yaw
float imu_data[3];

//Function definitions
void printGyro();
void printAccel();
void printMag();
void printAttitude(float ax, float ay, float az, float mx, float my, float mz);

void setup()
{
  //Serial.begin(115200);
  //Serial.begin(57600);

  Wire.begin();

  imu_msg.layout.data_offset = 0;
  imu_msg.layout.dim = &dimen;//(static std_msgs::MultiArrayDimension *) malloc(sizeof(std_msgs::MultiArrayDimension));
  imu_msg.layout.dim[0].label = "imu";
  imu_msg.layout.dim[0].size = 3;
  imu_msg.layout.dim[0].stride = 3;
  imu_msg.layout.dim_length = 1;
  imu_msg.data_length = 3;
  
  nh.initNode();
  nh.advertise(chatter);
  //ros::Publisher chatter = nh.advertise<std_msgs::Float32MultiArray>("IMU", 3);

  if (imu.begin() == false) // with no arguments, this uses default addresses (AG:0x6B, M:0x1E) and i2c port (Wire).
  {
    //Serial.println("Failed to communicate with LSM9DS1.");
    //Serial.println("Double-check wiring.");
    /*Serial.println("Default settings in this sketch will " \
                   "work for an out of the box LSM9DS1 " \
                   "Breakout, but may need to be modified " \
                   "if the board jumpers are.");*/
    while (1);
  }
}

void loop()
{
 
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

  if ((lastPrint + PRINT_SPEED) < millis())
  {
    // Print the heading and orientation for fun!
    // Call print attitude. The LSM9DS1's mag x and y
    // axes are opposite to the accelerometer, so my, mx are
    // substituted for each other.
    printAttitude(imu.ax, imu.ay, imu.az,
                  -imu.my, -imu.mx, imu.mz);
    //Serial.println();

    lastPrint = millis(); // Update lastPrint time
  }
//dtostrf(imu.ax, 6, 2, imu_data);
  //str_msg.data = imu_data;
  //chatter.publish(&str_msg);
  imu_msg.data = imu_data;
  chatter.publish(&imu_msg);
  
  nh.spinOnce();
  delay(1000);
}

// Calculate pitch, roll, and heading.
// Pitch/roll calculations take from this app note:
// http://cache.freescale.com/files/sensors/doc/app_note/AN3461.pdf?fpsp=1
// Heading calculations taken from this app note:
// http://www51.honeywell.com/aero/common/documents/myaerospacecatalog-documents/Defense_Brochures-documents/Magnetic__Literature_Application_notes-documents/AN203_Compass_Heading_Using_Magnetometers.pdf
void printAttitude(float ax, float ay, float az, float mx, float my, float mz)
{
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

  imu_data[0] = roll;
  imu_data[1] = pitch;
  imu_data[2] = heading;
  
  /*char data[8];
  //roll, pitch, yaw
  dtostrf(roll, 6, 2, data);
  memcpy(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(pitch, 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(heading, 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  
  //acceleration x, y, z
  dtostrf(imu.calcAccel(imu.ax), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcAccel(imu.ay), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcAccel(imu.az), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);  
  
  //gyroscope x, y, z
  dtostrf(imu.calcGyro(imu.gx), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcGyro(imu.gy), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcGyro(imu.gz), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  
  //magnometer x, y, z
  dtostrf(imu.calcMag(imu.mx), 6, 2, data);
  strncat(imu_data, data, 10);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcMag(imu.my), 6, 2, data);
  strncat(imu_data, data, 8);
  strncat(imu_data, ",", 1);
  dtostrf(imu.calcMag(imu.mz), 6, 2, data);
  strncat(imu_data, data, 8);
  //strncat(imu_data, ",", 1);*/

  //Serial.print("Pitch, Roll: ");
  //Serial.print(pitch, 2);
  //Serial.print(", ");
  //Serial.println(roll, 2);
  //Serial.print("Heading: "); Serial.println(heading, 2);
}
