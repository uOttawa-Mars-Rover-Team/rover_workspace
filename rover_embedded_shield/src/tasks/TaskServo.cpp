#include "TaskServo.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>

void TaskServo::init(DriverServo* pan, DriverServo* tilt)
{
    pan_  = pan;
    tilt_ = tilt;
}

void TaskServo::move(int8_t panDir, int8_t tiltDir)
{
    if (pan_ != nullptr) {
        pan_->move(panDir);
    }
    if (tilt_ != nullptr) {
        tilt_->move(tiltDir);
    }
}

void TaskServo::parse(const char* msg)
{
    if (msg == nullptr) {
        return;
    }

    char buffer[16];
    strncpy(buffer, msg, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    int8_t panDir  = 0;
    int8_t tiltDir = 0;

    char* token = strtok(buffer, ";");
    if (token != nullptr) {
        panDir = (int8_t)atoi(token);
        token  = strtok(nullptr, ";");
    }
    if (token != nullptr) {
        tiltDir = (int8_t)atoi(token);
    }

    move(panDir, tiltDir);
}

void TaskServo::tick(unsigned long now_ms)
{
    if (pan_ != nullptr) {
        pan_->tick(now_ms);
    }
    if (tilt_ != nullptr) {
        tilt_->tick(now_ms);
    }
}

void TaskServo::stop()
{
    move(0, 0);
}

