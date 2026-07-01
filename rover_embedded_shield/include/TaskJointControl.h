#ifndef TASKJOINTCONTROL_H
#define TASKJOINTCONTROL_H

#include <Arduino.h>
#include "DriverStepper.h"
#include "DriverLA.h"

class TaskJointControl {
public:
    // Constructor: User passes the number of joints here
    TaskJointControl(uint8_t numJoints);
    ~TaskJointControl();              // ← add this
    void addStepper(DriverStepper* stepper);
    void addLA(DriverLA* la);
    void parseMessage(const char* payload);
    void init();
    void update();
    void updateSteppers();
    void updateLA();
    void stopAll();

    struct JointHandle {
        enum Type { STEPPER, LA } type;
        union { 
            DriverStepper* stepper; 
            DriverLA* la; 
        };
        void setCommand(int8_t dir);
        void stop();
    };

    // Instead of a fixed array, we use a pointer
    JointHandle* joints_; 
    uint8_t      max_joints_;
    uint8_t      count_ = 0;
};

#endif
