/*
 * Description: Single-axis servo driver for the rover_embedded_shield.
 *              Non-blocking ms-per-step state machine wrapping Arduino Servo.
 * Authors:
 */
//------------------------------------------
//  Includes
//------------------------------------------
#include "ArmDriver_Servo.h"
#include <Arduino.h>

//------------------------------------------
//  Global Defines
//------------------------------------------

//------------------------------------------
//  Datatype Definitions
//------------------------------------------

//------------------------------------------
//  Global Variables
//------------------------------------------

//------------------------------------------
//  Local Variables
//------------------------------------------

//------------------------------------------
//  Local Function Prototypes
//------------------------------------------
static uint8_t clampDeg(int16_t value, uint8_t lo, uint8_t hi);

//------------------------------------------
//  Global Functions Definitions
//------------------------------------------

/**
 * @brief Attach servo to PWM pin, latch bounds, and write initial position.
 *
 * @details If maxDeg < minDeg the bounds collapse to minDeg so currentDeg_
 * remains valid. The Servo library is told the pin first, then the seeded
 * angle is written so the physical horn is centered at boot.
 *
 * @return void
 */
void ArmDriver_Servo::init(uint8_t pwmPin,
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

/**
 * @brief Aim at an absolute angle.
 *
 * @details Clamps targetDeg to [minDeg_, maxDeg_], records the cadence, and
 * resets the step timer so the first step happens msPerStep ms from now. The
 * resulting state distinguishes "already there" (AT_TARGET / AT_LIMIT) from
 * "needs to move" (MOVING). AT_LIMIT takes priority when current == bound,
 * matching the state machine drawn in the plan.
 *
 * @return void
 */
void ArmDriver_Servo::setTarget(uint8_t targetDeg, uint16_t msPerStep)
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

/**
 * @brief Aim relative to currentDeg_ by a signed delta.
 *
 * @details Wraps setTarget() so all clamp / state-transition rules are
 * consistent. Implemented in int16_t to safely tolerate negative results.
 *
 * @return void
 */
void ArmDriver_Servo::incrementTarget(int16_t deltaDeg, uint16_t msPerStep)
{
    int16_t next = static_cast<int16_t>(currentDeg_) + deltaDeg;
    setTarget(clampDeg(next, minDeg_, maxDeg_), msPerStep);
}

/**
 * @brief Halt the state machine immediately.
 *
 * @details Servo holds at the current commanded angle. targetDeg_ is collapsed
 * to currentDeg_ so a subsequent tick() cannot resume motion accidentally.
 *
 * @return void
 */
void ArmDriver_Servo::stop()
{
    state_     = State::IDLE;
    targetDeg_ = currentDeg_;
}

/**
 * @brief Advance one 1-degree step toward targetDeg_ if the cadence allows.
 *
 * @details Early-returns when state_ is not MOVING or when fewer than
 * msPerStep_ ms have elapsed since lastStep_ms_, so the caller can invoke this
 * every loop iteration without thinking about timing. After a step is taken,
 * the state is updated to AT_LIMIT (hit a bound), AT_TARGET (reached target),
 * or remains MOVING.
 *
 * @return void
 */
void ArmDriver_Servo::tick(unsigned long now_ms)
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

uint8_t ArmDriver_Servo::getCurrentDeg() const
{
    return currentDeg_;
}

ArmDriver_Servo::State ArmDriver_Servo::getState() const
{
    return state_;
}

//------------------------------------------
//  Local Function Definition
//------------------------------------------
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
