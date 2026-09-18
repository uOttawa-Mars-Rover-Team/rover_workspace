#include "TaskJointControl.h"

TaskJointControl::TaskJointControl(uint8_t numJoints) {
    max_joints_ = numJoints;
    joints_ = new JointHandle[numJoints];
}

TaskJointControl::~TaskJointControl() {
    delete[] joints_;
}

void TaskJointControl::addStepper(DriverStepper* driver_stepper) {
    if (count_ < max_joints_) {
        joints_[count_].type = JointHandle::STEPPER;
        joints_[count_].stepper = driver_stepper;
        count_++;
    }
}

void TaskJointControl::addLA(DriverLA* driver_la) {
    if (count_ < max_joints_) {
        joints_[count_].type = JointHandle::LA;
        joints_[count_].la = driver_la;
        count_++;
    }
}

void TaskJointControl::JointHandle::setCommand(int8_t dir) {
    if (type == STEPPER) {
        stepper->moveMotor((float)dir * stepper->speed);
    } else if (type == LA) {
        la->moveMotor(400, dir);
    }
}

// Parse payload string: "0;1;-1;0;0;0"
// Each token maps to the joint registered at that index
void TaskJointControl::parseMessage(const char* payload) {
    // Copy payload because strtok modifies the string
    char buffer[64];
    strncpy(buffer, payload, sizeof(buffer));

    char* token = strtok(buffer, ";");
    uint8_t index = 0;

    while (token != NULL && index < count_) {
        int8_t command = atoi(token);
        joints_[index].setCommand(command);
        
        token = strtok(NULL, ";");
        index++;
    }
}

void TaskJointControl::init() {
    // Loop only through the steppers joints that were actually added (count_) and initialize them
    for (uint8_t i = 0; i < count_; i++) {
        if (joints_[i].type == JointHandle::STEPPER) {
            joints_[i].stepper->init();
        } 
    }
}

void TaskJointControl::update() {
    for (uint8_t i = 0; i < count_; i++) {
        if (joints_[i].type == JointHandle::STEPPER) {
            joints_[i].stepper->run();
        }
    }
}

void TaskJointControl::updateSteppers() {
    for (uint8_t i = 0; i < count_; i++) {
        if (joints_[i].type == JointHandle::STEPPER) {
            joints_[i].stepper->run();
        }
    }
}

void TaskJointControl::updateLA() {
    // LAs are fire-and-forget I2C, nothing to poll
    // but keep this here for future use
}

void TaskJointControl::stopAll() {
    for (uint8_t i = 0; i < count_; i++) {
        joints_[i].setCommand(0);
    }
}
