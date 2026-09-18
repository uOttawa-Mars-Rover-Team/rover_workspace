#include "MQ-Sensor-SOLDERED.h"

#define HYDROGEN_SENSOR_ANALOG_PIN A3
#define OZONE_SENSOR_ANALOG_PIN    A1
#define DATA_LED_PIN               2

MQ8 mq8(HYDROGEN_SENSOR_ANALOG_PIN);
MQ131 mq131(OZONE_SENSOR_ANALOG_PIN);

#define NUM_OF_CALIBRATIONS   10

void setup() {
  Serial.begin(115200);
  pinMode(DATA_LED_PIN, OUTPUT);

  mq8.begin();
  mq131.begin();

  bool cal1 = mq8.calibrateSensor(NUM_OF_CALIBRATIONS);
  bool cal2 = mq131.calibrateSensor(NUM_OF_CALIBRATIONS);
}

void loop() {
  digitalWrite(DATA_LED_PIN, HIGH);

  mq8.update();
  mq131.update();

  Serial.print(mq8.readSensor());
  Serial.print(";");
  Serial.println(mq131.readSensor());

  digitalWrite(DATA_LED_PIN, LOW);
  delay(50);
}





