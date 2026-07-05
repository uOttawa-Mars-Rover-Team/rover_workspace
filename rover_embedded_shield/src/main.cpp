#include "TaskJointControl.h"
#include "AppMorseServo.h"
#include <TimerThree.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>

// --- Joint order, matching integrative_control.py's curr_cmd field order ---
// index 0: TW  (tower / turret)
// index 1: L1  (linear actuator 1)
// index 2: L2  (linear actuator 2)
// index 3: WP  (wrist pitch)
// index 4: WR  (wrist roll)
// index 5: EE  (end effector)

// ═══════════════════════════════════════════════════════════════════════════════
// GLOBALS
// ═══════════════════════════════════════════════════════════════════════════════

TaskJointControl robotArm(6);

DriverStepper tw("Tower", 55, 54, 16, 17,  5000, 1000000, 1000.0);
DriverStepper wp("Pitch", 4,  5,  3,  2, 10000, 1000000, 1000.0);
DriverStepper wr("Roll",  8,  9,  7,  6, 20000, 1000000, 1000.0);
DriverStepper ee("EE",   12, 13, 11, 10, 20000, 1000000, 1000.0);

DriverLA LA1(12);   // L1
DriverLA LA2(11);   // L2

AppMorseServo morseApp;

enum AppState { APP_ARM, APP_MORSE };
static AppState appState = APP_ARM;

// ═══════════════════════════════════════════════════════════════════════════════
// ISR
// ═══════════════════════════════════════════════════════════════════════════════

void timerIsr() {
    sei();
    robotArm.updateSteppers();
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERIAL BUFFERING
// ═══════════════════════════════════════════════════════════════════════════════

static char    serialBuf[64];
static uint8_t serialIdx = 0;

static bool isNumericStart(char c) {
    return isdigit((unsigned char)c) || c == '-' || c == '+' || c == '.';
}

// ═══════════════════════════════════════════════════════════════════════════════
// AXIS COMMAND DISPATCH
// ═══════════════════════════════════════════════════════════════════════════════

void dispatchAxisCommand(char* msg) {
    float values[6] = {0, 0, 0, 0, 0, 0};
    uint8_t index = 0;

    char* token = strtok(msg, ";");

    // Skip leading non-numeric token (e.g. "S")
    if (token != NULL && !isNumericStart(token[0])) {
        token = strtok(NULL, ";");
    }

    while (token != NULL && index < 6) {
        if (!isNumericStart(token[0])) break;   // stop at trailing "!" or junk
        values[index] = atof(token);
        token = strtok(NULL, ";");
        index++;
    }

    if (index < 6) {
        Serial.print("WARNING: expected 6 axis values, got ");
        Serial.println(index);
        return;
    }

    float v_tw = values[0];
    float v_l1 = values[1];
    float v_l2 = values[2];
    float v_wp = values[3];
    float v_wr = values[4];
    float v_ee = values[5];

    tw.moveMotor(v_tw * tw.speed);
    wp.moveMotor(v_wp * wp.speed);
    wr.moveMotor(v_wr * wr.speed);
    ee.moveMotor(v_ee * ee.speed);

    int8_t l1dir = (v_l1 >  0.05f) ? 1 : (v_l1 < -0.05f) ? -1 : 0;
    LA1.moveMotor(400, l1dir);
    int8_t l2dir = (v_l2 >  0.05f) ? 1 : (v_l2 < -0.05f) ? -1 : 0;
    LA2.moveMotor(400, l2dir);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MESSAGE ROUTER
// ═══════════════════════════════════════════════════════════════════════════════

void handleMessage(char* msg) {

    // ── Global mode switches — always checked first ──────────────────────────
    if (strcmp(msg, "MORSE") == 0) {
        appState = APP_MORSE;
        morseApp.init();
        Serial.println(F("[SYS] Entering MORSE mode — arm holding position"));
        Serial.println(F("[SYS] Type EXIT to return to arm mode"));
        return;
    }
    if (strcmp(msg, "EXIT") == 0) {
        appState = APP_ARM;
        Serial.println(F("[SYS] Returning to ARM mode"));
        Serial.println(F("[SYS] Awaiting: S;tw;l1;l2;wp;wr;ee;!"));
        return;
    }

    // ── MORSE mode — route to morse app, arm ignored ─────────────────────────
    if (appState == APP_MORSE) {
        morseApp.handleMessage(msg);
        return;
    }

    // ── ARM mode — dispatch axis command ─────────────────────────────────────
    dispatchAxisCommand(msg);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERIAL POLL — per-character accumulation, '!' or '\n' as terminator
// ═══════════════════════════════════════════════════════════════════════════════

void pollSerialCommand() {
    while (Serial.available() > 0) {
        char c = Serial.read();

        if (c == '!' || c == '\n' || c == '\r') {
            if (serialIdx > 0) {
                serialBuf[serialIdx] = '\0';
                serialIdx = 0;
                handleMessage(serialBuf);
            }
        } else if (serialIdx < sizeof(serialBuf) - 1) {
            serialBuf[serialIdx++] = c;
        } else {
            serialIdx = 0;
            Serial.println(F("Command too long, discarded"));
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SETUP
// ═══════════════════════════════════════════════════════════════════════════════

void setup() {
    Serial.begin(115200);

    robotArm.addStepper(&tw);
    robotArm.addStepper(&wp);
    robotArm.addStepper(&wr);
    robotArm.addStepper(&ee);

    DriverLA_InitI2C();
    robotArm.addLA(&LA1);
    robotArm.addLA(&LA2);

    robotArm.init();

    Timer3.initialize(100);
    Timer3.attachInterrupt(timerIsr);

    Serial.println(F("[SYS] Robot Arm Initialized"));
    Serial.println(F("[SYS] Awaiting: S;tw;l1;l2;wp;wr;ee;!"));
    Serial.println(F("[SYS] Type MORSE to enter morse mode, EXIT to return"));
}

// ═══════════════════════════════════════════════════════════════════════════════
// LOOP
// ═══════════════════════════════════════════════════════════════════════════════

void loop() {
    pollSerialCommand();

    if (appState == APP_MORSE) {
        morseApp.update();
    }
}
