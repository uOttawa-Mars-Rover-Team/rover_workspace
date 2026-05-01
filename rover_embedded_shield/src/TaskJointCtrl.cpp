#include "TaskJointCtrl.h"

// Constructor: Initializes the 5 joint drivers with pins from your verified reference
// TaskJointCtrl::TaskJointCtrl() 
    // : tw("Tower",   55, 54, 16, 17,  5000, 1000000, 1000.0),
//       wp("Pitch",    4,  5,  3,  2, 10000, 1000000, 1000.0),
    //   wr("Roll",     8,  9,  7,  6, 20000, 1000000, 1000.0),
//       ee("EE",      12, 13, 11, 10, 20000, 1000000, 2500.0)
// {
// }

TaskJointCtrl::TaskJointCtrl() 
    : tw("Tower",   55, 54, 16, 17,  5000, 1000000, 1000.0),

      wp("Pitch",   8,  9, 16, 62, 20000, 1000000, WP_BASE_SPEED),
      wr("Roll",   10, 11,  5, 55, 20000, 1000000, WR_BASE_SPEED),
    //   wp("Pitch",    4,  5,  3,  2, 10000, 1000000, 1000.0),
    //   wr("Roll",     8,  9,  7,  6, 20000, 1000000, 1000.0),      
      ee("EE",     12, 13, 11, 10, 20000, 1000000, 2500.0) // Kept the "Working" EE pins
{
}


void TaskJointCtrl::init() {
    tw.init();
    wp.init();
    wr.init();
    ee.init();
}

bool TaskJointCtrl::MoveEE(int value) {
    return ee.moveMotor(value*EE_BASE_SPEED);
}

bool TaskJointCtrl::MoveTW(int value) {
    return tw.moveMotor(value*TW_BASE_SPEED);
}

bool TaskJointCtrl::MoveWR(int value) {
    return wr.moveMotor(value*WR_BASE_SPEED);
}

bool TaskJointCtrl::MoveWP(int value) {
    return wp.moveMotor(value*WP_BASE_SPEED);
}

void TaskJointCtrl::stopAll() {
    tw.moveMotor(0);
    wp.moveMotor(0);
    wr.moveMotor(0);
    ee.moveMotor(0);
}