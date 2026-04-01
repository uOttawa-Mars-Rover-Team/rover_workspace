#include "DriverStepper.h"

// Constructor
StepperMotor::StepperMotor(const char* n, uint8_t step, uint8_t dir, uint8_t boot,
                           uint8_t fault, int32_t accel, int32_t range, float spd)
    : driver(AccelStepper::DRIVER, step, dir)
{
    name = n;
    stepPin = step;
    dirPin = dir;
    bootPin = boot;
    faultPin = fault;
    acceleration = accel;
    maxRange = range;
    speed = spd;
    enabled = false;
}

// Initialize hardware
void StepperMotor::init() {
    pinMode(bootPin, OUTPUT);
    digitalWrite(bootPin, HIGH);
    pinMode(faultPin, INPUT_PULLUP);
    driver.setAcceleration(acceleration);
    driver.setMaxSpeed(speed);
    enabled = true;
    Serial.print("Initialized: ");
    Serial.println(name);
}

// Enable motor
void StepperMotor::enable() {
    digitalWrite(bootPin, HIGH);
    enabled = true;
    Serial.print(name);
    Serial.println(" enabled");
}

// Disable motor
void StepperMotor::disable() {
    stop();
    digitalWrite(bootPin, LOW);
    enabled = false;
    Serial.print(name);
    Serial.println(" disabled");
}

// bool StepperMotor::moveMotor(int8_t value) {
//     if (value < -1 || value > 1) {
//         Serial.println("ERROR: value must be -1, 0, or 1");
//         return false;
//     }

//     if (!enabled) {
//         Serial.println("ERROR: motor is disabled");
//         return false;
//     }

//     driver.setMaxSpeed(speed);

//     if (value == 1) {
//         driver.move(maxRange);   // Forward
//     }
//     else if (value == -1) {
//         driver.move(-maxRange);  // Reverse
//     }
//     else {
//         driver.stop();           // Stop
//     }

//     driver.run();                // <-- this is the “fix” / coupling
//     return true;
// }

bool StepperMotor::moveMotor(float velocity) {
    if (fabs(velocity) > speed) {  // 'speed' is your configured max allowed
        Serial.println("ERROR: velocity exceeds max speed");
        return false;
    }
    if (!enabled) {
        Serial.println("ERROR: motor is disabled");
        return false;
    }

    driver.setMaxSpeed(fabs(velocity));

    if (velocity > 0) {
        driver.move(maxRange);      // "continuous" forward (large target)
    } else if (velocity < 0) {
        driver.move(-maxRange);     // "continuous" reverse
    } else {
        driver.stop();              // decelerate to stop (needs repeated calls)
    }

    driver.run();                   // coupled run like the sample project
    return true;
}


// Stop motor
void StepperMotor::stop() {
    driver.stop();
}

// Must call frequently - non-blocking
bool StepperMotor::run() {
    return driver.run();
}