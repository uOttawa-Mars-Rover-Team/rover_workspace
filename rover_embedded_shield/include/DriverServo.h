#ifndef _DRIVER_SERVO_H_
#define _DRIVER_SERVO_H_
#include <stdint.h>
#include <Servo.h>

class DriverServo
{
public:
    void init(uint8_t  pwmPin,
              uint8_t  minDeg,
              uint8_t  maxDeg,
              uint8_t  initialDeg,
              uint8_t  stepSize,
              uint16_t msPerStep);

    // Public members needed by TaskButton and AppMorseServo
    Servo         servo_;
    uint8_t       pin_;
    uint8_t       stepSize_;
    uint16_t      msPerStep_;
    uint8_t       currentDeg_;

    void detachServo() { servo_.detach(); }
    void attachServo() { servo_.attach(pin_); servo_.write(currentDeg_); }

    void move(int8_t dir);
    void tick(unsigned long now_ms);

    bool isMoving() const { return dir_ != 0; }
    bool atLimit()  const { return currentDeg_ == minDeg_ || currentDeg_ == maxDeg_; }

private:
    uint8_t       minDeg_;
    uint8_t       maxDeg_;
    unsigned long lastStep_ms_;
    int8_t        dir_;
};
#endif
