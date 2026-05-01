#ifndef TASKJOINTCTRL_H
#define TASKJOINTCTRL_H

#include <Arduino.h>
#include "DriverStepper.h"

class TaskJointCtrl {
private:
    // One DriverStepper instance for each joint
    DriverStepper tw;
    DriverStepper wp;
    DriverStepper wr;
    DriverStepper ee;

    const float TW_BASE_SPEED = 1000.0;
    const float WP_BASE_SPEED = 1000.0;
    const float WR_BASE_SPEED = 1500.0;
    const float EE_BASE_SPEED = 2500.0;    

public:
    // Constructor initializes all 5 drivers with their specific pins/settings
    TaskJointCtrl();

    // Initialization method to call in setup()
    void init();

    // Joint movement methods
    bool MoveEE(int value);
    bool MoveTW(int value);
    bool MoveWR(int value);
    bool MoveWP(int value);
    bool MoveLA(int value);

    // Global stop
    void stopAll();
};

#endif