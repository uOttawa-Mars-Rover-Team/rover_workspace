/*
 * Standalone demo: one camera mount (pan + tilt) via TaskServo.
 * Serial @ 115200 — send word commands while holding a key on the host:
 *   svu / svd  tilt up/down
 *   svl / svr  pan left/right
 *   svs        stop both axes
 * Or semicolon payload: "1;-1" (pan right, tilt down)
 *
 * App-layer serial routing lands in a later branch; this main is for
 * hardware smoke-testing the driver + task layers in isolation.
 */
#include <Arduino.h>
#include "DriverServo.h"
#include "TaskServo.h"

#define BAUDRATE            115200
#define DEFAULT_MS_PER_STEP 60   // legacy servo_delay

// Placeholder pins — replace with real wiring when confirmed.
#define PAN_SERVO_PIN       6
#define TILT_SERVO_PIN      7

DriverServo panServo;
DriverServo tiltServo;
TaskServo   cameraMount;

static char serialLine[32];
static uint8_t serialLen = 0;

static void drainSerial()
{
    while (Serial.available() > 0) {
        char c = static_cast<char>(Serial.read());
        if (c == '\n' || c == '\r') {
            if (serialLen > 0) {
                serialLine[serialLen] = '\0';

                if (strchr(serialLine, ';') != nullptr) {
                    cameraMount.parseMessage(serialLine, DEFAULT_MS_PER_STEP);
                } else {
                    cameraMount.parseWordCommand(serialLine, DEFAULT_MS_PER_STEP);
                }

                serialLen = 0;
            }
            continue;
        }

        if (serialLen < sizeof(serialLine) - 1) {
            serialLine[serialLen++] = c;
        }
    }
}

void setup()
{
    Serial.begin(BAUDRATE);

    panServo.init(PAN_SERVO_PIN);
    tiltServo.init(TILT_SERVO_PIN);
    cameraMount.init(&panServo, &tiltServo);

    Serial.println(F("TaskServo demo ready"));
    Serial.println(F("Commands: svu svd svl svr svs  or  1;-1"));
}

void loop()
{
    drainSerial();
    cameraMount.tick(millis());
}
