#include "AppGNC.h"
#include "DriverServo.h"
#include "TaskServo.h"
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

// ============================================================
// GNC Mega — terminator '!'
// Serial  (USB)  : debug + commands @ 115200
// Serial1        : inter-board     @ 115200
//
//   SV;A;-1;1!   servo A (2-axis): pan -1, tilt +1  (keeps moving until 0)
//   SV;B;1!      servo B (1-axis)
//   SV;C;0!      servo C stop
//   GNC;move;1! / GNC;move;-1! / GNC;stop! / GNC;update!
// ============================================================

#define A_PAN_PIN  6
#define A_TILT_PIN 7
#define B_PIN      8
#define C_PIN      9

#define MIN_DEG    0
#define MAX_DEG    180
#define START_DEG  90
#define STEP       2
#define STEP_DELAY 15

// --- serial buffers (USB + Serial1) ---
static char    bufUsb[64];
static uint8_t bufUsbIdx   = 0;
static bool    msgUsbReady = false;

static char    bufBoard[64];
static uint8_t bufBoardIdx   = 0;
static bool    msgBoardReady = false;

// --- GNC chassis stubs ---
static int8_t   currentDir   = 0;
static uint32_t lastMoveTime = 0;

// --- servos A (2-axis), B (1-axis), C (1-axis) ---
static DriverServo aPan, aTilt, bAxis, cAxis;
static TaskServo   servoA, servoB, servoC;

static void feedPort(HardwareSerial& port, char* buf, uint8_t& idx, bool& ready);
static void handleMessage(const char* msg);
static void handleSV(char* msg);   // mutable copy for strtok
static void sendUpdate();

static int8_t clampDir(int v)
{
    if (v > 0) return 1;
    if (v < 0) return -1;
    return 0;
}

void appGNC_setup()
{
    Serial.begin(115200);
    Serial1.begin(115200);

    aPan.init (A_PAN_PIN,  MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    aTilt.init(A_TILT_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoA.init(&aPan, &aTilt);

    bAxis.init(B_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoB.init(&bAxis, nullptr);

    cAxis.init(C_PIN, MIN_DEG, MAX_DEG, START_DEG, STEP, STEP_DELAY);
    servoC.init(&cAxis, nullptr);

    Serial.println(F("[GNC] Online. SV;A|B|C;...! or GNC;...! on Serial/Serial1"));
}

void appGNC_loop()
{
    feedPort(Serial,  bufUsb,   bufUsbIdx,   msgUsbReady);
    feedPort(Serial1, bufBoard, bufBoardIdx, msgBoardReady);

    if (msgUsbReady) {
        msgUsbReady = false;
        Serial.print(F("[GNC] USB: "));
        Serial.println(bufUsb);
        handleMessage(bufUsb);
    }
    if (msgBoardReady) {
        msgBoardReady = false;
        Serial.print(F("[GNC] Serial1: "));
        Serial.println(bufBoard);
        handleMessage(bufBoard);
    }

    unsigned long now = millis();
    servoA.tick(now);
    servoB.tick(now);
    servoC.tick(now);
}

static void feedPort(HardwareSerial& port, char* buf, uint8_t& idx, bool& ready)
{
    while (port.available()) {
        char c = port.read();
        if (c == '!') {
            buf[idx] = '\0';
            idx = 0;
            ready = true;
            return;
        } else if (c == '\n' || c == '\r') {
            // ignore
        } else if (idx < 63) {
            buf[idx++] = c;
        } else {
            idx = 0;
        }
    }
}

static void handleMessage(const char* msg)
{
    if (strncmp(msg, "SV;", 3) == 0) {
        char copy[64];
        strncpy(copy, msg, sizeof(copy) - 1);
        copy[sizeof(copy) - 1] = '\0';
        handleSV(copy);
        return;
    }

    if (strncmp(msg, "GNC;", 4) != 0) {
        Serial.println(F("[GNC] Ignored"));
        return;
    }

    const char* payload = msg + 4;

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
        Serial1.print("GNC;error;unknown;");
        Serial1.print(payload);
        Serial1.print('!');
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
    Serial1.print(reply);
    Serial1.print('!');
    Serial.print(F("[GNC] Sent: "));
    Serial.println(reply);
    (void)lastMoveTime;
}
