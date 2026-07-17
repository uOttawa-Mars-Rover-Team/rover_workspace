#ifndef _DRIVER_SERVO_H_
#define _DRIVER_SERVO_H_

#include <stdint.h>
#include <Servo.h>

/**
 * Single servo axis driven as a velocity.
 *
 * Port of the legacy svMoving / servo_delay loop in d_loop_motor.ino, turned
 * into the "velocity system" the original TODO asked for: move() just sets a
 * direction, and every `msPerStep` the axis increments by a fixed step until
 * it reaches an end stop, where it clamps to the limit and locks (stops).
 *
 * The endpoints, step size ("speed") and per-step delay are fixed at init;
 * that is the driver definition. The object is then driven with move(-1/0/+1).
 */
class DriverServo
{
public:
    void init(uint8_t  pwmPin,
              uint8_t  minDeg,
              uint8_t  maxDeg,
              uint8_t  initialDeg,
              uint8_t  stepSize,
              uint16_t msPerStep);

    // dir: -1 = toward min (left/down), +1 = toward max (right/up), 0 = stop.
    void move(int8_t dir);

    // Call every loop(): performs one increment once the delay has elapsed.
    void tick(unsigned long now_ms);

    uint8_t getCurrentDeg() const { return currentDeg_; }
    bool    isMoving()      const { return dir_ != 0; }
    bool    atLimit()       const { return currentDeg_ == minDeg_ || currentDeg_ == maxDeg_; }

private:
    Servo         servo_;
    uint8_t       pin_;
    uint8_t       minDeg_;
    uint8_t       maxDeg_;
    uint8_t       currentDeg_;
    uint8_t       stepSize_;
    uint16_t      msPerStep_;
    unsigned long lastStep_ms_;
    int8_t        dir_;
};

#endif

