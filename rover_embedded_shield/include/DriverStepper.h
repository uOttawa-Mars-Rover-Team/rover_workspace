#ifndef DRIVERSTEPPER_H
#define DRIVERSTEPPER_H

#include <Arduino.h>
#include <AccelStepper.h>

class DriverStepper {
 private:
    float lastVelocity_ = -1.0f;   // sentinel so first call always sets speed 
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
    int8_t lastDirection_ = 0;

    // Constructor
    DriverStepper(const char* n, uint8_t step, uint8_t dir, uint8_t boot,
                 uint8_t fault, int32_t accel, int32_t range, float spd);

    // Methods
    void init();
    void enable();
    void disable();
    bool moveMotor(float velocity);
    void stop();
    bool run();
};

#endif
