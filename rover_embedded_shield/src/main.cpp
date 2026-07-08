/*
 * Two-axis (pan + tilt) interactive control via the TaskServo module.
 *
 * This exercises the whole mservo module: TaskServo coordinating two
 * DriverServo axes (pan on pin 6, tilt on pin 7).
 *
 * Serial monitor @ 115200, press keys:
 *
 *   w -> tilt up        s -> tilt down
 *   a -> pan  left      d -> pan  right
 *   x -> stop both      (freezes in place, does NOT return to any position)
 *
 * Each axis holds its last direction until you change it. The only preset
 * position is START_DEG, written once at power-on.
 */
#include <Arduino.h>
#include "DriverServo.h"
#include "TaskServo.h"

#define BAUDRATE     115200

#define PAN_PIN      6
#define TILT_PIN     7

#define MIN_DEG      0
#define MAX_DEG      180
#define START_DEG    90     // power-on position only; never returned to
#define STEP         2      // ramp smoothness
#define STEP_DELAY   15     // ms between increments = ramp speed

DriverServo panServo;
DriverServo tiltServo;
TaskServo   cameraMount;

static int8_t        panDir    = 0;   // -1 left, +1 right, 0 stop
static int8_t        tiltDir   = 0;   // -1 down, +1 up,    0 stop
static unsigned long lastPrint = 0;

static void handleKey(char c)
{
    switch (c) {
        case 'w': case 'W':
            tiltDir = 1;
            Serial.println(F(">> TILT up"));
            break;
        case 's': case 'S':
            tiltDir = -1;
            Serial.println(F(">> TILT down"));
            break;
        case 'a': case 'A':
            panDir = -1;
            Serial.println(F(">> PAN left"));
            break;
        case 'd': case 'D':
            panDir = 1;
            Serial.println(F(">> PAN right"));
            break;
        case 'x': case 'X':
            panDir  = 0;
            tiltDir = 0;
            Serial.println(F(">> STOP both (hold in place)"));
            break;
        default:
            break;       // ignore newlines / other keys
    }
}

void setup()
{
    Serial.begin(BAUDRATE);

    //             pin       min      max      start      step   delay
    panServo.init (PAN_PIN,  MIN_DEG, MAX_DEG, START_DEG, STEP,  STEP_DELAY);
    tiltServo.init(TILT_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP,  STEP_DELAY);
    cameraMount.init(&panServo, &tiltServo);

    Serial.println(F("=== Two-axis servo control ready ==="));
    Serial.println(F("Keys:  w=up  s=down  a=left  d=right  x=stop"));
}

void loop()
{
    unsigned long now = millis();

    while (Serial.available() > 0) {
        handleKey((char)Serial.read());
    }

    // Push the held directions to both axes, then advance them.
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
