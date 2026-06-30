#include "TaskServo.h"
#include <Arduino.h>
#include <string.h>

static int8_t clampDir(int value)
{
    if (value > 0) {
        return 1;
    }
    if (value < 0) {
        return -1;
    }
    return 0;
}

static void applyDir(DriverServo* axis, int8_t dir, uint16_t msPerStep)
{
    if (axis == nullptr || dir == 0) {
        return;
    }
    axis->incrementTarget(dir, msPerStep);
}

void TaskServo::init(DriverServo* pan, DriverServo* tilt)
{
    pan_  = pan;
    tilt_ = tilt;
}

void TaskServo::parseMessage(const char* payload, uint16_t msPerStep)
{
    if (payload == nullptr) {
        return;
    }

    char buffer[32];
    strncpy(buffer, payload, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char* token = strtok(buffer, ";");
    if (token != nullptr) {
        applyDir(pan_, clampDir(atoi(token)), msPerStep);
        token = strtok(nullptr, ";");
    }
    if (token != nullptr) {
        applyDir(tilt_, clampDir(atoi(token)), msPerStep);
    }
}

void TaskServo::parseWordCommand(const char* cmd, uint16_t msPerStep)
{
    if (cmd == nullptr) {
        return;
    }

    if (strcmp(cmd, "svd") == 0) {
        applyDir(tilt_, -1, msPerStep);
    } else if (strcmp(cmd, "svu") == 0) {
        applyDir(tilt_, 1, msPerStep);
    } else if (strcmp(cmd, "svl") == 0) {
        applyDir(pan_, -1, msPerStep);
    } else if (strcmp(cmd, "svr") == 0) {
        applyDir(pan_, 1, msPerStep);
    } else if (strcmp(cmd, "svs") == 0) {
        stopAll();
    }
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

void TaskServo::stopAll()
{
    if (pan_ != nullptr) {
        pan_->stop();
    }
    if (tilt_ != nullptr) {
        tilt_->stop();
    }
}

void TaskServo::home(uint16_t msPerStep)
{
    if (pan_ != nullptr) {
        pan_->setTarget(DRIVER_SERVO_DEFAULT_INIT_DEG, msPerStep);
    }
    if (tilt_ != nullptr) {
        tilt_->setTarget(DRIVER_SERVO_DEFAULT_INIT_DEG, msPerStep);
    }
}

bool TaskServo::isIdle() const
{
    bool panIdle = (pan_ == nullptr)
        || pan_->getState() != DriverServo::State::MOVING;
    bool tiltIdle = (tilt_ == nullptr)
        || tilt_->getState() != DriverServo::State::MOVING;
    return panIdle && tiltIdle;
}
