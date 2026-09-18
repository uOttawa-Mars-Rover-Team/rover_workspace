#include "TaskEE.h"

// Constructor – forward everything to the base class
TaskEE::TaskEE(const char* n, uint8_t step, uint8_t dir, uint8_t boot,
               uint8_t fault, int32_t accel, int32_t range, float spd)
    : DriverStepper(n, step, dir, boot, fault, accel, range, spd)
{
}

// Open the end-effector (positive direction)
bool TaskEE::open(float velocity) {
    if (velocity < 0) {
        Serial.println("ERROR: open() expects a positive velocity");
        return false;
    }
    return moveMotor(velocity);   // forward
}

// Close the end-effector (negative direction)
bool TaskEE::close(float velocity) {
    if (velocity < 0) {
        Serial.println("ERROR: close() expects a positive velocity");
        return false;
    }
    return moveMotor(-velocity);  // reverse
}

bool TaskEE::stop() {
    Serial.println("CLOSING EE.");
    return moveMotor(0);
}