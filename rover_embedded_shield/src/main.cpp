/*
 * Bench keyboard demo (push / release) for TaskServo + DriverServo.
 *
 * Serial monitor @ 115200:
 *   Hold  w = tilt up     s = tilt down
 *   Hold  a = pan left    d = pan right
 *   Release the key       = stop that axis (hold in place)
 *
 * Serial Monitor does not send key-up events, so "release" is inferred:
 * if no press for that axis arrives within KEY_RELEASE_MS (key-repeat
 * keeps the axis moving while you hold), the axis stops.
 *
 * Hitting min/max still clamps and locks that axis (DriverServo end stop).
 * No 'x' stop key — release is the stop.
 */
#include <Arduino.h>
#include "DriverServo.h"
#include "TaskServo.h"

#define BAUDRATE        115200

#define PAN_PIN         6
#define TILT_PIN        7

#define MIN_DEG         0
#define MAX_DEG         180
#define START_DEG       90
#define STEP            2
#define STEP_DELAY      15

// How long after the last WASD char before we treat the key as released.
// OS key-repeat is typically ~30–50 ms; 80 ms is a safe gap.
#define KEY_RELEASE_MS  80

DriverServo panServo;
DriverServo tiltServo;
TaskServo   cameraMount;

static int8_t        panDir       = 0;
static int8_t        tiltDir      = 0;
static unsigned long lastPanKey   = 0;
static unsigned long lastTiltKey  = 0;
static unsigned long lastPrint    = 0;

static void handleKey(char c, unsigned long now)
{
    switch (c) {
        case 'w': case 'W':
            tiltDir     = 1;
            lastTiltKey = now;
            break;
        case 's': case 'S':
            tiltDir     = -1;
            lastTiltKey = now;
            break;
        case 'a': case 'A':
            panDir     = -1;
            lastPanKey = now;
            break;
        case 'd': case 'D':
            panDir     = 1;
            lastPanKey = now;
            break;
        default:
            break;  // ignore newlines / other keys (no 'x')
    }
}

static void applyRelease(unsigned long now)
{
    if (panDir != 0 && (now - lastPanKey) >= KEY_RELEASE_MS) {
        panDir = 0;
    }
    if (tiltDir != 0 && (now - lastTiltKey) >= KEY_RELEASE_MS) {
        tiltDir = 0;
    }
}

void setup()
{
    Serial.begin(BAUDRATE);

    panServo.init (PAN_PIN,  MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    tiltServo.init(TILT_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    cameraMount.init(&panServo, &tiltServo);

    Serial.println(F("=== Push/release servo bench ready ==="));
    Serial.println(F("Hold: w=up  s=down  a=left  d=right | release=stop"));
    Serial.println(F("End stops still clamp+lock at min/max."));
}

void loop()
{
    unsigned long now = millis();

    while (Serial.available() > 0) {
        handleKey((char)Serial.read(), now);
    }

    applyRelease(now);

    cameraMount.move(panDir, tiltDir);
    cameraMount.tick(now);

    if (now - lastPrint >= 500) {
        lastPrint = now;
        Serial.print(F("pan="));
        Serial.print(panServo.getCurrentDeg());
        Serial.print(F("  tilt="));
        Serial.println(tiltServo.getCurrentDeg());
    }
}
