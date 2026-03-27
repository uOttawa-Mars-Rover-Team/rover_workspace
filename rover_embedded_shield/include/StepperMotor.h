#ifndef STEPPERMOTOR_H
#define STEPPERMOTOR_H

#include <Arduino.h>
#include <AccelStepper.h>

class StepperMotor {
public:
    // Attributes
    const char* name;
    uint8_t stepPin;
    uint8_t dirPin;
    uint8_t bootPin;
    uint8_t faultPin;
    int32_t acceleration;
    int32_t maxRange;
    float speed;
    bool enabled;
    AccelStepper driver;

    // Constructor
    StepperMotor(const char* n, uint8_t step, uint8_t dir, uint8_t boot,
                 uint8_t fault, int32_t accel, int32_t range, float spd);

    // Methods
    void init();
    void enable();
    void disable();
    bool moveMotor(int8_t value);
    void stop();
    bool run();
};

#endif