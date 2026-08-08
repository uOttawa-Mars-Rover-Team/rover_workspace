#ifndef _TASK_SERVO_H_
#define _TASK_SERVO_H_

#include <stdint.h>
#include "DriverServo.h"

/**
 * One task servo = two DriverServo axes (pan + tilt) driven at the same time.
 *
 * move(pan, tilt) sets a velocity direction on each axis (each value in
 * {-1, 0, +1}); tick() then advances both axes on their own timers.
 * parse() accepts the wire form "pan;tilt" e.g. "-1;0".
 */
class TaskServo
{
public:
    void init(DriverServo* pan, DriverServo* tilt);

    // taskservo(-1, 0): pan toward min, tilt stop. Values clamped to {-1,0,1}.
    void move(int8_t panDir, int8_t tiltDir);

    // Wire form "pan;tilt", e.g. "-1;0".
    void parse(const char* msg);

    void tick(unsigned long now_ms);
    void stop();

private:
    DriverServo* pan_;
    DriverServo* tilt_;
};

#endif

