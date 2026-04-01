#ifndef TASKEE_H
#define TASKEE_H

#include <Arduino.h>
#include <AccelStepper.h>
#include <DriverStepper.h>

class TaskEE : public DriverStepper {
public:
    // Attributes
    TaskEE(const char* n, uint8_t step, uint8_t dir, uint8_t boot,
                 uint8_t fault, int32_t accel, int32_t range, float spd);

    // Methods
    bool open(float velocity);
    bool close(float velocity);
};

#endif