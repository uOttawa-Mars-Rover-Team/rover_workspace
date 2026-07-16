#include "AppRA.h"
#include "TaskJointControl.h"
#include "AppMorseServo.h"
#include "CommSerial.h"
#include <TimerThree.h>
#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include "DriverEncoder.h"
#include "TaskButton.h"

// one per joint, pass the CS pin

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

static TaskJointControl robotArm(6);

static DriverStepper tw("Tower", 55, 54, 16, 17,  5000, 1000000, 1000.0);
static DriverStepper wp("Pitch", 4,  5,  3,  2, 10000, 1000000, 2000.0);
static DriverStepper wr("Roll",  8,  9,  7,  22, 20000, 1000000, 1000.0);
static DriverStepper ee("EE",   12, 13, 11, 10, 20000, 1000000, 1000.0);

static DriverLA LA1(12);   // L1
static DriverLA LA2(11);   // L2

static AppMorseServo morseApp;
static TaskButton svBtn;  
DriverEncoder encTW(66, RES12);

enum AppState { APP_ARM, APP_MORSE };
static AppState appState = APP_ARM;

CommSerial comms(Serial3, 9600, "RA;", appRA_handleRA);

// ═══════════════════════════════════════════════════════════════════════════════
// ISR
// ═══════════════════════════════════════════════════════════════════════════════

static void timerIsr() {
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
// MESSAGE ROUTER
// ═══════════════════════════════════════════════════════════════════════════════
void appRA_handleRA(char* payload) {

    if (strcmp(payload, "MORSE") == 0) {
        svBtn.disable();   // block svT/svH/svR while morse runs
        appState = APP_MORSE;
        morseApp.init(); // morse has its own Servo on same pin — btn won't touch it
        return;
    }
    if (strcmp(payload, "EXIT") == 0) {
        appState = APP_ARM;
        svBtn.enable();    // restore button control
        svBtn.begin(6, 160, 20, 15, 10);  // reattach after morse releases pin
        return;
    }

    // ── MORSE mode — pass to morse app ───────────────────────────────────────
    if (appState == APP_MORSE) {
        morseApp.handleMessage(payload);
        return;
    }

    // ── ARM control commands ─────────────────────────────────────────────────
    if (strcmp(payload, "ESTOP") == 0) {
        robotArm.stopAll();
        Serial.println(F("[RAF] ESTOP"));
        return;
    }
    if (strcmp(payload, "ENABLE") == 0) {
        tw.enable(); wp.enable(); wr.enable(); ee.enable();
        Serial.println(F("[RAF] All steppers enabled"));
        return;
    }
    if (strcmp(payload, "DISABLE") == 0) {
        tw.disable(); wp.disable(); wr.disable(); ee.disable();
        Serial.println(F("[RAF] All steppers disabled"));
        return;
    }
    if (strcmp(payload, "STATUS") == 0) {
        Serial.print(F("[RAF] TW=")); Serial.println(tw.driver.currentPosition());
        Serial.print(F("[RAF] WP=")); Serial.println(wp.driver.currentPosition());
        Serial.print(F("[RAF] WR=")); Serial.println(wr.driver.currentPosition());
        Serial.print(F("[RAF] EE=")); Serial.println(ee.driver.currentPosition());
        return;
    }

    if (strcmp(payload, "svT") == 0) { svBtn.tap();          return; }
    if (strcmp(payload, "svH") == 0) { svBtn.holdDown();     return; }
    if (strcmp(payload, "svR") == 0) { svBtn.releaseUp();    return; }

    // ── Axis command via RA;S; ───────────────────────────────────────────────
    if (payload[0] == 'S' && payload[1] == ';') {
        appRA_dispatchAxisCommand(payload);
        return;
    }

    Serial.print(F("[RAF] Unknown: "));
    Serial.println(payload);
}

void appRA_dispatchAxisCommand(char* msg) {
    float values[6] = {0, 0, 0, 0, 0, 0};
    uint8_t index = 0;

    char* token = strtok(msg, ";");
    if (token != NULL && !isNumericStart(token[0])) {
        token = strtok(NULL, ";");
    }
    while (token != NULL && index < 6) {
        if (!isNumericStart(token[0])) break;
        values[index++] = atof(token);
        token = strtok(NULL, ";");
    }
    if (index < 6) {
        Serial.print(F("[RAF] WARNING: expected 6 values, got "));
        Serial.println(index);
        return;
    }

    tw.moveMotor(values[0] * tw.speed);
    wp.moveMotor(values[3] * wp.speed);
    wr.moveMotor(values[4] * wr.speed);
    ee.moveMotor(values[5] * ee.speed);

    int8_t l1dir = (values[1] >  0.05f) ? 1 : (values[1] < -0.05f) ? -1 : 0;
    int8_t l2dir = (values[2] >  0.05f) ? 1 : (values[2] < -0.05f) ? -1 : 0;
    
    uint16_t l1speed = (uint16_t)(fabs(values[1]) * 600.0f);
    uint16_t l2speed = (uint16_t)(fabs(values[2]) * 600.0f);
    LA1.moveMotor(l1speed, l1dir);
    LA2.moveMotor(l2speed, l2dir);
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERIAL POLL — per-character accumulation, '!' or '\n' as terminator
// ═══════════════════════════════════════════════════════════════════════════════
static void reportEncoders() {
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint < 1000) return;
    lastPrint = millis();

    uint16_t posTW = encTW.getPosition();

    if (encTW.isOk()) { 
      Serial.print(F("[RAF] TW=")); 
      Serial.println((posTW / 4096.0f) * 360.0f);
    }
    else               { 
      Serial.println(F("[RAF] TW=ERROR")); 
    }
}


static void pollSerialCommand() {
    while (Serial.available() > 0) {
        char c = Serial.read();
        if (c == '!' || c == '\n' || c == '\r') {
            if (serialIdx > 0) {
                serialBuf[serialIdx] = '\0';
                serialIdx = 0;
                comms.handleMessage(serialBuf);  // ← goes through CommSerial now
            }
        } else if (serialIdx < sizeof(serialBuf) - 1) {
            serialBuf[serialIdx++] = c;
        } else {
            serialIdx = 0;
            Serial.println(F("[SYS] Command too long, discarded"));
        }
    }
}
// ═══════════════════════════════════════════════════════════════════════════════
// PUBLIC ENTRY POINTS
// ═══════════════════════════════════════════════════════════════════════════════

void appRA_setup() {
    Serial.begin(9600);
    comms.init();          // starts Serial3 only

    svBtn.begin(6, 160, 20, 15, 10);
    
    robotArm.addStepper(&tw);
    robotArm.addStepper(&wp);
    robotArm.addStepper(&wr);
    robotArm.addStepper(&ee);

    DriverLA_InitI2C();
    robotArm.addLA(&LA1);
    robotArm.addLA(&LA2);

    robotArm.init();
    encTW.init();
    Timer3.initialize(400);
    Timer3.attachInterrupt(timerIsr);

    Serial.println(F("[SYS] Robot Arm Initialized"));
    Serial.println(F("[SYS] Awaiting: S;tw;l1;l2;wp;wr;ee;!"));
    Serial.println(F("[SYS] Type MORSE to enter morse mode, EXIT to return"));
}

void appRA_loop() {
    pollSerialCommand();
    reportEncoders();
    svBtn.update();


    if (appState == APP_MORSE) {
        morseApp.update();
    }
}

