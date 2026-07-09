#ifndef APP_MSERVO_H
#define APP_MSERVO_H

#include <stdint.h>
#include "DriverServo.h"
#include "TaskServo.h"

/**
 * App-layer multi-servo handler for the GNC Mega.
 *
 * Owns three TaskServo mounts:
 *   A = 2-axis (pan + tilt)  — expects 2 velocity values
 *   B = 1-axis               — expects 1 velocity value
 *   C = 1-axis               — expects 1 velocity value
 *
 * Wire form (terminator '!' stripped by AppGNC before this is called):
 *   SV;<id>;<v0>[;v1]
 *   e.g. SV;A;-1;1   -> A pan toward min, A tilt toward max
 *        SV;B;1      -> B toward max
 *        SV;C;0      -> C stop (hold in place)
 *
 * Values are velocity directions {-1, 0, +1}. End stops still clamp+lock
 * inside DriverServo.
 */
class AppMServo
{
public:
    void init();
    void update();                          // call every AppGNC loop
    void handleMessage(const char* msg);    // full payload, no trailing '!'

private:
    static const uint8_t MAX_ENTRIES = 8;

    struct Entry {
        char       id;
        TaskServo* servo;
        uint8_t    axisCount;
    };

    Entry* find(char id);
    void   handleServoCmd(char* payload);   // mutable copy for strtok

    // Servo A: two axes
    DriverServo aPan_;
    DriverServo aTilt_;
    TaskServo   servoA_;

    // Servo B: one axis
    DriverServo bAxis_;
    TaskServo   servoB_;

    // Servo C: one axis
    DriverServo cAxis_;
    TaskServo   servoC_;

    Entry   entries_[MAX_ENTRIES];
    uint8_t count_;
};

#endif
