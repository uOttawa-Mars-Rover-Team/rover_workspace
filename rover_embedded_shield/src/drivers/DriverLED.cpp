#include "DriverLED.h"
#include <Arduino.h>

void DriverLED::init(uint8_t pin) {
    pin_        = pin;
    state_      = false;
    brightness_ = 255;

    pinMode(pin_, OUTPUT);
    digitalWrite(pin_, LOW);
}

void DriverLED::on() {
    state_ = true;
    analogWrite(pin_, brightness_);

}

void DriverLED::off() {
    state_ = false;
    analogWrite(pin_, 0);

}

void DriverLED::toggle() {
    state_ ? off() : on();
}

void DriverLED::setBrightness(uint8_t value) {
    brightness_ = value;
    state_      = (value > 0);
    analogWrite(pin_, value);
}
