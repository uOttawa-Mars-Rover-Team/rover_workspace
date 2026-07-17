#include "AppGNC.h"
#include "DriverServo.h"
#include "TaskServo.h"
#include "CommSerial.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ============================================================
// GNC Mega — terminator '!'
// Serial (RX0/TX0) : debug + commands + inter-board, all on one port @ 9600
//
//   SV;A;-1;1!   servo A (2-axis): pan -1, tilt +1  (keeps moving until 0)
//   SV;B;1!      servo B (1-axis)
//   SV;C;0!      servo C stop
//   SV;D;1!      servo D (1-axis)
//   GNC;move;1! / GNC;move;-1! / GNC;stop! / GNC;update!
// ============================================================

#define A_PAN_PIN  6
#define A_TILT_PIN 7
#define B_PIN      8
#define C_PIN      9
#define D_PIN      10

#define MIN_DEG    0
#define MAX_DEG    180
#define START_DEG  180
#define STEP       2
#define STEP_DELAY 15

// --- serial buffer (single port now: Serial / RX0-TX0) ---
static char    bufUsb[64];
static uint8_t bufUsbIdx   = 0;

// --- GNC chassis stubs ---
static int8_t   currentDir   = 0;
static uint32_t lastMoveTime = 0;

// --- servos A (2-axis), B (1-axis), C (1-axis), D (1-axis) ---
static DriverServo aPan, aTilt, bAxis, cAxis, dAxis;
static TaskServo   servoA, servoB, servoC, servoD;

static void handleSV(char* msg);   // mutable copy for strtok
static void sendUpdate();
static void appGNC_handleGNC(char* payload);
static void pollSerialCommand();
static CommSerial commsGNC(Serial, 9600, "GNC;", appGNC_handleGNC);

static int8_t clampDir(int v)
{
    if (v > 0) return 1;
    if (v < 0) return -1;
    return 0;
}

// CommSerial now wraps the single Serial (RX0/TX0) port, same pattern as AppRA

void appGNC_setup()
{
    Serial.begin(9600);
    commsGNC.init();

    aPan.init (A_PAN_PIN,  MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    aTilt.init(A_TILT_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoA.init(&aPan, &aTilt);

    bAxis.init(B_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoB.init(&bAxis, nullptr);

    cAxis.init(C_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoC.init(&cAxis, nullptr);

    dAxis.init(D_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoD.init(&dAxis, nullptr);

    Serial.println(F("[GNC] Online. SV;A|B|C|D;...! or GNC;...! on Serial"));
}

void appGNC_loop()
{
    pollSerialCommand();

    unsigned long now = millis();
    servoA.tick(now);
    servoB.tick(now);
    servoC.tick(now);
    servoD.tick(now);
}

// ── SERIAL POLL — single port, per-character accumulation, '!' terminator ──
static void pollSerialCommand()
{
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '!' || c == '\n' || c == '\r') {
            if (bufUsbIdx > 0) {
                bufUsb[bufUsbIdx] = '\0';
                bufUsbIdx = 0;

                Serial.print(F("[GNC] RX: "));
                Serial.println(bufUsb);

                if (strncmp(bufUsb, "SV;", 3) == 0) {
                    char copy[64];
                    strncpy(copy, bufUsb, sizeof(copy) - 1);
                    copy[sizeof(copy) - 1] = '\0';
                    handleSV(copy);
                } else {
                    commsGNC.handleMessage(bufUsb);   // strips "GNC;" and calls appGNC_handleGNC
                }
            }
        } else if (bufUsbIdx < sizeof(bufUsb) - 1) {
            bufUsb[bufUsbIdx++] = c;
        } else {
            bufUsbIdx = 0;
            Serial.println(F("[GNC] Command too long, discarded"));
        }
    }
}

// payload already has "GNC;" stripped by CommSerial
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
    } else {
        Serial.print(F("[GNC] Unknown: "));
        Serial.println(payload);
        Serial.print(F("GNC;error;unknown;"));
        Serial.print(payload);
        Serial.print('!');
    }
}

// SV;<id>;<v0>[;<v1>]  — convert string → TaskServo::move(); holds until 0
static void handleSV(char* msg)
{
    strtok(msg, ";");                    // "SV"
    char* idTok = strtok(nullptr, ";");
    if (idTok == nullptr || idTok[0] == '\0') {
        Serial.println(F("[GNC] SV: missing id"));
        return;
    }

    char id = idTok[0];
    TaskServo* servo = nullptr;
    uint8_t axes = 1;

    if (id == 'A' || id == 'a') {
        servo = &servoA;
        axes = 2;
    } else if (id == 'B' || id == 'b') {
        servo = &servoB;
    } else if (id == 'C' || id == 'c') {
        servo = &servoC;
    } else if (id == 'D' || id == 'd') {
        servo = &servoD;
    } else {
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
    if (axes == 2) {
        Serial.print(F(";"));
        Serial.print(d1);
    }
    Serial.println();
}

static void sendUpdate()
{
    char reply[64];
    snprintf(reply, sizeof(reply),
             "GNC;status;dir=%d;uptime=%lums",
             currentDir, millis());
    Serial.print(reply);
    Serial.print('!');
    Serial.print(F("[GNC] Sent: "));
    Serial.println(reply);
    (void)lastMoveTime;
}
