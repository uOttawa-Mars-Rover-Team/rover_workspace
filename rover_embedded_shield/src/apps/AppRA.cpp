#include "AppRA.h"
#include <Arduino.h>
#include <string.h>

// ============================================================
// AppRA — piggyback comms only (joints ignored for now)
// ------------------------------------------------------------
// Wiring:
//   Mega TX3 (pin 14)  →  GNC RX1 (pin 19)
//   Mega RX3 (pin 15)  ←  GNC TX1 (pin 18)
//   Common GND
//
// Serial  (USB) : user / ROS terminal  @ 115200
// Serial3       : inter-board link     @ 115200
//
// Message format (terminator is '!'):
//   "RA;message!"   -> handled locally
//   "GNC;message!"  -> forwarded to GNC board over Serial3
// ============================================================

static char    usbBuf[64];
static uint8_t usbIdx = 0;
static bool    usbReady = false;

static char    boardBuf[64];
static uint8_t boardIdx = 0;
static bool    boardReady = false;

static void handleUSBMessage(const char* msg);

void appRA_setup() {
    Serial.begin(115200);    // USB -> user / ROS
    Serial3.begin(115200);   // UART -> GNC board

    Serial.println(F("[RA] Online. Send RA;<msg>! or GNC;<msg>!"));
    Serial.println(F("[RA] Joints ignored -- comms test build"));
}

void appRA_loop() {
    // 1. Accumulate chars from USB (user / ROS)
    while (Serial.available()) {
        char c = Serial.read();
        if (c == '!') {
            usbBuf[usbIdx] = '\0';
            usbIdx   = 0;
            usbReady = true;
        } else if (c == '\n' || c == '\r') {
            // ignore stray line-ending bytes, not part of the payload
        } else if (usbIdx < sizeof(usbBuf) - 1) {
            usbBuf[usbIdx++] = c;
        } else {
            // overflow: drop malformed message, reset for next one
            usbIdx = 0;
        }
    }

    // 2. Handle completed USB message
    if (usbReady) {
        usbReady = false;
        handleUSBMessage(usbBuf);
    }

    // 3. Accumulate chars from GNC board (Serial3)
    while (Serial3.available()) {
        char c = Serial3.read();
        if (c == '!') {
            boardBuf[boardIdx] = '\0';
            boardIdx   = 0;
            boardReady = true;
        } else if (c == '\n' || c == '\r') {
            // ignore stray line-ending bytes, not part of the payload
        } else if (boardIdx < sizeof(boardBuf) - 1) {
            boardBuf[boardIdx++] = c;
        } else {
            boardIdx = 0;
        }
    }

    // 4. Propagate GNC reply to user terminal
    if (boardReady) {
        boardReady = false;
        Serial.print(F("[GNC->RA] "));
        Serial.println(boardBuf);
    }
}

// ----------------------------------------------------------
// Route a fully-received USB message
// ----------------------------------------------------------
static void handleUSBMessage(const char* msg) {
    // Expect "PREFIX;payload"
    const char* sep = strchr(msg, ';');
    if (sep == NULL) {
        Serial.println(F("[RA] Malformed message (no ';')"));
        return;
    }

    uint8_t prefixLen = sep - msg;

    // ---- RA -> this board handles it (joints ignored for now) ----
    if (prefixLen == 2 && strncmp(msg, "RA", 2) == 0) {
        const char* payload = sep + 1;
        Serial.print(F("[RA] Handling locally: "));
        Serial.println(payload);
        // TODO: joints ignored in this build
    }
    // ---- GNC -> forward to GNC board over Serial3 ----
    else if (prefixLen == 3 && strncmp(msg, "GNC", 3) == 0) {
        Serial.print(F("[RA] Forwarding to GNC: "));
        Serial.println(msg);          // echo so user knows it was routed
        Serial3.print(msg);
        Serial3.print('!');
    }
    else {
        Serial.print(F("[RA] Unknown prefix: "));
        Serial.println(msg);
    }
}
