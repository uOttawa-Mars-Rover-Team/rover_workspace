#ifndef DRIVER_LED_H
#define DRIVER_LED_H

#include <stdint.h>

/**
 * GPIO-based LED control with optional PWM brightness.
 *
 * On a PWM pin, brightness sets the current driven to the LED (0-255).
 * on()/off()/toggle() drive the pin at the last brightness set via
 * setBrightness() (255 if never set) or at 0; the brightness value itself
 * is preserved across off()/on() cycles.
 */
class DriverLED {
public:
    void init(uint8_t pin);

    void on();
    void off();
    void toggle();

    void setBrightness(uint8_t value);   // 0-255, PWM pins only

    bool getState() const { return state_; }

private:
    uint8_t pin_;

    bool    state_;
    uint8_t brightness_;
};

#endif
