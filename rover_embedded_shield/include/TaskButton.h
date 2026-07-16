#pragma once
#include <Arduino.h>
#include <Servo.h>

class TaskButton {
public:

    void begin(uint8_t pin, uint8_t restDeg, uint8_t pressDeg,
               uint8_t stepDeg, uint16_t msPerStep) {
        pin_       = pin;
        restDeg_   = restDeg;
        pressDeg_  = pressDeg;
        stepDeg_   = stepDeg;
        msPerStep_ = msPerStep;
        currentDeg_ = restDeg_;
        servo_.attach(pin_);
        servo_.write(currentDeg_);
    }

    void enable()  { disabled_ = false; }
    void disable() { disabled_ = true;  }  // call when morse takes over
    bool isDisabled() const { return disabled_; }

    // press → hold 100ms → release
    void tap() {
        if (disabled_ || state_ != IDLE) return;
        holdMs_ = 100;
        autoRelease_ = true;
        startSweep(pressDeg_);
        state_ = PRESSING;
    }

    // press → hold for ms → release
    void press(uint16_t holdMs) {
        if (disabled_ || state_ != IDLE) return;
        holdMs_ = holdMs;
        autoRelease_ = true;
        startSweep(pressDeg_);
        state_ = PRESSING;
    }

    // press and hold indefinitely until releaseUp()
    void holdDown() {
        if (disabled_ || state_ != IDLE) return;
        autoRelease_ = false;
        startSweep(pressDeg_);
        state_ = PRESSING;
    }

    // release from indefinite hold
    void releaseUp() {
        if (disabled_ || state_ != HELD) return;
        startSweep(restDeg_);
        state_ = RELEASING;
    }

    bool isIdle() const { return state_ == IDLE; }

    // call every loop()
    void update() {
        unsigned long now = millis();

        // ── servo step ───────────────────────────────────────────────────────
        if (sweeping_) {
            if (now - lastStep_ >= msPerStep_) {
                lastStep_ = now;

                if (currentDeg_ < targetDeg_)
                    currentDeg_ = min((int)currentDeg_ + stepDeg_, (int)targetDeg_);
                else if (currentDeg_ > targetDeg_)
                    currentDeg_ = max((int)currentDeg_ - stepDeg_, (int)targetDeg_);

                servo_.write(currentDeg_);

                if (currentDeg_ == targetDeg_) {
                    sweeping_ = false;
                    arrivalTime_ = now;
                }
            }
        }

        // ── state machine ────────────────────────────────────────────────────
        switch (state_) {

            case PRESSING:
                if (!sweeping_) {
                    // arrived at pressDeg
                    if (autoRelease_) {
                        state_ = HOLDING;
                    } else {
                        state_ = HELD;
                    }
                }
                break;

            case HOLDING:
                if (now - arrivalTime_ >= holdMs_) {
                    startSweep(restDeg_);
                    state_ = RELEASING;
                }
                break;

            case HELD:
                // waiting for releaseUp()
                break;

            case RELEASING:
                if (!sweeping_) {
                    state_ = IDLE;
                }
                break;

            case IDLE:
                break;
        }
    }

private:
    Servo    servo_;
    uint8_t  pin_        = 6;
    uint8_t  restDeg_    = 160;
    uint8_t  pressDeg_   = 20;
    uint8_t  stepDeg_    = 15;
    uint16_t msPerStep_  = 10;
    uint8_t  currentDeg_ = 160;
    uint8_t  targetDeg_  = 160;

    bool          sweeping_     = false;
    unsigned long lastStep_     = 0;
    unsigned long arrivalTime_  = 0;
    uint16_t      holdMs_       = 100;
    bool          autoRelease_  = true;
    bool          disabled_     = false;

    enum State { IDLE, PRESSING, HOLDING, HELD, RELEASING };
    State state_ = IDLE;

    void startSweep(uint8_t target) {
        targetDeg_ = target;
        sweeping_  = true;
        lastStep_  = millis();
    }
};

