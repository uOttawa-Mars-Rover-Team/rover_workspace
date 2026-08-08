#include "TaskLED.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>

void TaskLED::init(DriverLED* a, DriverLED* b, DriverLED* c)
{
    leds_[0] = a;
    leds_[1] = b;
    leds_[2] = c;
}

void TaskLED::parse(const char* msg)
{
    if (msg == nullptr) {
        return;
    }

    char buffer[16];
    strncpy(buffer, msg, sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';

    char* idTok = strtok(buffer, ";");
    if (idTok == nullptr || idTok[0] == '\0') {
        return;
    }

    DriverLED* led = resolve(idTok[0]);
    if (led == nullptr) {
        return;
    }

    char* cmdTok = strtok(nullptr, ";");
    if (cmdTok == nullptr) {
        return;
    }

    if (strcmp(cmdTok, "on") == 0) {
        led->on();
    } else if (strcmp(cmdTok, "off") == 0) {
        led->off();
    } else if (strcmp(cmdTok, "toggle") == 0) {
        led->toggle();
    } else if (strcmp(cmdTok, "bright") == 0) {
        char* valTok = strtok(nullptr, ";");
        if (valTok != nullptr) {
            led->setBrightness((uint8_t)atoi(valTok));
        }
    }
}

void TaskLED::on(char id)
{
    DriverLED* led = resolve(id);
    if (led != nullptr) {
        led->on();
    }
}

void TaskLED::off(char id)
{
    DriverLED* led = resolve(id);
    if (led != nullptr) {
        led->off();
    }
}

void TaskLED::toggle(char id)
{
    DriverLED* led = resolve(id);
    if (led != nullptr) {
        led->toggle();
    }
}

void TaskLED::setBrightness(char id, uint8_t value)
{
    DriverLED* led = resolve(id);
    if (led != nullptr) {
        led->setBrightness(value);
    }
}

void TaskLED::allOff()
{
    for (uint8_t i = 0; i < 3; i++) {
        if (leds_[i] != nullptr) {
            leds_[i]->off();
        }
    }
}

DriverLED* TaskLED::resolve(char id) const
{
    switch (id) {
        case 'A': case 'a': return leds_[0];
        case 'B': case 'b': return leds_[1];
        case 'C': case 'c': return leds_[2];
        default:            return nullptr;
    }
}
