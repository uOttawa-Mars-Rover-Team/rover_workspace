#include "DriverServo.h"
#include <Arduino.h>

static uint8_t clampDeg(int16_t value, uint8_t lo, uint8_t hi)
{
    if (value < static_cast<int16_t>(lo)) {
        return lo;
    }
    if (value > static_cast<int16_t>(hi)) {
        return hi;
    }
    return static_cast<uint8_t>(value);
}

void DriverServo::init(uint8_t pwmPin,
                       uint8_t minDeg,
                       uint8_t maxDeg,
                       uint8_t initialDeg)
{
    pin_         = pwmPin;
    minDeg_      = minDeg;
    maxDeg_      = (maxDeg >= minDeg) ? maxDeg : minDeg;
    currentDeg_  = clampDeg(initialDeg, minDeg_, maxDeg_);
    targetDeg_   = currentDeg_;
    msPerStep_   = 0;
    lastStep_ms_ = 0;
    state_       = State::IDLE;

    servo_.attach(pin_);
    servo_.write(currentDeg_);
}

void DriverServo::setTarget(uint8_t targetDeg, uint16_t msPerStep)
{
    targetDeg_   = clampDeg(static_cast<int16_t>(targetDeg), minDeg_, maxDeg_);
    msPerStep_   = msPerStep;
    lastStep_ms_ = millis();

    if (currentDeg_ != targetDeg_) {
        state_ = State::MOVING;
    } else if (currentDeg_ == minDeg_ || currentDeg_ == maxDeg_) {
        state_ = State::AT_LIMIT;
    } else {
        state_ = State::AT_TARGET;
    }
}

void DriverServo::incrementTarget(int16_t deltaDeg, uint16_t msPerStep)
{
    int16_t next = static_cast<int16_t>(currentDeg_) + deltaDeg;
    setTarget(clampDeg(next, minDeg_, maxDeg_), msPerStep);
}

void DriverServo::stop()
{
    state_     = State::IDLE;
    targetDeg_ = currentDeg_;
}

void DriverServo::tick(unsigned long now_ms)
{
    if (state_ != State::MOVING) {
        return;
    }
    if ((now_ms - lastStep_ms_) < msPerStep_) {
        return;
    }
    lastStep_ms_ = now_ms;

    if (currentDeg_ < targetDeg_) {
        currentDeg_++;
    } else if (currentDeg_ > targetDeg_) {
        currentDeg_--;
    }

    if (currentDeg_ <= minDeg_) {
        currentDeg_ = minDeg_;
        state_      = State::AT_LIMIT;
    } else if (currentDeg_ >= maxDeg_) {
        currentDeg_ = maxDeg_;
        state_      = State::AT_LIMIT;
    } else if (currentDeg_ == targetDeg_) {
        state_ = State::AT_TARGET;
    }

    servo_.write(currentDeg_);
}

uint8_t DriverServo::getCurrentDeg() const
{
    return currentDeg_;
}

DriverServo::State DriverServo::getState() const
{
    return state_;
}
