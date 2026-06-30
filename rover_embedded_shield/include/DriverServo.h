#ifndef _DRIVER_SERVO_H_
#define _DRIVER_SERVO_H_

#include <stdint.h>
#include <Servo.h>

#define DRIVER_SERVO_DEFAULT_MIN_DEG    0
#define DRIVER_SERVO_DEFAULT_MAX_DEG    180
#define DRIVER_SERVO_DEFAULT_INIT_DEG   90

/**
 * Single-axis positional servo with non-blocking ms-per-step motion.
 * Port of the legacy svMoving / servo_delay loop in d_loop_motor.ino.
 */
class DriverServo
{
public:
    enum class State : uint8_t
    {
        IDLE,
        MOVING,
        AT_TARGET,
        AT_LIMIT
    };

    void init(uint8_t pwmPin,
              uint8_t minDeg     = DRIVER_SERVO_DEFAULT_MIN_DEG,
              uint8_t maxDeg     = DRIVER_SERVO_DEFAULT_MAX_DEG,
              uint8_t initialDeg = DRIVER_SERVO_DEFAULT_INIT_DEG);

    void setTarget(uint8_t targetDeg, uint16_t msPerStep);
    void incrementTarget(int16_t deltaDeg, uint16_t msPerStep);
    void stop();

    void tick(unsigned long now_ms);

    uint8_t getCurrentDeg() const;
    State   getState()      const;

private:
    Servo         servo_;
    uint8_t       pin_;
    uint8_t       minDeg_;
    uint8_t       maxDeg_;
    uint8_t       currentDeg_;
    uint8_t       targetDeg_;
    uint16_t      msPerStep_;
    unsigned long lastStep_ms_;
    State         state_;
};

#endif
