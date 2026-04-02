#include "DriverLA.h"

DriverLA LA1(12);
// Upper layer will construct actuators and call moveMotor; placeholder sketch.
void setup() {
    DriverLA_InitI2C();
}

void loop() {
    LA1.moveMotor(400, 1);
    delay(3000);
    LA1.moveMotor(200, -1);
    delay(3000);
}
