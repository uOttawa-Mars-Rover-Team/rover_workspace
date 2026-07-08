#include "AppGNC.h"
#include <Arduino.h>
#include <string.h>
#include <stdio.h>

// ============================================================
// GNC (slave) Mega, terminator is '!'
// ------------------------------------------------------------
// Serial  (USB, pin 0/1)  : debug terminal   @ 115200
// Serial1      (pin 18/19): inter-board link @ 115200
//
// Message format received on Serial1:
//   "GNC;move;1!"     -> move forward
//   "GNC;move;-1!"    -> move reverse
//   "GNC;stop!"       -> stop
//   "GNC;update!"     -> reply with status back to RA Mega
// ============================================================

static char    buf[64];
static uint8_t bufIdx   = 0;
static bool    msgReady = false;

static int8_t   currentDir   = 0;
static uint32_t lastMoveTime = 0;

static void handleMessage(const char* msg);
static void sendUpdate();
static void doWork();

void appGNC_setup() {
    Serial.begin(115200);    // USB debug
    Serial1.begin(115200);   // inter-board link (pins 18/19)

    Serial.println(F("[GNC] Online. Waiting for messages on Serial1 (pins 18/19)..."));
}

void appGNC_loop() {
    // 1. Accumulate chars from RA Mega (Serial1), terminator is '!'
    while (Serial1.available()) {
        char c = Serial1.read();
        if (c == '!') {
            buf[bufIdx] = '\0';
            bufIdx   = 0;
            msgReady = true;
        } else if (c == '\n' || c == '\r') {
            // ignore stray line-ending bytes, not part of the payload
        } else if (bufIdx < sizeof(buf) - 1) {
            buf[bufIdx++] = c;
        } else {
            // overflow: drop malformed message, reset for next one
            bufIdx = 0;
        }
    }

    // 2. Handle completed message
    if (msgReady) {
        msgReady = false;
        Serial.print(F("[GNC] Received: "));
        Serial.println(buf);
        handleMessage(buf);
    }

    // 3. Autonomous operation — runs regardless of messages
    doWork();
}

static void handleMessage(const char* msg) {
    if (strncmp(msg, "GNC;", 4) != 0) {
        Serial.println(F("[GNC] Ignored (not my prefix)"));
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
    // currentDir drives whatever actuators this board owns
    (void)lastMoveTime;
}
