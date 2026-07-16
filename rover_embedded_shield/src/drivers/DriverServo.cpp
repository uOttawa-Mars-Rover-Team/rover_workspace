#include "DriverServo.h"
#include <Arduino.h>

void DriverServo::init(uint8_t  pwmPin,
                       uint8_t  minDeg,
                       uint8_t  maxDeg,
                       uint8_t  initialDeg,
                       uint8_t  stepSize,
                       uint16_t msPerStep)
{
    pin_         = pwmPin;
    minDeg_      = minDeg;
    maxDeg_      = (maxDeg >= minDeg) ? maxDeg : minDeg;
    stepSize_    = (stepSize == 0) ? 1 : stepSize;
    msPerStep_   = msPerStep;
    currentDeg_  = constrain(initialDeg, minDeg_, maxDeg_);
    lastStep_ms_ = 0;
    dir_         = 0;

    servo_.attach(pin_);
    servo_.write(currentDeg_);
}

void DriverServo::move(int8_t dir)
{
    if (dir > 0) {
        dir_ = 1;
    } else if (dir < 0) {
        dir_ = -1;
    } else {
        dir_ = 0;
    }
}

void DriverServo::tick(unsigned long now_ms)
{
    // Not moving: nothing to do.
    if (dir_ == 0) {
        return;
    }
    // Hold the direction until the per-step delay has elapsed.
    if ((now_ms - lastStep_ms_) < msPerStep_) {
        return;
    }
    lastStep_ms_ = now_ms;

    // Same fixed increment every time, in the current direction.
    int16_t next = (int16_t)currentDeg_ + (int16_t)dir_ * (int16_t)stepSize_;

    // If the step reaches or overshoots an end stop, snap to the endpoint
    // (final position) and lock: direction goes back to 0.
    if (next >= (int16_t)maxDeg_) {
        next = maxDeg_;
        dir_ = 0;
    } else if (next <= (int16_t)minDeg_) {
        next = minDeg_;
        dir_ = 0;
    }

    currentDeg_ = (uint8_t)next;
    servo_.write(currentDeg_);
}

