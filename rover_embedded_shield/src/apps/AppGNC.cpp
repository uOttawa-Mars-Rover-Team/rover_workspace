#include "AppGNC.h"
#include "DriverServo.h"
#include "TaskServo.h"
#include "DriverLED.h"
#include "TaskLED.h"
#include "CommSerial.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ============================================================
// GNC Mega — terminator '!'
//
// Normal (APP_GNC):
//   Serial (RX0/TX0) : commands + debug @ 9600
//
// Debug (APP_GNC_DEBUG):
//   Serial1 (RX1/TX1) : commands (from RA Mega or USB-serial)
//   Serial  (RX0/TX0) : debug output to USB Serial Monitor
//
//   SV;A;-1;1!   servo A (2-axis): pan -1, tilt +1
//   SV;B;1!      servo B (1-axis)
//   SV;C;0!      servo C stop
//   SV;D;1!      servo D (1-axis)
//   LED;A;on!  / LED;A;off! / LED;A;toggle! / LED;A;bright;180!
//   GNC;move;1! / GNC;move;-1! / GNC;stop! / GNC;update!
// ============================================================

#ifdef APP_GNC_DEBUG
    #define CMD_SERIAL Serial1   // receives commands
#else
    #define CMD_SERIAL Serial    // receives commands
#endif
// Serial (USB) always used for debug prints regardless of mode


#define LED_A_PIN  46
#define LED_B_PIN  45
#define LED_C_PIN  44
#define A_PAN_PIN  8
#define A_TILT_PIN 9
#define B_PAN_PIN  5
#define B_TILT_PIN 4
#define C_PIN      7

#define MIN_DEG    0
#define MAX_DEG    180
#define START_DEG  180
#define STEP       2
#define STEP_DELAY 30

// --- serial buffer ---
static char    buf[64];
static uint8_t bufIdx = 0;

// --- GNC chassis state ---
static int8_t   currentDir   = 0;
static uint32_t lastMoveTime = 0;

// --- servos ---
static DriverServo aPan, aTilt, bPan, bTilt, cAxis, dAxis;
static TaskServo   servoA, servoB, servoC, servoD;

// --- LEDs ---
static DriverLED ledA, ledB, ledC;
static TaskLED   ledTask;

static void handleSV(char* msg);
static void handleLED(char* msg);
static void sendUpdate();
static void appGNC_handleGNC(char* payload);
static void handleGNCLight(char* payload);
static void pollSerialCommand();

static CommSerial commsGNC(CMD_SERIAL, 9600, "GNC;", appGNC_handleGNC);

static int8_t clampDir(int v) {
    if (v > 0) return  1;
    if (v < 0) return -1;
    return 0;
}

// ── Setup ─────────────────────────────────────────────────────────────────────

void appGNC_setup()
{
    Serial.begin(9600);          // debug output always on USB

#ifdef APP_GNC_DEBUG
    CMD_SERIAL.begin(9600);      // Serial1 for commands in debug mode
    Serial.println(F("[GNC] DEBUG mode — commands on Serial1, debug on Serial0"));
#else
    Serial.println(F("[GNC] Online. SV;A|B|C;...! or GNC;...!"));
#endif

    commsGNC.init();

    aPan.init (A_PAN_PIN,  MIN_DEG, MAX_DEG, 40, STEP, STEP_DELAY);
    aTilt.init(A_TILT_PIN, MIN_DEG, MAX_DEG, 40, STEP, STEP_DELAY);
    servoA.init(&aPan, &aTilt);

    bPan.init(B_PAN_PIN, MIN_DEG, MAX_DEG, 40, STEP, STEP_DELAY);
    bTilt.init(B_TILT_PIN, MIN_DEG, MAX_DEG, 40, STEP, STEP_DELAY);
    servoB.init(&bPan, &bTilt);

    cAxis.init(C_PIN, MIN_DEG, MAX_DEG, 40, STEP, STEP_DELAY);
    servoC.init(&cAxis, nullptr);

    ledA.init(LED_A_PIN);
    ledB.init(LED_B_PIN);
    ledC.init(LED_C_PIN);
    ledTask.init(&ledA, &ledB, &ledC);
}

// ── Loop ──────────────────────────────────────────────────────────────────────

void appGNC_loop()
{
    pollSerialCommand();

    unsigned long now = millis();
    servoA.tick(now);
    servoB.tick(now);
    servoC.tick(now);
}

// ── Serial poll — reads from CMD_SERIAL, prints debug to Serial ───────────────

static void pollSerialCommand()
{
    while (CMD_SERIAL.available() > 0) {
        char c = CMD_SERIAL.read();
        if (c == '!' || c == '\n' || c == '\r') {
            if (bufIdx > 0) {
                buf[bufIdx] = '\0';
                bufIdx = 0;

                Serial.print(F("[GNC] RX: "));
                Serial.println(buf);

                if (strncmp(buf, "SV;", 3) == 0) {
                    char copy[64];
                    strncpy(copy, buf, sizeof(copy) - 1);
                    copy[sizeof(copy) - 1] = '\0';
                    handleSV(copy);
                } else if (strncmp(buf, "LED;", 4) == 0) {
                    char copy[64];
                    strncpy(copy, buf, sizeof(copy) - 1);
                    copy[sizeof(copy) - 1] = '\0';
                    handleLED(copy);
                } else {
                    commsGNC.handleMessage(buf);
                }
            }
        } else if (bufIdx < sizeof(buf) - 1) {
            buf[bufIdx++] = c;
        } else {
            bufIdx = 0;
            Serial.println(F("[GNC] Command too long, discarded"));
        }
    }
}


static void appGNC_handleGNC(char* payload)
{
    if (strncmp(payload, "move;1", 6) == 0) {
        currentDir = 1;
        lastMoveTime = millis();
        Serial.println(F("[GNC] Moving forward"));
    } else if (strncmp(payload, "move;-1", 7) == 0) {
        currentDir = -1;
        lastMoveTime = millis();
        Serial.println(F("[GNC] Moving reverse"));
    } else if (strncmp(payload, "stop", 4) == 0) {
        currentDir = 0;
        Serial.println(F("[GNC] Stopped"));
    } else if (strncmp(payload, "update", 6) == 0) {
        sendUpdate();
    } else if ((payload[0] == 'L' || payload[0] == 'l' ||
                payload[0] == 'M' || payload[0] == 'm' ||
                payload[0] == 'R' || payload[0] == 'r' ||
                payload[0] == 'O' || payload[0] == 'o') && payload[1] == ';') {
        handleGNCLight(payload);
    } else {
        Serial.print(F("[GNC] Unknown: "));
        Serial.println(payload);
        CMD_SERIAL.print(F("GNC;error;unknown;"));
        CMD_SERIAL.print(payload);
        CMD_SERIAL.print('!');
    }
}

// ── SV handler ────────────────────────────────────────────────────────────────

static void handleSV(char* msg)
{
    strtok(msg, ";");
    char* idTok = strtok(nullptr, ";");
    if (idTok == nullptr || idTok[0] == '\0') {
        Serial.println(F("[GNC] SV: missing id"));
        return;
    }

    char id = idTok[0];
    TaskServo* servo = nullptr;
    uint8_t axes = 1;

    if      (id == 'A' || id == 'a') { servo = &servoA; axes = 2; }
    else if (id == 'B' || id == 'b') { servo = &servoB; axes = 2; }
    else if (id == 'C' || id == 'c') { servo = &servoC; }
    else {
        Serial.print(F("[GNC] SV: unknown id "));
        Serial.println(id);
        return;
    }

    int8_t d0 = 0, d1 = 0;
    char* v0 = strtok(nullptr, ";");
    if (v0) d0 = clampDir(atoi(v0));
    if (axes == 2) {
        char* v1 = strtok(nullptr, ";");
        if (v1) d1 = clampDir(atoi(v1));
    }

    servo->move(d0, d1);

    Serial.print(F("[GNC] SV "));
    Serial.print(id);
    Serial.print(F(" "));
    Serial.print(d0);
    if (axes == 2) { Serial.print(F(";")); Serial.print(d1); }
    Serial.println();
}

// ── LED handler ───────────────────────────────────────────────────────────────

static void handleLED(char* msg)
{
    strtok(msg, ";");   // discard "LED" token
    char* payload = strtok(nullptr, "");
    if (payload == nullptr) {
        Serial.println(F("[GNC] LED: missing payload"));
        return;
    }

    ledTask.parse(payload);

    Serial.print(F("[GNC] LED "));
    Serial.println(payload);
}

// ── GNC light handler ─────────────────────────────────────────────────────────
// Payload forms (prefix "GNC;" already stripped):
//   L;1        L;0        M;1  R;1  O;1        -> on/off
//   L;B;0.75   M;B;0.30   R;B;1.00  O;B;0.50    -> brightness 0.00–1.00
//   O = outer = Left + Right together (Middle untouched)

static void applyLightCmd(DriverLED& led, bool isBrightness, float brightVal, int onOff)
{
    if (isBrightness) {
        uint8_t b = (uint8_t)(brightVal * 255.0f + 0.5f);
        led.setBrightness(b);
    } else {
        if (onOff) led.on(); else led.off();
    }
}

static void handleGNCLight(char* payload)
{
    char* target = strtok(payload, ";");   // "L" "M" "R" "O"
    if (target == nullptr) {
        Serial.println(F("[GNC] Light: missing target"));
        return;
    }
    char t = target[0];

    char* next = strtok(nullptr, ";");
    if (next == nullptr) {
        Serial.println(F("[GNC] Light: missing value"));
        return;
    }

    bool  isBrightness = (next[0] == 'B' || next[0] == 'b');
    float brightVal = 0.0f;
    int   onOff = -1;

    if (isBrightness) {
        char* valTok = strtok(nullptr, ";");
        if (valTok == nullptr) {
            Serial.println(F("[GNC] Light: missing brightness value"));
            return;
        }
        brightVal = atof(valTok);
        if (brightVal < 0.0f) brightVal = 0.0f;
        if (brightVal > 1.0f) brightVal = 1.0f;
    } else {
        onOff = atoi(next);
    }

    switch (t) {
        case 'L': case 'l': applyLightCmd(ledA, isBrightness, brightVal, onOff); break;
        case 'M': case 'm': applyLightCmd(ledB, isBrightness, brightVal, onOff); break;
        case 'R': case 'r': applyLightCmd(ledC, isBrightness, brightVal, onOff); break;
        case 'O': case 'o':
            applyLightCmd(ledA, isBrightness, brightVal, onOff);   // Left
            applyLightCmd(ledC, isBrightness, brightVal, onOff);   // Right
            break;
        default:
            Serial.print(F("[GNC] Light: unknown target "));
            Serial.println(t);
            return;
    }

    Serial.print(F("[GNC] Light "));
    Serial.print(t);
    if (isBrightness) {
        Serial.print(F(" brightness="));
        Serial.println(brightVal, 2);
    } else {
        Serial.print(F(" state="));
        Serial.println(onOff);
    }
}
// ── Update reply ──────────────────────────────────────────────────────────────

static void sendUpdate()
{
    char reply[64];
    snprintf(reply, sizeof(reply),
             "GNC;status;dir=%d;uptime=%lums",
             currentDir, millis());
    CMD_SERIAL.print(reply);   // reply goes back on command port
    CMD_SERIAL.print('!');
    Serial.print(F("[GNC] Sent: "));
    Serial.println(reply);
    (void)lastMoveTime;
}
