#ifndef _TASK_SERVO_H_
#define _TASK_SERVO_H_

#include <stdint.h>
#include "DriverServo.h"

/**
 * Links two DriverServo instances (pan + tilt) for one camera mount.
 * Upper layers talk to one mount instead of two separate servos.
 */
class TaskServo
{
public:
    void init(DriverServo* pan, DriverServo* tilt);

    // Payload "1;-1" -> pan +1 deg/step, tilt -1 deg/step (values clamped to {-1,0,1})
    void parseMessage(const char* payload, uint16_t msPerStep = 60);

    // Legacy word commands: svu, svd, svl, svr, svs
    void parseWordCommand(const char* cmd, uint16_t msPerStep = 60);

    void tick(unsigned long now_ms);
    void stopAll();
    void home(uint16_t msPerStep = 60);

    bool isIdle() const;

private:
    DriverServo* pan_;
    DriverServo* tilt_;
};

#endif
