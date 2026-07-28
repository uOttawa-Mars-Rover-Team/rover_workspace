#ifndef _TASK_LED_H_
#define _TASK_LED_H_

#include <stdint.h>
#include "DriverLED.h"

/**
 * Groups the 3 GNC LED channels (A/B/C) behind one wire-parseable task.
 *
 * parse() accepts "id;cmd[;value]", e.g. "A;on", "B;off", "C;bright;180".
 * id is 'A'/'B'/'C' (case-insensitive); cmd is one of on/off/toggle/bright.
 */
class TaskLED
{
public:
    void init(DriverLED* a, DriverLED* b, DriverLED* c);

    // Wire form "id;cmd[;value]", e.g. "A;on", "C;bright;180".
    void parse(const char* msg);

    void on(char id);
    void off(char id);
    void toggle(char id);
    void setBrightness(char id, uint8_t value);

    void allOff();

private:
    DriverLED* leds_[3];

    DriverLED* resolve(char id) const;
};

#endif
