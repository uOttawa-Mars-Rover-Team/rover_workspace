#include "StepperMotor.h"

// Variable names: stepMotor1, stepMotor2, ...

// StepperMotor stepMotor1(
//   "Motor1",     name:   label for debugging/printing
//   6,            step:   STEP pin number
//   7,            dir:    DIR pin number
//   17,           boot:   BOOT/ENABLE pin (your init() drives HIGH)
//   68,           fault:  FAULT pin (input, pullup)
//   5000,         accel:  acceleration (steps/sec^2)
//   1000000,      range:  maxRange (steps) used for long/continuous move commands
//   3000.0        spd:    max speed (steps/sec)
// );

static uint8_t direction = 1;
static float cmdSpeed = 2500;
static unsigned long t0 = millis();

StepperMotor stepMotor1("Motor1", 4,  5, 3, 2,  5000, 1000000, 3000.0);


void setup() {
  Serial.begin(115200);
  stepMotor1.init();
}

void loop() {

  if (millis() - t0 < 2000){
    stepMotor1.moveMotor(cmdSpeed);
  }
  else{
    stepMotor1.moveMotor(0);
    delay(1000);
    direction *=-1;
    t0 = millis();

    if (cmdSpeed < 3000) {
      cmdSpeed = (cmdSpeed)*-1;
    }
  }
}