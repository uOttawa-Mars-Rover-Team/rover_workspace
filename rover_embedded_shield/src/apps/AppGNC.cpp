#include "AppGNC.h"
#include "AppMServo.h"
#include <Arduino.h>
#include <string.h>
#include <stdio.h>

// ============================================================
// GNC (slave) Mega, terminator is '!'
// ------------------------------------------------------------
// Serial  (USB, pin 0/1)  : debug terminal + SV bench  @ 115200
// Serial1      (pin 18/19): inter-board link           @ 115200
//
// Message formats (accepted on BOTH Serial and Serial1):
//   "GNC;move;1!"     -> move forward
//   "GNC;move;-1!"    -> move reverse
//   "GNC;stop!"       -> stop
//   "GNC;update!"     -> reply with status back to RA Mega
//   "SV;A;-1;1!"      -> multi-servo velocity (see AppMServo)
//   "SV;B;1!"         -> 1-axis servo B
//   "SV;C;0!"         -> stop servo C
// ============================================================

static char    bufUsb[64];
static uint8_t bufUsbIdx   = 0;
static bool    msgUsbReady = false;

static char    bufBoard[64];
static uint8_t bufBoardIdx   = 0;
static bool    msgBoardReady = false;

static int8_t   currentDir   = 0;
static uint32_t lastMoveTime = 0;

static AppMServo mservo;

static void feedPort(HardwareSerial& port,
                     char* buf, uint8_t& idx, bool& readyFlag);
static void handleMessage(const char* msg, const char* source);
static void sendUpdate();
static void doWork();

void appGNC_setup() {
    Serial.begin(115200);    // USB debug + SV bench
    Serial1.begin(115200);   // inter-board link (pins 18/19)

    mservo.init();

    Serial.println(F("[GNC] Online."));
    Serial.println(F("[GNC] Accepts GNC;...! and SV;...! on Serial (USB) and Serial1."));
}

void appGNC_loop() {
    // 1. Accumulate chars from USB (Serial) and RA Mega (Serial1)
    feedPort(Serial,  bufUsb,   bufUsbIdx,   msgUsbReady);
    feedPort(Serial1, bufBoard, bufBoardIdx, msgBoardReady);

    // 2. Handle completed messages
    if (msgUsbReady) {
        msgUsbReady = false;
        Serial.print(F("[GNC] USB: "));
        Serial.println(bufUsb);
        handleMessage(bufUsb, "USB");
    }
    if (msgBoardReady) {
        msgBoardReady = false;
        Serial.print(F("[GNC] Serial1: "));
        Serial.println(bufBoard);
        handleMessage(bufBoard, "Serial1");
    }

    // 3. Tick multi-servo axes + other autonomous work
    mservo.update();
    doWork();
}

static void feedPort(HardwareSerial& port,
                     char* buf, uint8_t& idx, bool& readyFlag)
{
    while (port.available()) {
        char c = port.read();
        if (c == '!') {
            buf[idx] = '\0';
            idx = 0;
            readyFlag = true;
            return;  // one complete message per call; rest next loop
        } else if (c == '\n' || c == '\r') {
            // ignore stray line-ending bytes
        } else if (idx < 63) {
            buf[idx++] = c;
        } else {
            idx = 0;  // overflow: drop malformed message
        }
    }
}

static void handleMessage(const char* msg, const char* /*source*/) {
    // ---- SV -> AppMServo (multi-servo velocity) ----
    if (strncmp(msg, "SV;", 3) == 0) {
        mservo.handleMessage(msg);
        return;
    }

    // ---- GNC -> existing chassis/status handlers ----
    if (strncmp(msg, "GNC;", 4) != 0) {
        Serial.println(F("[GNC] Ignored (not GNC; or SV;)"));
        return;
    }

    const char* payload = msg + 4;   // skip "GNC;"

    if (strncmp(payload, "move;1", 6) == 0) {
        currentDir   = 1;
        lastMoveTime = millis();
        Serial.println(F("[GNC] Moving forward"));
        // TODO: start actuator here
    } else if (strncmp(payload, "move;-1", 7) == 0) {
        currentDir   = -1;
        lastMoveTime = millis();
        Serial.println(F("[GNC] Moving reverse"));
        // TODO: start actuator here
    } else if (strncmp(payload, "stop", 4) == 0) {
        currentDir = 0;
        Serial.println(F("[GNC] Stopped"));
        // TODO: stop actuator here
    } else if (strncmp(payload, "update", 6) == 0) {
        Serial.println(F("[GNC] Sending update to RA..."));
        sendUpdate();
    } else {
        Serial.print(F("[GNC] Unknown payload: "));
        Serial.println(payload);
        Serial1.print("GNC;error;unknown;");
        Serial1.print(payload);
        Serial1.print('!');
    }
}

static void sendUpdate() {
    char reply[64];
    snprintf(reply, sizeof(reply),
        "GNC;status;dir=%d;uptime=%lums",
        currentDir, millis());
    Serial1.print(reply);
    Serial1.print('!');
    Serial.print(F("[GNC] Sent: "));
    Serial.println(reply);
}

static void doWork() {
    // Autonomous work here — runs every loop regardless of comms
    (void)lastMoveTime;
}
